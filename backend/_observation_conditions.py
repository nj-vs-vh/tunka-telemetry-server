from datetime import datetime
import ephem
import pytz
from math import pi

import logging

from typing import Dict, Any, Union


def heating_controller_info():
    def value_from_key_equals_value(k_eq_v: str) -> str:
        return k_eq_v.split('=')[1].strip(r'°CW%')

    controller_tty = "/dev/ttyACM0"
    try:
        with open(controller_tty, 'r') as controller:
            print(controller.read(1))
            # data = controller.readline().strip()
        data = 'a=1, b=2, c=3'
        data = data.split(', ')
        return {
            'external_temp': value_from_key_equals_value(data[-2]),
            'external_humidity': value_from_key_equals_value(data[-1]),
        }
    except Exception as e:
        logging.exception(f'Exception while reading from heating controller TTY: {e}')
        return dict()


def to_radians(degrees: float) -> float:
    return pi * degrees / 180


irkutsk = pytz.timezone('Asia/Irkutsk')


def localtime_str(dt: Union[datetime, ephem.Date]) -> str:
    if isinstance(dt, ephem.Date):
        dt = ephem.to_timezone(dt, irkutsk)
    elif isinstance(dt, datetime):
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            dt = pytz.utc.localize(dt)
        dt = dt.astimezone(irkutsk)
    else:
        raise ValueError(f"dt must be datetime or ephem.Date, not {dt.__class__.__name__}")
    return dt.strftime(r'%Y/%m/%d %X')


sit = ephem.Observer()
sit.lon, sit.lat = '103.0409', '51.4848'  # SIT location in Tunka

sit.elevation = 680
sit.pressure = 950
sit.temp = -15

sun, moon = ephem.Sun(), ephem.Moon()


def observation_conditions() -> Dict[str, Any]:
    sit.date = ephem.Date(datetime.utcnow())
    sun.compute(sit)
    moon.compute(sit)
    return {
        'local_time': localtime_str(datetime.utcnow()),
        'is_night': sun.alt < 0.0,
        'is_astronomical_night': sun.alt < to_radians(-18),  # definition of astronomical night
        'sunrise': {
            'previous': localtime_str(sit.previous_rising(sun)),
            'next': localtime_str(sit.next_rising(sun))
        },
        'sunset': {
            'previous': localtime_str(sit.previous_setting(sun)),
            'next': localtime_str(sit.next_setting(sun))
        },
        'is_moonless': moon.alt < 0.0,
        'moonrise': {
            'previous': localtime_str(sit.previous_rising(moon)),
            'next': localtime_str(sit.next_rising(moon))
        },
        'moonset': {
            'previous': localtime_str(sit.previous_setting(moon)),
            'next': localtime_str(sit.next_setting(moon))
        },
        # **heating_controller_info(),
    }


if __name__ == "__main__":
    from time import sleep

    for i in range(3):
        print(observation_conditions())
        sleep(3)
