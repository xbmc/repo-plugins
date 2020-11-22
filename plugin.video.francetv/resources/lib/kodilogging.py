# coding: utf-8
#
# Copyright © 2015 Thomas Amland
# Copyright © 2020 melmorabity
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

from __future__ import unicode_literals
import logging
from logging import Formatter
from logging import StreamHandler

import xbmc  # pylint: disable=import-error
import xbmcaddon  # pylint: disable=import-error


class KodiLogHandler(StreamHandler):
    def __init__(self):
        StreamHandler.__init__(self)

        self._addon = xbmcaddon.Addon()
        addon_id = self._addon.getAddonInfo("id")
        formatter = Formatter("[{}] %(message)s".format(addon_id))
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

        if self._addon.getSetting("debug_logging") == "true":
            levels[logging.DEBUG] = xbmc.LOGINFO

        try:
            xbmc.log(self.format(record), levels[record.levelno])
        except UnicodeEncodeError:
            xbmc.log(
                self.format(record).encode("utf-8", "ignore"),
                levels[record.levelno],
            )

    def flush(self):
        pass


def config():
    logger = logging.getLogger()
    # Make sure we pass all messages, Kodi will do some filtering itself.
    logger.setLevel(logging.DEBUG)
    logger.addHandler(KodiLogHandler())
