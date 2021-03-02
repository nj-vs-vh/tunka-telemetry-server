import asyncio
import serial_asyncio


CONTROLLER_TTY = "/dev/ttyACM0"


class MeasurementsReadingProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport.loop.stop()

    def data_received(self, data):
        print('data received', repr(data))

    def pause_writing(self):
        pass

    def resume_writing(self):
        pass


async def dummy():
    while True:
        print('...')
        await asyncio.sleep(1)


loop = asyncio.get_event_loop()
loop.run_until_complete(
    serial_asyncio.create_serial_connection(loop, MeasurementsReadingProtocol, CONTROLLER_TTY)
)
loop.run_until_complete(dummy())
loop.run_forever()
loop.close()
