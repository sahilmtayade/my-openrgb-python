import os

from logger_tt import logger, setup_logging

DEBUG = os.environ.get("DEBUG", "0") == "1"
LOGGING_SETUP = False


def debug_print(*args, **kwargs):
    global LOGGING_SETUP
    if DEBUG:
        if not LOGGING_SETUP:
            setup_logging(log_path="debug.log")
            LOGGING_SETUP = True
        logger.debug(*args, **kwargs)
