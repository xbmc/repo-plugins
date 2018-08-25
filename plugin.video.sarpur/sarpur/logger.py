#!/usr/bin/env python
# encoding: UTF-8

import xbmc
import sarpur


def log(message, level=xbmc.LOGNOTICE):
    """
    This is the preferred way to log things in Kodi (rather than using print)

    :param message to log
    """
    if sarpur.LOGGING_ENABLED:
        xbmc.log(message, level=level)
