import numpy as np

from astropy.io.fits import HDUList
from PIL import Image


def save_fits_as_jpeg(hdul: HDUList, filename: str):
    data: np.ndarray = hdul[0].data
    vmin = data.min()
    vmax = data.max()
    data = (data - vmin)/(vmax - vmin)
    data = (255*data).astype(np.uint8)
    # data = data[::-1, :]

    image = Image.fromarray(data, 'L')
    image.save(filename)
