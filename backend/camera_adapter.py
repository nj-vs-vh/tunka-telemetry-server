from pathlib import Path
import asyncio
import time
from collections import defaultdict

from typing import Callable, Any, Dict

import logging

from datetime import datetime
from astropy.io.fits import HDUList
from io import BytesIO

import fitsutils
from camera_config import camera_config, ShotType
from observation_conditions import observation_conditions, localtime_str

from pyindigo.models.driver import IndigoDriver
import pyindigo.models.client as IndigoClient

from pyindigo.core.properties import (
    IndigoProperty,
    BlobVectorProperty,
    CCDSpecificProperties,
)
from pyindigo.core.properties.schemas import UserDefinedItem
from pyindigo.core.enums import IndigoDriverAction, IndigoPropertyState


driver = IndigoDriver("indigo_ccd_simulator")

DEBUG_LOCK = False

FITS_DIR = Path(__file__).parent.parent / "images"
FITS_DIR.mkdir(exist_ok=True)


class CameraAdapter:
    """Adapter for pyindigo camera, handling high-level asyncronous operation, configuration, etc

    In future it should encapsulate any other image processing tasks:
        - accumulation for timelapse videos (though it can be done from previews)
        - cloud detection
    """

    def __init__(self, mode: str, loop: asyncio.AbstractEventLoop):

        # set in .env file
        if mode == "Simulator":
            driver_name = "indigo_ccd_simulator"
            device_name = "CCD Imager Simulator"
        elif mode == "Real":
            driver_name = "indigo_ccd_asi"
            device_name = "ZWO ASI120MC-S #0"
        else:
            raise ValueError(f"mode must be 'Real' or 'Simulator' (preferably set in .env file), but {mode} received")

        self.driver = IndigoDriver(driver_name)
        self.driver.attach()
        time.sleep(1)
        self.device = IndigoClient.find_device(device_name)
        self.device.connect(blocking=True)

        self.loop = loop

        self.terminal_failure = False
        self.camera_lock = asyncio.Lock()
        self.operation_pending = defaultdict(lambda: False)

        self.preview: bytes = None
        self.preview_metadata: dict = None
        self.new_preview_ready = asyncio.Event()

    async def operate(self):
        """All operations by camera, ready to be run concurrently.

        This is the only coroutine that should be launched from outside!"""
        return await asyncio.gather(
            self._regularly_take_shots(ShotType.PREVIEW, self._preview_generation_callback),
            self._regularly_take_shots(
                ShotType.SAVE_TO_DISK, self._fits_saving_callback, enabled=self.save_to_disk_enabled
            ),
            # testing is usually turned off on server (enabled: False in config)
            self._regularly_take_shots(ShotType.TESTING, lambda *args: logging.debug("testing callback run")),
        )

    def _regularly_take_shots(
        self,
        shot_type: ShotType,
        callback: Callable[[Any], None],
        enabled: Callable[[Dict], bool] = None,
    ):
        """Coroutine factory, return coroutine that regularly takes shots with given
        shot_type (see camconfig.yaml) and callback. Conflicts are resolved with lock"""

        if enabled is None:

            def enabled(config_entry) -> bool:
                return config_entry and config_entry["enabled"] is True

        shot_pending = False

        async def coro():
            """The actual coroutine that can be put into an event loop"""
            nonlocal shot_pending

            while True:
                config_entry = camera_config.get(shot_type, None)
                if enabled(config_entry) and not shot_pending:
                    shot_pending = True
                    shot_start_time = time.time()
                    await self.take_shot(
                        config_entry["exposure"],
                        config_entry["gain"],
                        color_mode=config_entry.get("color_mode", "rgb").upper(),
                        callback=callback,
                    )
                    shot_pending = False
                    shot_duration = time.time() - shot_start_time
                else:
                    shot_duration = 0

                SLEEP_BETWEEN_PENDING_PROBES = 3  # sec
                await asyncio.sleep(max(config_entry["period"] - shot_duration, SLEEP_BETWEEN_PENDING_PROBES))

        return coro()

    async def take_shot(self, exposure: float, gain: float, color_mode: str, callback: Callable):
        exposure_result = {"prop": None}
        exposure_done = asyncio.Event()
        exposure_done.clear()

        async def get_exposure_results(action: IndigoDriverAction, prop: IndigoProperty):
            if DEBUG_LOCK:
                logging.debug("exposure done")
            exposure_result["prop"] = prop
            exposure_done.set()

        if DEBUG_LOCK:
            import random

            pseudouid = random.randint(1, 100)
            logging.debug(f"waiting for camera lock (pseudo id={pseudouid})")
        async with self.camera_lock:
            self.device.callback(
                get_exposure_results,
                accepts={
                    "action": IndigoDriverAction.UPDATE,
                    "name": CCDSpecificProperties.CCD_IMAGE.property_name,
                    "state": IndigoPropertyState.OK,
                },
                run_times=1,
                loop=self.loop,
            )

            self.device.set_property(  # specific values are hardcoded for ZWO camera
                CCDSpecificProperties.CCD_MODE,
                UserDefinedItem(
                    item_name="RAW 8 1x1" if color_mode == "greyscale" else "RGB 24 1x1",
                    item_value=True,
                )
            )
            self.device.set_property(CCDSpecificProperties.CCD_GAIN, GAIN=gain)
            time.sleep(0.1)  # safety sleep
            self.device.set_property(CCDSpecificProperties.CCD_EXPOSURE, EXPOSURE=exposure)
            await exposure_done.wait()
            image_prop: BlobVectorProperty = exposure_result["prop"]
            callback(fitsutils.fits_bytes_to_hdu_list(image_prop.items[0].value))
            if DEBUG_LOCK:
                logging.debug(f"releasing camera lock (pseudo id={pseudouid})")

    def _preview_generation_callback(self, hdul: HDUList):
        logging.debug("generating preview image...")
        inmem_file = BytesIO()
        fitsutils.save_fits_as_jpeg(hdul, inmem_file)
        inmem_file.seek(0)
        self.preview = inmem_file.getvalue()
        self.preview_metadata = fitsutils.extract_metadata(hdul)
        self.preview_metadata.update(
            {
                "shot_datetime": localtime_str(datetime.utcnow()),
                "period": camera_config[ShotType.PREVIEW]["period"],
            }
        )
        self.new_preview_ready.set()

    async def preview_feed_generator(self):
        """Async generator yielding new preview shots as they arise, for outside use"""
        while True:
            await self.new_preview_ready.wait()
            self.new_preview_ready.clear()
            yield self.preview, self.preview_metadata

    def _fits_saving_callback(self, hdul: HDUList):
        file_path = str(FITS_DIR / self._generate_image_name("image", "fits"))
        logging.debug(f"saving FITS image to {file_path}...")
        hdul.writeto(file_path)

    @staticmethod
    def save_to_disk_enabled(config_entry):
        if not config_entry or config_entry["enabled"] is False:
            return False
        if config_entry.get("override", False):
            return True
        conditions = observation_conditions()
        return conditions["is_astronomical_night"] and conditions["is_moonless"]

    @staticmethod
    def _generate_image_name(prefix: str, format_: str) -> str:
        """Helper function to generate unique filenames like 'some_prefix_2020_10_15_19_21_39.image_format'"""
        return f'{prefix}_{datetime.utcnow().strftime(r"%Y_%m_%d_%H_%M_%S")}.{format_}'


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    camera_adapter = CameraAdapter(mode="Simulator", loop=loop)
    loop.create_task(camera_adapter.operate())
    loop.run_forever()
