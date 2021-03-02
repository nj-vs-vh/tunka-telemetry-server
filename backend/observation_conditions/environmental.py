import asyncio
import serial_asyncio

from datetime import datetime

import re
from dataclasses import dataclass
from typing import List, Optional, Dict


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


class EnvironmentalConditionsReadingProtocol(asyncio.Protocol):
    _current_measurement_set: Optional[MeasurementSet] = None

    def __init__(self):
        super().__init__()
        self.buffer = bytes()

    @classmethod
    def activate(cls, loop):
        """Activate protocol = start listening for serial messages while attached to the given loop"""
        loop.run_until_complete(serial_asyncio.create_serial_connection(loop, cls, CONTROLLER_TTY))

    def process_buffer(self):
        m = self.parse_measurement_set(self.buffer.decode())
        self._current_measurement_set = m

    @classmethod
    def current_measurements_as_dict(self, key_style: str = 'json') -> Dict[str, str]:
        """"Current measurement formatted to dict.
        
        Keys are either measurement names (valid identifiers, JSON-friendly) or all-caps names with units
        (FITS header-friendly).
        
        If no current measurement is available (connection with controller is lost or it simply has not been done yet),
        empty dict is returned."""
        if self._current_measurement_set is None:
            return dict()
        if key_style == 'json':
            format_name = lambda measurement: measurement.name
        elif key_style == 'fits':
            format_name = lambda measurement: (
                measurement.name.replace('_', '-').upper()
                + '-'
                + measurement.units.encode('ascii', errors='ignore').decode().upper()
            )
        else:
            raise ValueError(f"Unknown key_style {key_style}. Options are 'json' and 'fits'!")
        return {format_name(m): m.value for m in self._current_measurement_set.measurements}

    @staticmethod
    def parse_measurement_set(line: str) -> MeasurementSet:
        measurement_strs = [m.strip() for m in line.split(',')]

        measurement_names_mapping = {
            'Window T': 'window_temperature',
            'Win.heat. P': 'window_heating_power',
            'Camera T': 'camera_temperature',
            'Cam.heat. P': 'camera_heating_power',
            'Fan': 'fan_is_on',
            'Arduino T': 'arduino_temperature',
            'Ext. T': 'external_temperature',
            'Hum.': 'external_humidity',
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
        """Measurements are invalidated if controller is not available"""
        self._current_measurement_set = None

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

    async def dummy_action():
        while True:
            print('...')
            await asyncio.sleep(2)

    loop = asyncio.get_event_loop()
    EnvironmentalConditionsReadingProtocol.activate(loop)
    try:
        loop.run_until_complete(dummy())
    finally:
        loop.close()
        print('done!')
