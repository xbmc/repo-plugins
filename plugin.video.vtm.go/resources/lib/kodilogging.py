# -*- coding: utf-8 -*-
"""Log handler for Kodi"""

from __future__ import absolute_import, division, unicode_literals

import logging

import xbmc
import xbmcaddon

ADDON = xbmcaddon.Addon()


class KodiLogHandler(logging.StreamHandler):
    """ A log handler for Kodi """

    def __init__(self):
        logging.StreamHandler.__init__(self)
        formatter = logging.Formatter("[{}] [%(name)s] %(message)s".format(ADDON.getAddonInfo("id")))
        self.setFormatter(formatter)

    def emit(self, record):
        """ Emit a log message """
        levels = {
            logging.CRITICAL: xbmc.LOGFATAL,
            logging.ERROR: xbmc.LOGERROR,
            logging.WARNING: xbmc.LOGWARNING,
            logging.INFO: xbmc.LOGNOTICE,
            logging.DEBUG: xbmc.LOGDEBUG,
            logging.NOTSET: xbmc.LOGNONE,
        }

        # Map DEBUG level to LOGNOTICE if debug logging setting has been activated
        # This is for troubleshooting only
        if ADDON.getSetting('debug_logging') == 'true':
            levels[logging.DEBUG] = xbmc.LOGNOTICE

        try:
            xbmc.log(self.format(record), levels[record.levelno])
        except UnicodeEncodeError:
            xbmc.log(self.format(record).encode('utf-8', 'ignore'), levels[record.levelno])

    def flush(self):
        """ Flush the messages """


def config():
    """ Setup the logger with this handler """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Make sure we pass all messages, Kodi will do some filtering itself.
    logger.addHandler(KodiLogHandler())
