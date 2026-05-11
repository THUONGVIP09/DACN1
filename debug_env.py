import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / '.env'
print(f"Checking path: {env_path.absolute()}")
print(f"Path exists: {env_path.exists()}")

load_dotenv(dotenv_path=env_path)
key = os.getenv("GOOGLE_VISION_API_KEY")
print(f"LOADED API KEY: '{key}'")
