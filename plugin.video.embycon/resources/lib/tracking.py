# Gnu General Public License - see LICENSE.TXT

import sys
import functools
import time
from .simple_logging import SimpleLogging

log = SimpleLogging(__name__)

enabled = False

def set_timing_enabled(val):
    global enabled
    enabled = val

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        started = time.time()
        value = func(*args, **kwargs)
        ended = time.time()
        if enabled:
            data = ""
            if func.__name__ == "downloadUrl" and len(args) > 1:
                data = args[1]
            elif func.__name__ == "mainEntryPoint" and len(sys.argv) > 2:
                data = sys.argv[2]
            log.info("timing_data|{0}|{1}|{2}|{3}", func.__name__ , started, ended, data)
        return value
    return wrapper