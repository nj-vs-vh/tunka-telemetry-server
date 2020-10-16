import asyncio
import time

from datetime import datetime
from astropy.io.fits import HDUList
from io import BytesIO
from importlib import reload

from pyindigo import camera
from pyindigo.callback_utils import prints_errors, accepts_hdu_list

import fitsutils

from camera_config import config as camera_config


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
        self.new_preview = asyncio.Event()

        # take at least one shot on initialization to begin with
        camera_init_loop = asyncio.get_event_loop()
        camera_init_loop.create_task(self.operate())
        camera_init_loop.run_until_complete(self.new_preview.wait())
        # camera_init_loop.close()

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
        """All operations by camera ready to be run concurrently.

        This is the only coroutine that should be launched from outside!"""
        return await asyncio.gather(
            self._regularly_take_shots(camera_config['preview'], self._preview_generation_callback),
            self._regularly_take_shots(camera_config['testing'], self._testing_callback)
        )

    def _regularly_take_shots(self, config_entry, callback):
        """Coroutine factory, return coroutine that regularly takes shots with given
        period, gain, exposure and callback. Conflicts are resolved with lock"""

        if config_entry['enabled'] is False:
            fut = asyncio.Future()
            fut.cancel()
            return fut

        async def coro():
            """The actual coroutine that can be put into an event loop"""
            while True:
                start = time.time()
                camera.take_shot(config_entry['exposure'], config_entry['gain'], callback)
                duration = time.time() - start
                await asyncio.sleep(max(config_entry['period'] - duration, 0))

        return coro()

    @prints_errors
    @accepts_hdu_list
    def _preview_generation_callback(self, hdul: HDUList):
        inmem_file = BytesIO()
        fitsutils.save_fits_as_jpeg(hdul, inmem_file)
        inmem_file.seek(0)
        self.preview = inmem_file.getvalue()
        self.preview_metadata = fitsutils.extract_metadata(hdul)
        self.new_preview.set()
        print('hello from preview!')

    async def preview_feed_generator(self):
        """Async generator yielding new preview shots as they arise, for outside use"""
        while True:
            await self.new_preview.wait()
            self.new_preview.clear()
            yield self.preview, self.preview_metadata

    def _testing_callback(self, *args):
        print('hello from testing!')

    @staticmethod
    def _generate_image_name(prefix: str, format_: str) -> str:
        """Helper function to generate unique filenames like 'some_prefix_2020_10_15_19_21_39.image_format'"""
        return f'{prefix}_{datetime.now().strftime(r"%Y_%m_%d_%H_%M_%S")}.{format_}'


if __name__ == "__main__":
    camera_adapter = CameraAdapter()
    loop = asyncio.get_event_loop()
    loop.create_task(camera_adapter.operate())
    loop.run_forever()
