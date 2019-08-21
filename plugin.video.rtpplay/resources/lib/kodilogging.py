# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from resources.lib.kodiutils import get_setting_as_bool

import logging
import xbmc
import xbmcaddon


class KodiLogHandler(logging.StreamHandler):

    def __init__(self):
        logging.StreamHandler.__init__(self)
        addon_id = xbmcaddon.Addon().getAddonInfo('id')
        prefix = "[%s] " % addon_id
        formatter = logging.Formatter(prefix + '%(name)s: %(message)s')
        self.setFormatter(formatter)

    def emit(self, record):
        levels = {
            logging.CRITICAL: xbmc.LOGFATAL,
            logging.ERROR: xbmc.LOGERROR,
            logging.WARNING: xbmc.LOGWARNING,
            logging.INFO: xbmc.LOGINFO,
            logging.DEBUG: xbmc.LOGDEBUG,
            logging.NOTSET: xbmc.LOGNONE,
        }
        if get_setting_as_bool('debug'):
            try:
                xbmc.log(self.format(record), levels[record.levelno])
            except UnicodeEncodeError:
                xbmc.log(self.format(record).encode(
                    'utf-8', 'ignore'), levels[record.levelno])

    def flush(self):
        pass


def config():
    logger = logging.getLogger()
    logger.addHandler(KodiLogHandler())
    logger.setLevel(logging.DEBUG)
