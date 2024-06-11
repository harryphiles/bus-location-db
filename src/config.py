import os
from pathlib import Path
import time


OS_WORKING_DIR = {
    "nt": "",  # Windows
    "posix": (
        "" if os.path.expanduser("~") == "/root" else os.path.expanduser("~")
    ),  # Linux
}

parent_folder_name = Path(__file__).resolve().parent.name


def load_env():
    """Look for .env file and load env variables"""
    env_file_path = ".env"
    if os.path.exists(env_file_path):
        with open(env_file_path, encoding="utf-8") as fp:
            for line in fp:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value


class Config:
    APP_NAME = ["bus", "location", "db"]
    SYSTEM_TIMEZONE = time.tzname[0]
    WORKING_DIRECTORY = OS_WORKING_DIR.get(os.name)
    load_env()
    SERVICE_KEY_BUS_API = os.getenv("SERVICE_KEY_BUS_API")
    BUS_ROUTE_ID = os.getenv("BUS_ROUTE_ID")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_TABLE_PARENT = os.getenv("DB_TABLE_PARENT")
    DB_TABLE_CHILD = os.getenv("DB_TABLE_CHILD")
