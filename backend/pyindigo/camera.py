"""Main pyindigo submodule that acts as a singleton object encapsulating available camera functionality

Example:

>>> from pyindigo import camera
>>> from pyindigo.callback_utils import prints_errors, accepts_hdu_list

>>> @prints_errors
>>> @accepts_hdu_list
>>> def save_fits_to_file(hdul):
>>>     hdul.writeto('image.fits')

>>> camera.take_shot(0.1, 100, save_fits_to_file)
>>> camera.wait_for_exposure()
"""

import os
import time
import atexit

import logging

from dotenv import load_dotenv
from pathlib import Path
from enum import Enum
from numbers import Number
from typing import Callable

import _pyindigo


env_path = (Path(__file__).parent / '../.indigoenv').resolve()
load_dotenv(env_path)

camera_mode = os.environ.get('CAMERA_MODE', None)


# device names are hard-coded until pyindigo upgrade
if camera_mode == 'Simulator':
    DRIVER = 'indigo_ccd_simulator'
    DEVICE = 'CCD Imager Simulator'
elif camera_mode == 'Real':
    DRIVER = 'indigo_ccd_asi'
    DEVICE = 'ZWO ASI120MC-S #0'
else:
    raise OSError(
        "CAMERA_MODE environment variable must be set to 'Real' or 'Simulator' (preferably in .indigoenv file)"
    )


class ColorMode(Enum):
    """Color mode as recognized by set_ccd_mode _pyindigo function"""
    GREYSCALE = 0
    RGB = 1


logging.info(f"Pyindigo is connecting to camera ({DRIVER} driver, device '{DEVICE}')")

_pyindigo.set_device_name(DEVICE)
_pyindigo.setup_ccd_client(DRIVER)
time.sleep(5)  # workaround to give camera time to connect before usage

logging.info("Pyindigo connected to camera")

if DRIVER != 'indigo_ccd_simulator':
    _pyindigo.set_usb_bandwidth(50.0)


def unload_pyindigo():
    """Direct wrapper of internal INDIGO unloading, but can be called from outside (see CameraAdapter reload method)"""
    logging.info("Unloading pyindigo")
    _pyindigo.cleanup_ccd_client()


atexit.register(unload_pyindigo)

_exposing = False


def take_shot(exposure: Number, gain: Number, color_mode: ColorMode = None, callback: Callable = lambda *args: None):
    """Request new shot from camera with given gain, exposure and callback for processing

    Note: use decorators from pyindigo.callback_utils to automatically add error catching, HDUList conversion and
    other handy features to your callback
    """
    global _exposing
    if not _pyindigo.check_if_device_is_connected():
        _exposing = False  # prevent mess if device is disconnected while exposing
        return
    if _exposing:
        logging.error(f'Attempt to take shot with {DEVICE} which is exposing at the time!')
        return
    if color_mode is None:
        color_mode = ColorMode.RGB
    elif isinstance(color_mode, str):
        try:
            color_mode = ColorMode[color_mode]
        except Exception:
            color_mode = ColorMode.RGB
    logging.debug(
        f"Pyindigo takes shot with gain {gain}, exposure {exposure} and {color_mode.name} color mode. "
        + f"A result will be passed to {callback.__name__}"
    )
    _pyindigo.set_ccd_mode(color_mode.value)
    _pyindigo.set_gain(float(gain))
    time.sleep(0.1)  # safety delay to let gain be accepted by device
    _pyindigo.set_shot_processing_callback(_report_on_exposition_end(callback))
    _exposing = True
    _pyindigo.take_shot_with_exposure(float(exposure))


def connected():
    return _pyindigo.check_if_device_is_connected()


def wait_for_exposure():
    """Convenience function to wait until exposure is done.
    Useful for avoiding camera destruction with unfinished exposure."""
    while _exposing:
        time.sleep(0.1)


def _report_on_exposition_end(callback):
    """Camera's internal decorator letting camera object know when exposure is finished"""
    def decorated_callback(*args):
        callback(*args)
        global _exposing
        _exposing = False
    return decorated_callback


if __name__ == "__main__":
    from callback_utils import prints_errors, accepts_hdu_list
    from astropy.io.fits import HDUList

    @prints_errors
    @accepts_hdu_list
    def dummy_callback(hdul: HDUList):
        print('callback run!')
        hdul.writeto('bw.fits')

    take_shot(0.01, 30, ColorMode.GREYSCALE, dummy_callback)
    wait_for_exposure()
