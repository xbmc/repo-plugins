# -*- coding: utf-8 -*-
"""Log handler for Kodi"""

from __future__ import absolute_import, division, unicode_literals

import logging

import xbmc
import xbmcaddon

from resources.lib import kodiutils

ADDON = xbmcaddon.Addon()


class KodiLogHandler(logging.StreamHandler):
    """ A log handler for Kodi """

    def __init__(self):
        logging.StreamHandler.__init__(self)
        formatter = logging.Formatter("[{}] [%(name)s] %(message)s".format(ADDON.getAddonInfo("id")))
        self.setFormatter(formatter)
        # xbmc.LOGNOTICE is deprecated in Kodi 19 Matrix
        if kodiutils.kodi_version_major() > 18:
            self.info_level = xbmc.LOGINFO
        else:
            self.info_level = xbmc.LOGNOTICE

    def emit(self, record):
        """ Emit a log message """
        levels = {
            logging.CRITICAL: xbmc.LOGFATAL,
            logging.ERROR: xbmc.LOGERROR,
            logging.WARNING: xbmc.LOGWARNING,
            logging.INFO: self.info_level,
            logging.DEBUG: xbmc.LOGDEBUG,
            logging.NOTSET: xbmc.LOGNONE,
        }

        # Map DEBUG level to info_level if debug logging setting has been activated
        # This is for troubleshooting only
        if ADDON.getSetting('debug_logging') == 'true':
            levels[logging.DEBUG] = self.info_level

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
