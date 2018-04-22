# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import os
import sys
from resources.lib import simpleplugin as sp

PLUGIN = sp.Plugin()
ADDON = sp.Addon()

CACHE_TIME = 10

PLUGIN_NAME = 'Catch-up TV & More'

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
GETTEXT = ADDON.initialize_gettext()

FILESYSTEM_CODING = sys.getfilesystemencoding()
if sys.getfilesystemencoding() is None:
    FILESYSTEM_CODING = "utf-8"

ADDON_DATA = sp.xbmc.translatePath(
    os.path.join(
        'special://profile/addon_data',
        ADDON.id
    )
)

MEDIA_PATH = sp.xbmc.translatePath(
    os.path.join(
        ADDON.path,
        "resources",
        "media"
    )
)

LIB_PATH = sp.xbmc.translatePath(
    os.path.join(
        ADDON.path,
        "resources",
        "lib"
    )
)


def get_window_title():
    query = sp.sys.argv[2][1:]
    params = PLUGIN.get_params(query)
    if 'window_title' in params:
        return params.window_title
    else:
        return PLUGIN_NAME
