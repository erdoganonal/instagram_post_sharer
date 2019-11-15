"""
    The log module that is used entire application.
"""
import logging

from settings import LOGGER_NAME, LOG_LEVEL, FILENAME, FORMAT


def _get_logger():
    logging.basicConfig(
        filename=FILENAME,
        level=logging.ERROR,
        format=FORMAT
    )
    module_logger = logging.getLogger(LOGGER_NAME)
    module_logger.setLevel(LOG_LEVEL)

    return module_logger


# pylint: disable=invalid-name
logger = _get_logger()
