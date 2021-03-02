import asyncio
import serial_asyncio

from datetime import datetime

import re
from dataclasses import dataclass
from typing import List


CONTROLLER_TTY = "/dev/ttyACM0"


@dataclass
class Measurement:
    name: str
    value: str
    unit: str

    def __str__(self) -> str:
        return f"{self.name}, {self.unit} = {self.value}"


@dataclass
class MeasurementSet:
    measurements: List[Measurement]
    timestamp: datetime

    def __str__(self) -> str:
        return f"[{self.timestamp}] {'; '.join([str(m) for m in self.measurements])}"


class MeasurementsReadingProtocol(asyncio.Protocol):
    measurments_log = {}

    def __init__(self):
        super().__init__()
        self.buffer = bytes()

    def process_buffer(self):
        ms = self.parse_measurement_set(self.buffer.decode())
        print(ms)

    @staticmethod
    def parse_measurement_set(line: str) -> MeasurementSet:
        measurement_strs = [m.strip() for m in line.split(',')]

        measurement_names_mapping = {
            'Window T': 'Window Temperature',
            'Win.heat. P': 'Window Heating Power',
            'Camera T': 'Camera Temperature',
            'Cam.heat. P': 'Camera Heating Power',
            'Fan': 'Fan is on',
            'Arduino T': 'Arduino Temperature',
            'Ext. T': 'External Temperature',
            'Hum.': 'External Humidity'
        }

        measurements = []
        for measurement_str in measurement_strs:
            try:
                name, value = measurement_str.split('=')
            except ValueError:  # special case for 'Fan off'
                name, value = measurement_str.split(' ')
                value = '1' if value == 'on' else '0'
            except Exception:
                continue

            name = measurement_names_mapping.get(name, name)
            value_and_unit_split = re.split(r'([^\-\.0-9])', value.strip(), maxsplit=1)
            value = value_and_unit_split[0]
            unit = ''.join(value_and_unit_split[1:]) if len(value_and_unit_split) > 1 else 'logical'
            measurements.append(Measurement(name, value, unit))
        return MeasurementSet(measurements, timestamp=datetime.utcnow())

    # boilerplate from pyserial-asyncio

    def connection_made(self, transport):
        self.transport = transport

    def connection_lost(self, exc):
        self.transport.loop.stop()

    def data_received(self, data):
        self.buffer += data
        if b'\n' in data:
            self.process_buffer()
            self.buffer = bytes()

    def pause_writing(self):
        pass

    def resume_writing(self):
        pass


if __name__ == "__main__":

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
