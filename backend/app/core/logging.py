import logging
import logging.config
import sys
from typing import Dict, Any
from .config import settings


def setup_logging():
    """Configure application logging."""
    
    log_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
                "level": settings.LOG_LEVEL,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": "app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "detailed",
                "level": "DEBUG",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"] if settings.DEBUG else ["console"],
                "level": settings.LOG_LEVEL,
                "propagate": True,
            },
            "app": {
                "handlers": ["console", "file"] if settings.DEBUG else ["console"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    
    logging.config.dictConfig(log_config)
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")
    
    return logger


# Create module logger
logger = logging.getLogger(__name__)