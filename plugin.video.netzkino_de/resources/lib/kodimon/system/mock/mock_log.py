__author__ = 'bromix'

from ...constants import *


def log(text, log_level=LOG_NOTICE):
    log_level_2_string = {LOG_DEBUG: 'DEBUG',
                          LOG_INFO: 'INFO',
                          LOG_NOTICE: 'NOTICE',
                          LOG_WARNING: 'WARNING',
                          LOG_ERROR: 'ERROR',
                          LOG_SEVERE: 'SEVERE',
                          LOG_FATAL: 'FATAL',
                          LOG_NONE: 'NONE'}

    log_text = "[%s] %s" % (log_level_2_string.get(log_level, 'UNKNOWN'), text)
    print log_text.encode('utf-8')
    pass
