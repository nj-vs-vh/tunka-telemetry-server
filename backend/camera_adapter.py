import asyncio
import time

from datetime import datetime
from astropy.io.fits import HDUList
import base64
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
        self.latest_preview_base64 = None
        self.latest_preview_metadata = None

        # TODO: read these from config file and make dependent on time
        self.shooting_period = 2
        self.gain = 30
        self.exposure = 0.02

        # take at least one shot on initialization to begin with
        camera.take_shot(self.exposure, self.gain, self.preview_generating_callback)

    def reconnect(self):
        """Experimental method for when we want to reconnect to camera by restarting whole INDIGO interface"""
        if camera.connected():
            return
        else:
            print('Reloading INDIGO interface...')
            camera.unload_pyindigo()
            time.sleep(1)
            reload(camera)

    @prints_errors
    @accepts_hdu_list
    def preview_generating_callback(self, hdul: HDUList):
        inmem_file = BytesIO()
        fitsutils.save_fits_as_jpeg(hdul, inmem_file)
        inmem_file.seek(0)
        self.latest_preview_base64 = base64.b64encode(inmem_file.getvalue())
        self.latest_preview_metadata = fitsutils.extract_metadata(hdul)
        print('inmemory file created and encoded to base64')

    async def generate_previews_regularly(self):
        """Main coroutine to take shots with camera each several seconds"""
        while True:
            exposure_start = time.time()
            camera.take_shot(self.exposure, self.gain, self.preview_generating_callback)
            exposure_duration = time.time() - exposure_start
            await asyncio.sleep(self.shooting_period - exposure_duration)

    async def operation(self):
        """All operations by camera to expose to outside user.

        All coroutines (i.e. previews, processing) should be gathered here to launch concurrently"""
        return await asyncio.gather(
            self.generate_previews_regularly(),
        )

    @staticmethod
    def generate_image_name(prefix: str, format_: str) -> str:
        """Helper function to generate unique filenames like 'some_prefix_2020_10_15_19_21_39.image_format'"""
        return f'{prefix}_{datetime.now().strftime(r"%Y_%m_%d_%H_%M_%S")}.{format_}'


if __name__ == "__main__":
    camera_adapter = CameraAdapter()
    asyncio.run(camera_adapter.operation())
