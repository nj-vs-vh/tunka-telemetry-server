from pathlib import Path
import asyncio
import time
from collections import defaultdict

import logging

from datetime import datetime
from astropy.io.fits import HDUList
from io import BytesIO
from importlib import reload

from pyindigo.callback_utils import handles_errors, accepts_hdu_list

import fitsutils

from camera_config import get_camera_config


DEBUG_LOCK = False

FITS_DIR = Path(__file__).parent.parent / 'images'
FITS_DIR.mkdir(exist_ok=True)


class CameraAdapter:
    """Adapter for pyindigo camera, handling high-level asyncronous operation, configuration, etc

    In future it should encapsulate any other image processing tasks:
        - accumulation for timelapse videos (though it can be done from previews)
        - cloud detection
    """

    def __init__(self):
        from pyindigo import camera  # actual pyindigo initialization
        self.camera = camera

        self.terminal_failure = False
        self.camera_lock = asyncio.Lock()
        self.operation_pending = defaultdict(lambda: False)

        self.preview: bytes = None
        self.preview_metadata: dict = None
        self.new_preview_ready = asyncio.Event()

    def connected(self):
        return self.camera.connected()

    def reconnect(self):
        """Experimental method for when we want to reconnect to camera by restarting whole INDIGO interface"""
        if self.camera.connected() or self.terminal_failure:
            return
        else:
            logging.info('Reloading INDIGO interface on some error...')
            self.camera.unload_pyindigo()
            time.sleep(1)
            reload(self.camera)
            if not self.camera.connected():
                logging.info("Reloading unsuccessful, camera is in terminal failure state")
                self.terminal_failure = True
            logging.info("Reloading successful, camera operating")

    async def operate(self):
        """All operations by camera, ready to be run concurrently.

        This is the only coroutine that should be launched from outside!"""
        return await asyncio.gather(
            self._regularly_take_shots('preview', self._preview_generation_callback),
            self._regularly_take_shots('savetodisk', self._fits_saving_callback),
            # testing is usually turned off on server (enabled: False in config)
            self._regularly_take_shots('testing', lambda *args: logging.debug('testing callback run'))
        )

    def _regularly_take_shots(self, config_id, callback):
        """Coroutine factory, return coroutine that regularly takes shots with given
        config_id (see camconfig.yaml) and callback. Conflicts are resolved with lock"""

        async def unlock_camera():
            if DEBUG_LOCK:
                logging.debug(f'{config_id} releasing lock')
            self.camera_lock.release()
            self.operation_pending[config_id] = False

        def camera_freeing(callback, loop):
            def decorated_callback(*args):
                callback(*args)
                try:
                    asyncio.run_coroutine_threadsafe(unlock_camera(), loop)
                except Exception as e:
                    logging.error(f'Error unlocking camera: {e}')
            return decorated_callback

        async def coro():
            """The actual coroutine that can be put into an event loop"""
            while True:
                config_entry = get_camera_config().get(config_id, None)
                if config_entry and config_entry['enabled'] is True and not self.operation_pending[config_id]:
                    start = time.time()
                    loop = asyncio.get_running_loop()
                    if DEBUG_LOCK:
                        logging.debug(f'{config_id} awaiting lock')
                    self.operation_pending[config_id] = True
                    await self.camera_lock.acquire()
                    if DEBUG_LOCK:
                        logging.debug(f'{config_id} got lock')
                    self.camera.take_shot(
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

    @handles_errors(lambda e: logging.error(f"Error in preview generation callback: {e}"))
    @accepts_hdu_list
    def _preview_generation_callback(self, hdul: HDUList):
        logging.debug('preview callback run')
        hdul.writeto(FITS_DIR / self._generate_image_name('preview', 'fits'))
        inmem_file = BytesIO()
        fitsutils.save_fits_as_jpeg(hdul, inmem_file)
        inmem_file.seek(0)
        self.preview = inmem_file.getvalue()
        self.preview_metadata = fitsutils.extract_metadata(hdul)
        self.preview_metadata.update({'Current datetime': datetime.now().strftime(r"%Y_%m_%d_%H_%M_%S")})
        self.new_preview_ready.set()

    @handles_errors(lambda e: logging.error(f"Error in FITS saving callback: {e}"))
    @accepts_hdu_list
    def _fits_saving_callback(self, hdul: HDUList):
        hdul.writeto(FITS_DIR / self._generate_image_name('preview', 'fits'))

    async def preview_feed_generator(self):
        """Async generator yielding new preview shots as they arise, for outside use"""
        while True:
            await self.new_preview_ready.wait()
            self.new_preview_ready.clear()
            yield self.preview, self.preview_metadata

    @staticmethod
    def _generate_image_name(prefix: str, format_: str) -> str:
        """Helper function to generate unique filenames like 'some_prefix_2020_10_15_19_21_39.image_format'"""
        return f'{prefix}_{datetime.now().strftime(r"%Y_%m_%d_%H_%M_%S")}.{format_}'


if __name__ == "__main__":
    camera_adapter = CameraAdapter()
    loop = asyncio.get_event_loop()
    loop.create_task(camera_adapter.operate())
    loop.run_forever()
