import os
import asyncio
from pathlib import Path


from quart import Quart, websocket
from hypercorn.asyncio import serve
from hypercorn.config import Config

from pyindigo import logging
from pyindigo.core import IndigoLogLevel, set_indigo_log_level

from camera_adapter import CameraAdapter
import camera_config
from observation_conditions import get_observation_conditions, EnvironmentalConditionsReadingProtocol

import read_dotenv  # noqa


# see https://docs.python.org/3/library/logging.html#logging.basicConfig
logging_config = {'format': r'[%(asctime)s] %(levelname)s: %(message)s', 'datefmt': r'%x %X'}
log_filename = os.environ.get("LOG_FILENAME", None)
if log_filename:
    logging_config['filename'] = str((Path(__file__).parent.parent / log_filename).resolve())
log_level = os.environ.get("LOG_LEVEL", None)
if log_level:
    logging_config['level'] = getattr(logging, log_level)  # log_level.DEBUG, log_level.INFO, etc
logging.basicConfig(**logging_config)

indigo_debug_settings = os.environ.get("INDIGO_DEBUG", None)
if indigo_debug_settings:
    indigo_debug_args = {
        f'log_{setting.strip().lower()}': True for setting in indigo_debug_settings.split(',')
    }
    logging.pyindigoConfig(**indigo_debug_args)

native_inidgo_log_level = os.environ.get("NATIVE_INDIGO_LOG_LEVEL", None)
if native_inidgo_log_level:
    set_indigo_log_level(IndigoLogLevel[native_inidgo_log_level])


loop = asyncio.get_event_loop()

if os.environ.get('READ_FROM_TTY_CONTROLLER', None) == 'yes':
    EnvironmentalConditionsReadingProtocol.activate(loop)

camera = CameraAdapter(mode=os.environ.get('CAMERA_MODE', None), loop=loop)
loop.create_task(camera.operate())

loop.create_task(camera_config.update_on_the_fly())


app = Quart(__name__)


@app.websocket('/ws/camera-feed')
async def ws_camera_feed():
    if camera.preview_metadata is not None:
        await websocket.send_json(camera.preview_metadata)
        await websocket.send(camera.preview)
    async for image, metadata in camera.preview_feed_generator():
        await websocket.send_json(metadata)
        await websocket.send(image)


@app.route('/api/observation-conditions')
async def obs_conditions():
    return get_observation_conditions()


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
    logging.info("==================== CAMERA SERVER GOING OFFLINE ====================")
