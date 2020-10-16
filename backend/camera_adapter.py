import asyncio
import time

from datetime import datetime
from astropy.io.fits import HDUList
from io import BytesIO
from importlib import reload

from pyindigo import camera
from pyindigo.callback_utils import prints_errors, accepts_hdu_list

import fitsutils


class CameraAdapter:
    """Adapter for pyindigo camera, handling high-level asyncronous operation, configuration, etc

    In future it should encapsulate any other image processing tasks:
        - accumulation for timelapse videos (though it can be done from previews)
        - cloud detection
    """

    def __init__(self):
        self.terminal_failure = False

        self.preview: bytes = None
        self.preview_metadata: dict = None
        self.new_preview = asyncio.Event()

        # TODO: read these from config file and make dependent on time
        self.shooting_period = 2
        self.gain = 30
        self.exposure = 0.02

        # take at least one shot on initialization to begin with
        camera.take_shot(self.exposure, self.gain, self._preview_generation_callback)
        camera.wait_for_exposure()

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

    async def operation(self):
        """All operations by camera ready to be run concurrently.

        This is the only coroutine that should be launched from outside!"""
        return await asyncio.gather(
            self._run_preview_live_stream(),
        )

    async def preview_feed_generator(self):
        """Async generator for outside use yielding new preview shots as they arise"""
        while True:
            await self.new_preview.wait()
            self.new_preview.clear()
            yield self.preview, self.preview_metadata

    # "private" methods

    @prints_errors
    @accepts_hdu_list
    def _preview_generation_callback(self, hdul: HDUList):
        inmem_file = BytesIO()
        fitsutils.save_fits_as_jpeg(hdul, inmem_file)
        inmem_file.seek(0)
        self.preview = inmem_file.getvalue()
        self.preview_metadata = fitsutils.extract_metadata(hdul)
        self.new_preview.set()

    async def _run_preview_live_stream(self):
        """Coroutine requesting new shot from camera with given period, converting it to jpeg and extracting metadata"""
        while True:
            exposure_start = time.time()
            camera.take_shot(self.exposure, self.gain, self._preview_generation_callback)
            exposure_duration = time.time() - exposure_start
            await asyncio.sleep(self.shooting_period - exposure_duration)

    @staticmethod
    def _generate_image_name(prefix: str, format_: str) -> str:
        """Helper function to generate unique filenames like 'some_prefix_2020_10_15_19_21_39.image_format'"""
        return f'{prefix}_{datetime.now().strftime(r"%Y_%m_%d_%H_%M_%S")}.{format_}'


if __name__ == "__main__":
    camera_adapter = CameraAdapter()
    asyncio.run(camera_adapter.operation())
