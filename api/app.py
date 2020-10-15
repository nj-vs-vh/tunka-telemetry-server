from flask import Flask
from pathlib import Path
from astropy.io.fits import HDUList

from ..pyindigo import camera
from ..pyindigo.callback_utils import prints_errors, accepts_hdu_list

from .fitsutils import save_fits_as_jpeg


static_dir = Path('static')
current_shot_path = static_dir / 'current_shot.jpeg'


@prints_errors
@accepts_hdu_list
def save_fits_to_file(hdul: HDUList):
    if current_shot_path.exists():
        current_shot_path.unlink()
    save_fits_as_jpeg(hdul, current_shot_path)


camera.take_shot(0.1, 100, save_fits_to_file)

camera.wait_for_exposure()


app = Flask(__name__)


@app.route('/api/latest-shot')
def get_latest_shot():
    return app.send_static_file(str(current_shot_path))


if __name__ == "__main__":
    app.run()
