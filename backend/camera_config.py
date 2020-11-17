from pathlib import Path
from watchgod import awatch
import logging
import yaml


CONFIG_PATH = Path(__file__).parent / '../camconfig.yaml'

config = dict()


def update_config():
    global config
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)


def get_camera_config():
    return config


update_config()  # initial read


async def update_on_the_fly():
    """Watch for changes in config file and update it"""
    async for _ in awatch(CONFIG_PATH):
        update_config()
        logging.info(f'config file updated:\n' + '\n'.join('\t\t' + line for line in yaml.dump(config).split('\n')))


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.create_task(update_on_the_fly())
    loop.run_forever()
