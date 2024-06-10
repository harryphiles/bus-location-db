import os


OS_WORKING_DIR = {
    "nt": "",  # Windows
    "posix": os.path.expanduser("~"),  # Linux
}


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
    load_env()
    WORKING_DIRECTORY = (
        "/app/"
        if os.getenv("DOCKER_CONTAINER") == "true"
        else OS_WORKING_DIR.get(os.name)
    )
    SERVICE_KEY_BUS_API = os.getenv("SERVICE_KEY_BUS_API")
    BUS_ROUTE_ID = os.getenv("BUS_ROUTE_ID")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_TABLE_PARENT = os.getenv("DB_TABLE_PARENT")
    DB_TABLE_CHILD = os.getenv("DB_TABLE_CHILD")
