import logging
import inspect

_LOGGER = logging.getLogger(__name__)


class Logger:

    @staticmethod
    def info(msg):
        filename = inspect.stack()[1].filename
        lineno = inspect.stack()[1].lineno
        _LOGGER.info(f' [{filename}] [{lineno}行]:{msg}')

    @staticmethod
    def error(msg):
        filename = inspect.stack()[1].filename
        lineno = inspect.stack()[1].lineno
        _LOGGER.error(f'[{filename}] [{lineno}行]:{msg}')

    @staticmethod
    def debug(msg):
        filename = inspect.stack()[1].filename
        lineno = inspect.stack()[1].lineno
        _LOGGER.debug(f' [{filename}] [{lineno}行]:{msg}')
