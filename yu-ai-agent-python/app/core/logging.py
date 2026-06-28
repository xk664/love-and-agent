"""
Logging Configuration
Supports JSON format for production, human-readable for development
"""
import logging
import logging.config
import sys
from pathlib import Path

from app.core.config import settings


# Log directory
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


# Logging format definitions
LOG_FORMATS = {
    "standard": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s",
    "json": '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
}


def get_logging_config() -> dict:
    """Get logging configuration based on environment"""
    is_debug = settings.app.DEBUG
    log_level = "DEBUG" if is_debug else "INFO"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": LOG_FORMATS["standard"]
            },
            "detailed": {
                "format": LOG_FORMATS["detailed"]
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "detailed" if is_debug else "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json" if not is_debug else "detailed",
                "filename": str(LOG_DIR / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json" if not is_debug else "detailed",
                "filename": str(LOG_DIR / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file", "error_file"],
                "level": log_level,
                "propagate": True,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING" if not is_debug else "INFO",
                "propagate": False,
            },
            "asyncpg": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
        },
        "root": {
            "handlers": ["console", "file", "error_file"],
            "level": log_level,
        },
    }

    return config


def setup_logging() -> logging.Logger:
    """
    Setup and configure logging for the application.
    Returns the root logger.
    Falls back to console-only logging if file handlers fail.
    """
    config = get_logging_config()

    try:
        logging.config.dictConfig(config)
    except (PermissionError, OSError) as e:
        # Fallback: console-only logging when file handlers fail
        print(f"Warning: File logging failed ({e}), falling back to console-only")
        config["handlers"] = {
            "console": config["handlers"]["console"],
        }
        config["root"]["handlers"] = ["console"]
        config["loggers"][""]["handlers"] = ["console"]
        logging.config.dictConfig(config)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
    logger.info(f"Log level: {settings.app.DEBUG and 'DEBUG' or 'INFO'}")
    logger.info(f"Log directory: {LOG_DIR}")

    return logging.getLogger()


# Initialize logging on module import
root_logger = setup_logging()


def get_logger(name: str) -> logging.Logger:
    """Get a named logger instance"""
    return logging.getLogger(name)
