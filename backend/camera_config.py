from watchgod import awatch

import yaml

from pathlib import Path

from pprint import pprint


CONFIG_PATH = Path(__file__).parent / '../camconfig.yaml'

config = dict()


def read_config():
    global config
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)


read_config()  # initial read


async def update_on_the_fly():
    """Watch for changes in config file and update it"""
    async for _ in awatch(CONFIG_PATH):
        read_config()
        print('config file updated:')
        pprint(config, indent=4)


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.create_task(update_on_the_fly())
    loop.run_forever()
