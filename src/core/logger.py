import logging
import logging.config as logging_config
from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    json = "json"
    default = "default"
    simple = "simple"


class LoggerConfig(BaseSettings):
    level: LogLevel = Field(default=LogLevel.INFO)
    format: LogFormat = Field(default=LogFormat.default)

    model_config = SettingsConfigDict(env_prefix="LOG_")


log_config = LoggerConfig()

LOGGING_CONFIG = {
    "version": 1,
    "filters": {
        "correlation_id": {
            "()": "asgi_correlation_id.CorrelationIdFilter",
            "uuid_length": 32,
            "default_value": "-",
        },
    },
    "formatters": {
        "default": {
            "format": "%(asctime)s:%(name)s:%(process)d:%(lineno)d %(levelname)s [%(correlation_id)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[%(correlation_id)s] %(message)s",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": """
                    asctime: %(asctime)s
                    created: %(created)f
                    filename: %(filename)s
                    funcName: %(funcName)s
                    levelname: %(levelname)s
                    levelno: %(levelno)s
                    lineno: %(lineno)d
                    request_id: %(correlation_id)s
                    message: %(message)s
                    module: %(module)s
                    msec: %(msecs)d
                    name: %(name)s
                    pathname: %(pathname)s
                    process: %(process)d
                    processName: %(processName)s
                    relativeCreated: %(relativeCreated)d
                    thread: %(thread)d
                    threadName: %(threadName)s
                    exc_info: %(exc_info)s
                """,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console_handler": {
            "filters": ["correlation_id"],
            "level": log_config.level.value,
            "formatter": log_config.format.value,
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "app": {
            "level": log_config.level.value,
            "handlers": [
                "console_handler",
            ],
            "propagate": False,
        },
        "uvicorn": {"handlers": ["console_handler"], "level": "INFO"},
        "uvicorn.error": {"level": "CRITICAL", "handlers": ["console_handler"], "propagate": False},
        "uvicorn.access": {"handlers": ["console_handler"], "level": "INFO", "propagate": False},
    },
    "root": {
        "level": log_config.level.value,
        "handlers": [
            "console_handler",
        ],
    },
}

logging_config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("app")
