# encoding: utf-8
# Copyright (C) 2019-2020 ArvVoid (https://github.com/arvvoid)
# SPDX-License-Identifier: GPL-2.0-or-later
#########################################################

from __future__ import absolute_import, division

import sys
from hbogolib.base import hbogo
from kodi_six import xbmc, xbmcaddon  # type: ignore


# Setup plugin
PLUGIN_HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]
# We use string slicing to trim the leading ? from the plugin call paramstring
REQUEST_PARAMS = sys.argv[2][1:]


if __name__ == '__main__':
    add_on = xbmcaddon.Addon()
    xbmc.log("[" + add_on.getAddonInfo('id') + "]  STARTING VERSION: " + add_on.getAddonInfo('version'), xbmc.LOGDEBUG)
    addon_main = hbogo(PLUGIN_HANDLE, BASE_URL)
    addon_main.router(REQUEST_PARAMS)
