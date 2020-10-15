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

from dotenv import load_dotenv
from pathlib import Path

import _pyindigo


env_path = (Path(__file__).parent / '../.indigoenv').resolve()
load_dotenv(env_path)

camera_mode = os.environ.get('CAMERA_MODE', None)

if camera_mode == 'Simulator':
    DRIVER = 'indigo_ccd_simulator'
    DEVICE = 'CCD Imager Simulator'  # hard-coded until pyindigo upgrade
elif camera_mode == 'Real':
    DRIVER = 'indigo_ccd_asi'
    DEVICE = 'ZWO ASI120MC-S #0'  # hard-coded until pyindigo upgrade
else:
    raise OSError("CAMERA_MODE environment variable must be set to 'Real' or 'Simulator' (preferably in .env file)")


_pyindigo.set_device_name(DEVICE)
_pyindigo.setup_ccd_client(DRIVER)
time.sleep(5)  # workaround to give camera time to connect before usage

atexit.register(_pyindigo.cleanup_ccd_client)


def take_shot(exposure, gain, callback):
    """Request new shot from camera with given gain, exposure and callback for processing

    Note: use decorators from pyindigo.callback_utils to automatically add error catching, HDUList conversion and
    other handy features to your callback
    """
    global _exposing
    if not _pyindigo.check_if_device_is_connected():
        _exposing = False  # prevent mess if device is disconnected while exposing
        return
    if _exposing:
        return
    _pyindigo.set_gain(float(gain))
    time.sleep(0.1)  # safety delay to let gain be accepted by device
    _pyindigo.set_shot_processing_callback(_set_exposing_to_false_decorator(callback))
    _exposing = True
    _pyindigo.take_shot_with_exposure(float(exposure))


def wait_for_exposure():
    """Convenience function to wait until exposure is done.
    Useful for avoiding camera destruction with unfinished exposure."""
    while _exposing:
        time.sleep(0.1)


def _set_exposing_to_false_decorator(callback):
    """Camera's internal decorator letting camera object know when exposure is finished"""
    def decorated_callback(*args):
        callback(*args)
        global _exposing
        _exposing = False
    return decorated_callback


if __name__ == "__main__":
    def dummy_callback(b: bytes):
        print('callback run!')
        global callback_run
        callback_run = True

    callback_run = False
    take_shot(1, 50, dummy_callback)
    wait_for_exposure()
