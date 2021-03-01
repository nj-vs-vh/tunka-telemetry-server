from dotenv import load_dotenv
from pathlib import Path

env_path = (Path(__file__).parent / '.env').resolve()
load_dotenv(env_path)
