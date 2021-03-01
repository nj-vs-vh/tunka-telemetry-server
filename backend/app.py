import os
import asyncio

from pyindigo import logging

from quart import Quart, Response
from hypercorn.asyncio import serve
from hypercorn.config import Config

from pathlib import Path
from dotenv import load_dotenv

from camera_adapter import CameraAdapter
import camera_config
from observation_conditions import observation_conditions


env_path = (Path(__file__).parent / '.env').resolve()
load_dotenv(env_path)

# see https://docs.python.org/3/library/logging.html#logging.basicConfig
logging_config = {'format': r'[%(asctime)s] %(levelname)s: %(message)s', 'datefmt': r'%x %X'}
log_filename = os.environ.get("LOG_FILENAME", None)
if log_filename:
    logging_config['filename'] = str((Path(__file__).parent.parent / log_filename).resolve())
log_level = os.environ.get("LOG_LEVEL", None)
if log_level:
    logging_config['level'] = getattr(logging, log_level)  # log_level.DEBUG, log_level.INFO, etc
logging.basicConfig(**logging_config)
logging.pyindigoConfig(log_device_connection=True, lop_callback_exceptions=True)


app = Quart(__name__)

loop = asyncio.get_event_loop()

camera = CameraAdapter(mode=os.environ.get('CAMERA_MODE', None), loop=loop)


@app.route('/api/camera-feed')
async def camera_feed():
    async def preview_feed():
        async for image, _ in camera.preview_feed_generator():
            yield b"--shot\r\n" + b"Content-Type: image/jpeg\r\n\r\n" + image + b"\r\n"
    res = Response(preview_feed(), mimetype="multipart/x-mixed-replace; boundary=shot")
    res.timeout = None
    return res


@app.route('/api/latest-camera-metadata')
async def latest_camera_metadata():
    if camera.preview_metadata is None:
        return {"message": "No available metadata"}, 500
    else:
        return camera.preview_metadata


@app.route('/api/observation-conditions')
async def obs_conditions():
    return observation_conditions()


# running camera and server concurrently in asyncio event loop

loop.create_task(camera.operate())
loop.create_task(camera_config.update_on_the_fly())

serve_with = os.environ.get('SERVE_WITH', None)

try:
    if serve_with == 'Hypercorn':
        loop.run_until_complete(serve(app, Config()))
    elif serve_with == 'Quart_run':
        app.run(debug=False, use_reloader=False, loop=loop, port=8000)
        loop.run_forever()
    else:
        raise OSError(
            "SERVE_WITH environment variable must be set to 'Hypercorn' or 'Quart_run' (preferably in .quartenv file)"
        )
finally:
    loop.close()
