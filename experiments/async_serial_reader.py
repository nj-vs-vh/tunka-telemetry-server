import asyncio
import serial_asyncio


CONTROLLER_TTY = "/dev/ttyACM0"


class MeasurementsReadingProtocol(asyncio.Protocol):

    def __init__(self):
        super().__init__()
        self.buffer = bytes()

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport.loop.stop()

    def data_received(self, data):
        self.buffer += data
        if b'\n' in data:
            print(self.buffer)
            self.buffer = bytes()

    def pause_writing(self):
        pass

    def resume_writing(self):
        pass


async def dummy():
    while True:
        print('...')
        await asyncio.sleep(2)


loop = asyncio.get_event_loop()
loop.run_until_complete(
    serial_asyncio.create_serial_connection(loop, MeasurementsReadingProtocol, CONTROLLER_TTY)
)
loop.run_until_complete(dummy())
loop.run_forever()
loop.close()
