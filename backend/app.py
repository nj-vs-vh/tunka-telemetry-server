import asyncio

from quart import Quart

from camera_adapter import CameraAdapter


camera = CameraAdapter()

app = Quart(__name__)


@app.route('/api/latest-shot')
async def latest_shot():
    # return camera.latest_preview_base64, 200, {'Content-Type': 'image/jpeg'}
    return camera.latest_preview_base64


@app.route('/api/latest-shot-metadata')
async def latest_shot_metadata():
    return camera.latest_preview_metadata


# running camera and server concurrently in asyncio event loop

loop = asyncio.get_event_loop()
loop.create_task(camera.operation())
app.run(debug=False, use_reloader=False, loop=loop)

loop.run_forever()
