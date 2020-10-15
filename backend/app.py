import time
import asyncio

from quart import Quart
from pathlib import Path
from astropy.io.fits import HDUList

from pyindigo import camera
from pyindigo.callback_utils import prints_errors, accepts_hdu_list

from fitsutils import save_fits_as_jpeg


static_dir = Path(__file__).parent / 'static'
current_shot_path = static_dir / 'current_shot.jpeg'


@prints_errors
@accepts_hdu_list
def save_fits_to_file(hdul: HDUList):
    if current_shot_path.exists():
        current_shot_path.unlink()
    save_fits_as_jpeg(hdul, current_shot_path)
    print('new shot ready!')


async def take_shots_regularly(period):
    """Main coroutine to take shots with camera each 'period' seconds"""
    print('coroutine entered')
    while True:
        exposure_start = time.time()
        camera.take_shot(0.01, 30, save_fits_to_file)
        exposure_duration = time.time() - exposure_start
        await asyncio.sleep(period - exposure_duration)


app = Quart(__name__, static_url_path='')


@app.route('/api/latest-shot')
async def get_latest_shot():
    return await app.send_static_file(str(current_shot_path.name))


# if __name__ == "__main__":
loop = asyncio.get_event_loop()
task = loop.create_task(take_shots_regularly(3))

app.run(debug=False, use_reloader=False, loop=loop)

loop.run_forever()
