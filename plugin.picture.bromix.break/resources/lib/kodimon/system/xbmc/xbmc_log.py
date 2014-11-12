__author__ = 'bromix'

import xbmc
from ...constants import *


def log(text, log_level=LOG_NOTICE):
    xbmc.log(msg=text, level=log_level)
    pass
