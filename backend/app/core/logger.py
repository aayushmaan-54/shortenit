import logging
from logging.config import dictConfig

from .config import settings

LOG_LEVEL = "DEBUG" if settings.debug else "INFO"
ACTIVE_FORMATTER = "standard" if settings.debug else "json"

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # ensures Uvicorn startup & error loggers logs aren't silenced
    "formatters": {  # Shape of the log output
        "standard": {  # Name of the formatter
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%d-%m-%Y %H:%M:%S",
        },
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            # JSON keys that will appear in the log output
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
    },
    "handlers": {  # Destination of the log output
        "console": {  # Name of the handler
            "class": "logging.StreamHandler",
            "formatter": ACTIVE_FORMATTER,  # formatter name
            "level": LOG_LEVEL,
            "stream": "ext://sys.stdout",  # Default: use stderr, but we want to use stdout for container app
        },
    },
    "loggers": {  # Define loggers for python
        "root": {  # Root logger
            "handlers": ["console"],
            "level": "WARNING",  # Hardcoded
        },
        "app": {  # Logger name
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        # Override Uvicorn's default logger for HTTP access logs
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",  # Hardcoded
            "propagate": False,
        },
        # Override Uvicorn's startup/shutdown & error logs
        "uvicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

dictConfig(LOGGING_CONFIG)

logger = logging.getLogger("app")
