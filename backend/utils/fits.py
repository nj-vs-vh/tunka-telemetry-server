import numpy as np
from nptyping import NDArray

from astropy.io.fits import HDUList
from PIL import Image

from typing import Dict, Any


def normalize_frame(frame: NDArray, bits: int = 8) -> NDArray:
    frame = frame.astype(float)
    frame_min = frame.min()
    frame_range = frame.max() - frame_min
    return ((2 ** bits - 1) * (frame - frame_min) / frame_range).astype('int8')


def save_fits_as_jpeg(hdul: HDUList, filename: str):
    image_data: NDArray = hdul[0].data.copy()
    if image_data.ndim == 3:
        image_data = np.transpose(image_data, (1, 2, 0))
        image_data = normalize_frame(image_data)
        image = Image.fromarray(image_data, 'RGB')
    elif image_data.ndim == 2:
        image_data = normalize_frame(image_data)
        image = Image.fromarray(image_data, 'L')
    image.save(filename, format='jpeg')


fits_fields_to_metadata_fields = {
    'EXPTIME': 'exposure',
    'CCD-TEMP': 'device_temperature',
    'GAIN': 'gain',
    'DATE-OBS': 'device_time'
}


def extract_metadata(hdul: HDUList) -> Dict[str, Any]:
    fits_header_dict = {k: v for k, v in hdul[0].header.items()}
    metadata = dict()
    for fits_key, meta_key in fits_fields_to_metadata_fields.items():
        metadata[meta_key] = fits_header_dict.get(fits_key, 'NOT SET')
    return metadata


def fits_bytes_to_hdu_list(fits_bytes: bytes) -> HDUList:
    if isinstance(fits_bytes, bytes):
        try:
            return HDUList.fromstring(fits_bytes)
        except Exception:
            raise ValueError("Unable to convert bytes to HDUList object")
    else:
        raise TypeError(f"Expected bytes as an argument, got {fits_bytes.__class__.__name__}")
