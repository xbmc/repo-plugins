# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2020  SylvainCecchetto, wwark

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

from kodi_six import xbmcaddon
from kodi_six import xbmc


def autorun_addon():
    if xbmcaddon.Addon().getSettingBool("auto_run"):
        xbmc.executebuiltin('RunAddon(plugin.video.catchuptvandmore)')
    return


autorun_addon()
