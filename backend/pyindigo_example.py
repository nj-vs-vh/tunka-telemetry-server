from astropy.io.fits import HDUList
from pathlib import Path
from datetime import datetime

from pyindigo import camera
from pyindigo.callback_utils import prints_errors, accepts_hdu_list

from fitsutils import save_fits_as_jpeg


images_path = Path('images').resolve()


@prints_errors
@accepts_hdu_list
def save_fits_to_file(hdul: HDUList):
    # hdul.writeto(images_path / f'IMG_{datetime.now().strftime("%Y_%m_%d_%X")}.fits')
    save_fits_as_jpeg(hdul, images_path / f'IMG_{datetime.now().strftime("%Y_%m_%d_%X")}.jpeg')


camera.take_shot(0.01, 10, save_fits_to_file)

camera.wait_for_exposure()
