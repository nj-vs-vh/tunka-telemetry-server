from .celestial import get_celestial_observation_conditions
from .environmental import EnvironmentalConditionsReadingProtocol


def get_observation_conditions():
    return {
        **get_celestial_observation_conditions(),
        **EnvironmentalConditionsReadingProtocol.current_measurements_as_dict(),
    }
