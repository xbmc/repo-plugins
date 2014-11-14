__all__ = ['LOG_DEBUG', 'LOG_INFO', 'LOG_NOTICE', 'LOG_WARNING', 'LOG_ERROR', 'LOG_SEVERE', 'LOG_FATAL', 'LOG_NONE',
           'log', 'log_debug', 'log_error', 'log_notice', 'log_warning']

__author__ = 'bromix'

from .constants import *


def log(text, log_level=LOG_NOTICE):
    """
    Needs to be implemented by a mock for testing or the real deal.
    Logging.
    :param text:
    :param log_level:
    :return:
    """
    raise NotImplementedError()


def log_debug(text):
    log(text, LOG_DEBUG)
    pass


def log_notice(text):
    log(text, LOG_NOTICE)
    pass


def log_warning(text):
    log(text, LOG_WARNING)
    pass


def log_error(text):
    log(text, LOG_ERROR)
    pass


try:
    from .system.xbmc.xbmc_log import log
except ImportError, ex:
    from .system.mock.mock_log import log

    pass