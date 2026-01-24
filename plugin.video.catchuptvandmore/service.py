# -*- coding: utf-8 -*-
# Copyright: (c) 2020, SylvainCecchetto, wwark
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from kodi_six import xbmc, xbmcaddon


def autorun_addon():
    if xbmcaddon.Addon().getSetting("auto_run") == "true":
        xbmc.executebuiltin('RunAddon(plugin.video.catchuptvandmore)')
    return


autorun_addon()
