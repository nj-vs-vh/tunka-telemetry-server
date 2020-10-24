import os
import asyncio

from quart import Quart, Response
from hypercorn.asyncio import serve
from hypercorn.config import Config

from pathlib import Path
from dotenv import load_dotenv

from camera_adapter import CameraAdapter
import camera_config


camera = CameraAdapter()

app = Quart(__name__)


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
        return Response({"message": "Try reconnecting camera"}, 500)
    else:
        return camera.preview_metadata


@app.route('/api/force-camera-reconnect')
async def force_camera_reconnect():
    camera.reconnect()
    if camera.terminal_failure:
        return Response({"message": "Camera has failed and cannot be reconnected, server reboot required :("}, 500)
    else:
        return Response({"message": "Reconnected ok"}, 200)


# running camera and server concurrently in asyncio event loop

loop = asyncio.get_event_loop()
loop.create_task(camera.operate())
loop.create_task(camera_config.update_on_the_fly())

env_path = (Path(__file__).parent / '.quartenv').resolve()
load_dotenv(env_path)
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
