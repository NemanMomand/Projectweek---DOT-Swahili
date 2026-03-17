import logging
from logging.config import dictConfig

from pythonjsonlogger.jsonlogger import JsonFormatter

from app.core.config import get_settings


class DotSwahiliJsonFormatter(JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record.setdefault("level", record.levelname)
        log_record.setdefault("logger", record.name)


def setup_logging() -> None:
    settings = get_settings()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": DotSwahiliJsonFormatter,
                    "fmt": "%(asctime)s %(level)s %(name)s %(message)s",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "level": settings.log_level,
                }
            },
            "root": {"handlers": ["default"], "level": settings.log_level},
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
