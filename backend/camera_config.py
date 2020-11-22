from pathlib import Path
from enum import Enum
import yaml

import logging

from watchgod import awatch
from dictdiffer import diff


CONFIG_PATH = Path(__file__).parent / '../camconfig.yaml'

camera_config = dict()


class CameraMode(Enum):
    """Keys from camconfig.yaml"""

    PREVIEW = 'preview'
    SAVE_TO_DISK = 'savetodisk'
    TESTING = 'testing'

    def __str__(self):
        return self.value


def update_config(verbose: bool):
    with open(CONFIG_PATH, 'r') as f:
        raw_new_config = yaml.safe_load(f)
        new_config = dict()
        for raw_key, mode_config in raw_new_config.items():
            try:
                mode = CameraMode(raw_key)
                new_config[mode] = mode_config
            except ValueError:
                logging.exception(
                    f'Invalid mode name "{raw_key}" in camconfig.yaml, ignoring! '
                    + f'Valid mode names are {", ".join(str(mode) for mode in list(CameraMode))}'
                )
    if verbose:
        config_diff = diff(camera_config, new_config)
        change_str = ''
        for change in config_diff:
            change_str += f'\t\t{".".join(str(field) for field in change[1])}: "{change[2][0]}" => "{change[2][1]}"\n'
        logging.info('config file updated:\n' + change_str)
    camera_config.update(new_config)


update_config(verbose=False)  # initial read


async def update_on_the_fly():
    """Watch for changes in config file and update it"""
    async for _ in awatch(CONFIG_PATH):
        update_config(verbose=True)


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.create_task(update_on_the_fly())
    loop.run_forever()
