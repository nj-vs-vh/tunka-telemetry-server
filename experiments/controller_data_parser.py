from dataclasses import dataclass
from typing import List
import re
import serial


@dataclass
class Measurement:
    name: str
    value: str
    unit: str

    def __str__(self) -> str:
        return f"{self.name}, {self.unit} = {self.value}"


def parse_measurements(line: str) -> List[Measurement]:
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
    return measurements


controller_tty = '/dev/ttyACM0'

with serial.Serial(controller_tty) as controller:
    line = controller.readline()
    line = line.decode()
    measurements = parse_measurements(line)
    for m in measurements:
        print(m)
