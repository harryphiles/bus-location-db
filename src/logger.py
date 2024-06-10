import logging.config
from typing import Optional


class Logger:
    def __init__(self, name: str, log_config: dict, file_name: Optional[str]) -> None:
        self.logger = logging.getLogger(name)
        self.log_config = log_config
        if file_name:
            self.log_config["handlers"]["file"]["filename"] = file_name
        logging.config.dictConfig(config=log_config)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {},
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "encoding": "utf-8",
            "filename": "logs/my_app.log",
            "maxBytes": 100000,
            "backupCount": 5,
        }
    },
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": [
                "file",
            ],
        }
    },
}
