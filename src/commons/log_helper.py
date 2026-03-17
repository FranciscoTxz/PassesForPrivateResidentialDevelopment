import logging
import os
from logging import Logger
from sys import stdout

_name_to_level = {
    "CRITICAL": logging.CRITICAL,
    "FATAL": logging.FATAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

logger = logging.getLogger(__name__)
logger.propagate = False
console_handler = logging.StreamHandler(stream=stdout)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
)
logger.addHandler(console_handler)


log_level = _name_to_level.get(os.environ.get("log_level") or "INFO")
logging.captureWarnings(True)


def get_logger(log_name, level=log_level) -> Logger:
    module_logger = logger.getChild(log_name)
    if level:
        module_logger.setLevel(level)
    return module_logger
