import asyncio
import time

from datetime import datetime
from astropy.io.fits import HDUList
from io import BytesIO
from importlib import reload

from pyindigo import camera
from pyindigo.callback_utils import prints_errors, accepts_hdu_list

import fitsutils

from camera_config import get_camera_config


def timed_log(s):
    print(datetime.now().strftime(r'%X %f') + ': ' + s)


class CameraAdapter:
    """Adapter for pyindigo camera, handling high-level asyncronous operation, configuration, etc

    In future it should encapsulate any other image processing tasks:
        - accumulation for timelapse videos (though it can be done from previews)
        - cloud detection
    """

    def __init__(self):
        self.terminal_failure = False
        self.camera_lock = asyncio.Lock()

        self.preview: bytes = None
        self.preview_metadata: dict = None
        self.new_preview_ready = asyncio.Event()

        # taking one preview shot in adavance to avoid cold start
        config_entry = get_camera_config()['preview']
        shot_ready = False

        def flag_setting(callback):
            def decorated(*args):
                callback(*args)
                nonlocal shot_ready
                shot_ready = True
            return decorated

        camera.take_shot(
            config_entry['exposure'],
            config_entry['gain'],
            color_mode=config_entry.get('color_mode', 'rgb').upper(),
            callback=flag_setting(self._preview_generation_callback)
        )

        while not shot_ready:  # blocking await
            time.sleep(0.1)

    def connected(self):
        return camera.connected()

    def reconnect(self):
        """Experimental method for when we want to reconnect to camera by restarting whole INDIGO interface"""
        if camera.connected() or self.terminal_failure:
            return
        else:
            print('Reloading INDIGO interface...')
            camera.unload_pyindigo()
            time.sleep(1)
            reload(camera)
            if not camera.connected():
                self.terminal_failure = True

    async def operate(self):
        """All operations by camera, ready to be run concurrently.

        This is the only coroutine that should be launched from outside!"""
        return await asyncio.gather(
            self._regularly_take_shots('preview', self._preview_generation_callback),
            self._regularly_take_shots('testing', self._testing_callback)
        )

    def _regularly_take_shots(self, config_id, callback):
        """Coroutine factory, return coroutine that regularly takes shots with given
        period, gain, exposure and callback. Conflicts are resolved with lock"""

        async def unlock_camera():
            timed_log(f'{config_id} releasing lock')
            self.camera_lock.release()

        def camera_freeing(callback, loop):
            def decorated_callback(*args):
                callback(*args)
                try:
                    asyncio.run_coroutine_threadsafe(unlock_camera(), loop)
                except Exception as e:
                    print(e)
            return decorated_callback

        async def coro():
            """The actual coroutine that can be put into an event loop"""
            while True:
                config_entry = get_camera_config()[config_id]
                if config_entry['enabled'] is True:
                    start = time.time()
                    loop = asyncio.get_running_loop()
                    timed_log(f'{config_id} awaiting lock')
                    await self.camera_lock.acquire()
                    timed_log(f'{config_id} got lock')
                    camera.take_shot(
                        config_entry['exposure'],
                        config_entry['gain'],
                        color_mode=config_entry.get('color_mode', 'rgb').upper(),
                        callback=camera_freeing(callback, loop)
                    )
                    duration = time.time() - start
                else:
                    duration = 0
                await asyncio.sleep(max(config_entry['period'] - duration, 0))

        return coro()

    @prints_errors
    @accepts_hdu_list
    def _preview_generation_callback(self, hdul: HDUList):
        timed_log('preview callback fired')
        inmem_file = BytesIO()
        fitsutils.save_fits_as_jpeg(hdul, inmem_file)
        inmem_file.seek(0)
        self.preview = inmem_file.getvalue()
        self.preview_metadata = fitsutils.extract_metadata(hdul)
        self.new_preview_ready.set()

    async def preview_feed_generator(self):
        """Async generator yielding new preview shots as they arise, for outside use"""
        while True:
            await self.new_preview_ready.wait()
            self.new_preview_ready.clear()
            yield self.preview, self.preview_metadata

    def _testing_callback(self, *args):
        timed_log('testing callback fired')

    @staticmethod
    def _generate_image_name(prefix: str, format_: str) -> str:
        """Helper function to generate unique filenames like 'some_prefix_2020_10_15_19_21_39.image_format'"""
        return f'{prefix}_{datetime.now().strftime(r"%Y_%m_%d_%H_%M_%S")}.{format_}'


if __name__ == "__main__":
    camera_adapter = CameraAdapter()
    loop = asyncio.get_event_loop()
    loop.create_task(camera_adapter.operate())
    loop.run_forever()
