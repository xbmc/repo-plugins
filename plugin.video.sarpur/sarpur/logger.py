#!/usr/bin/env python
# encoding: UTF-8

import xbmc
import sarpur

def log(message):
    """
    .. py:function:: log(message)

    This is the preferred way to log things in XBMC (rahter than using print)

    :param message to log
    """
    if sarpur.LOGGING_ENABLED:
        xbmc.log(message)
