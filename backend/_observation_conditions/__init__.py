from .celestial import get_celestial_observation_conditions


def get_observation_conditions():
    return {
        **get_celestial_observation_conditions()
        # **
    }
