import os
import asyncio
from pathlib import Path
from datetime import datetime

from quart import Quart, websocket
from hypercorn.asyncio import serve
from hypercorn.config import Config

from pyindigo import logging
from pyindigo.core import IndigoLogLevel, set_indigo_log_level

from camera_adapter import CameraAdapter
import camera_config
from observation_conditions import get_observation_conditions, run_environmental_conditions_monitor

import read_dotenv  # noqa


CUR_DIR = Path(__file__).parent.resolve()
ROOT_DIR = CUR_DIR.parent
SERVER_LOG = ROOT_DIR / "server.log"
CAMERA_LOG = ROOT_DIR / "camera.log"

PREVIOUS_LOGS_DIR = ROOT_DIR / 'previous_logs'
PREVIOUS_LOGS_DIR.mkdir(exist_ok=True)
now_str = datetime.utcnow().isoformat()
for log in [SERVER_LOG, CAMERA_LOG]:
    log.rename(PREVIOUS_LOGS_DIR / f"{log.stem}.before.{now_str}.log")

# logging setup
# see https://docs.python.org/3/library/logging.html#logging.basicConfig
logging_config = {"format": r"[%(asctime)s] %(levelname)s: %(message)s", "datefmt": r"%x %X", "filename": CAMERA_LOG}
log_level = os.environ.get("LOG_LEVEL", "INFO")
logging_config["level"] = getattr(logging, log_level)  # log_level.DEBUG, log_level.INFO, etc
logging.basicConfig(**logging_config)

indigo_debug_settings = os.environ.get("INDIGO_DEBUG", None)
if indigo_debug_settings:
    indigo_debug_args = {f"log_{setting.strip().lower()}": True for setting in indigo_debug_settings.split(",")}
    logging.pyindigoConfig(**indigo_debug_args)

native_inidgo_log_level = os.environ.get("NATIVE_INDIGO_LOG_LEVEL", None)
if native_inidgo_log_level:
    set_indigo_log_level(IndigoLogLevel[native_inidgo_log_level])


# loop setup, non-Quart tasks startup
loop = asyncio.get_event_loop()
if os.environ.get("READ_FROM_TTY_CONTROLLER", None) == "yes":
    run_environmental_conditions_monitor(loop)
camera = CameraAdapter(mode=os.environ.get("CAMERA_MODE", None), loop=loop)
loop.create_task(camera.operate())
loop.create_task(camera_config.update_on_the_fly())


# Quart web app setup
FRONTENT_BUILD = CUR_DIR / "../frontend/build"
STATIC_DIR = FRONTENT_BUILD.resolve()

app = Quart(__name__, static_folder=str(STATIC_DIR), static_url_path="/")


@app.websocket("/ws/camera-feed")
async def ws_camera_feed():
    if camera.preview_metadata is not None:
        await websocket.send_json(camera.preview_metadata)
        await websocket.send(camera.preview)
    async for image, metadata in camera.preview_feed_generator():
        await websocket.send_json(metadata)
        await websocket.send(image)


@app.route("/api/observation-conditions")
async def obs_conditions():
    return get_observation_conditions()


@app.route("/", methods=["GET"])
async def index():
    return await app.send_static_file("index.html")


@app.route("/<path>", methods=["GET"])
async def static_file(path: str):
    return await app.send_static_file(path)


# serving Quart app

serve_with = os.environ.get("SERVE_WITH", None)

try:
    PORT = int(os.environ.get("PORT", 8000))
    if serve_with == "Hypercorn":
        config = Config()
        config.bind = f'0.0.0.0:{PORT}'
        config.workers = 1
        config.errorlog = str(SERVER_LOG.resolve())
        config.accesslog = str(SERVER_LOG.resolve())
        loop.run_until_complete(serve(app, config))
    elif serve_with == "Quart_run":
        app.run(debug=False, use_reloader=False, loop=loop, port=PORT)
        loop.run_forever()
    else:
        raise OSError(
            "SERVE_WITH environment variable must be set to 'Hypercorn' or 'Quart_run' (preferably in .env file)"
        )
finally:
    loop.close()
    logging.info("==================== CAMERA SERVER GOING OFFLINE ====================")
