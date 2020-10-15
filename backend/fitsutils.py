import numpy as np

from astropy.io.fits import HDUList
from PIL import Image

from typing import Dict, Any


def save_fits_as_jpeg(hdul: HDUList, filename: str):
    data: np.ndarray = hdul[0].data
    vmin = data.min()
    vmax = data.max()
    data = (data - vmin)/(vmax - vmin)
    data = (255*data).astype(np.uint8)
    # data = data[::-1, :]

    image = Image.fromarray(data, 'L')
    image.save(filename, format='jpeg')


fits_fields_to_metadata_fields = {
    'EXPTIME': 'exposure',
    'CCD-TEMP': 'device temperature',
    'GAIN': 'gain',
    'DATE-OBS': 'device time'
}


def extract_metadata(hdul: HDUList) -> Dict[str, Any]:
    fits_header_dict = {k: v for k, v in hdul[0].header.items()}
    metadata = dict()
    for fits_key, meta_key in fits_fields_to_metadata_fields.items():
        metadata[meta_key] = fits_header_dict.get(fits_key, 'NOT SET')
    return metadata
