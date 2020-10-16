import asyncio

from quart import Quart, Response

from camera_adapter import CameraAdapter


camera = CameraAdapter()

app = Quart(__name__)


@app.route('/api/camera-feed')
async def camera_feed():
    async def preview_feed():
        async for image, _ in camera.preview_feed_generator():
            yield b"--shot\r\n" + b"Content-Type: image/jpeg\r\n\r\n" + image + b"\r\n"
    return Response(preview_feed(), mimetype="multipart/x-mixed-replace; boundary=shot")


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
loop.create_task(camera.operation())
app.run(debug=False, use_reloader=False, loop=loop)

loop.run_forever()
