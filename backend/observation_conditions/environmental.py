import asyncio
import serial_asyncio
from serial.serialutil import SerialException

from datetime import datetime
from pathlib import Path

import re
from dataclasses import dataclass
from typing import List, Optional, Dict

from pyindigo import logging


CONTROLLER_TTY = "/dev/ttyACM0"

LOGS_DIR = Path(__file__).parent.parent.parent / "observation-conditions-logs"


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

    def as_dict(self, key_style: str = 'json', include_timestamp: bool = False) -> Dict[str, str]:
        """"Set of measurements formatted as dict.
        
        Keys can be formatted as
            (1) valid identifiers, to use as JSON key
            (2) all-caps names with units integrated, to use in FITS headers
            (3) Human-readable, to use in tsv header
        """
        if key_style == 'json':
            format_name = lambda measurement: measurement.name
            timestamp_key = 'environmental_obs_conditions_timestamp_utc'
        elif key_style == 'fits':
            def format_name_for_fits(measurement: Measurement) -> str:
                name = measurement.name.replace('_', '-').upper()
                for patt, sub in {  # name shortening is applied here
                    'WINDOW': 'WND',
                    'TEMPERATURE': 'T',
                    'HEATING-POWER': 'POW',
                    'CAMERA': 'CAM',
                    'IS-ON': 'ON',
                    'ARDUINO': 'INO',
                    'EXTERNAL': 'EXT',
                    'HUMIDITY': 'HUM'
                }.items():
                    name = name.replace(patt, sub)
                return name

            format_name = format_name_for_fits
            timestamp_key = 'OBS-UTC'
        elif key_style == 'tsv':
            format_name = lambda measurement: (
                measurement.name.replace('_', ' ').capitalize() + ', ' + measurement.unit
            )
            timestamp_key = 'timestamp'
        else:
            raise ValueError(f"Unknown key_style {key_style}. Options are 'json', 'fits' or 'tsv'!")
        result = dict()
        if include_timestamp:
            result[timestamp_key] = str(self.timestamp)
        for m in self.measurements:
            result[format_name(m)] = m.value
        return result

    def __str__(self) -> str:
        return f"[{self.timestamp}] {'; '.join([str(m) for m in self.measurements])}"


class EnvironmentalConditionsReadingProtocol(asyncio.Protocol):
    _current_measurement_set: Optional[MeasurementSet] = None

    @classmethod
    def save_current_measurement_set(cls, ms):
        cls._current_measurement_set = ms

    def __init__(self):
        super().__init__()
        self.buffer = bytes()

    @classmethod
    def activate(cls, loop):
        """Activate protocol = start listening for serial messages while attached to the given loop"""
        try:
            loop.run_until_complete(serial_asyncio.create_serial_connection(loop, cls, CONTROLLER_TTY))
        except SerialException as e:
            logging.warning(f"Problem opening TTY controller, continuing without it. Details: {e}")

    def process_buffer(self):
        self.save_current_measurement_set(
            self.parse_measurement_set(self.buffer.decode())
        )
        
        dict_to_dump = self._current_measurement_set.as_dict(key_style='tsv', include_timestamp=True)
        current_log_file = LOGS_DIR / f'obs_conditions_{datetime.utcnow().strftime(r"%Y_%m_%d")}.tsv'
        if not current_log_file.exists():
            with open(current_log_file, 'w') as f:
                f.write('\t'.join(dict_to_dump.keys()) + '\n')
        with open(current_log_file, 'a') as f:
            f.write('\t'.join(dict_to_dump.values()) + '\n')

    @classmethod
    def current_measurements_as_dict(self, key_style: str = 'json', include_timestamp: bool = False) -> Dict[str, str]:
        """"Current measurement formatted to dict. See MeasurementSet.as_dict for details.
        
        If no current measurement is available (connection with controller is lost or it simply has not been done yet),
        empty dict is returned."""
        if self._current_measurement_set is None:
            return dict()
        return self._current_measurement_set.as_dict(key_style, include_timestamp)

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
                try:
                    name, value = measurement_str.split(' ')
                    value = '1' if value == 'on' else '0'
                except Exception as e:
                    logging.warning(
                        f"Error while parsing measurement read from TTY controller '{measurement_str}': {e}"
                    )
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
            try:
                self.process_buffer()
            except Exception as e:
                logging.warning(f"Error occurred while processing buffer from TTY controller. Details: {e}")
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
