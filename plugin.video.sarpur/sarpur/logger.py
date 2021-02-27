#!/usr/bin/env python
# encoding: UTF-8

from __future__ import absolute_import
import xbmc
import sarpur


def log(message, level=xbmc.LOGDEBUG):
    """
    This is the preferred way to log things in Kodi (rather than using print)

    :param message to log
    """
    if sarpur.LOGGING_ENABLED:
        xbmc.log(message, level=level)
