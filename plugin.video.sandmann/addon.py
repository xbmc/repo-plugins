# -*- coding: utf-8 -*-
# Copyright 2019 sorax
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys
from threading import Timer

from sandmann import getEpisodes

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon

episodes_url = "https://appdata.ardmediathek.de/appdata/servlet/tv/Sendung?documentId=6503982&json"

addon = xbmcaddon.Addon()
# addon_name = addon.getAddonInfo("name")
# addon_icon = addon.getAddonInfo("icon")

addon_handle = int(sys.argv[1])
base_path = sys.argv[0]

quality = addon.getSettingInt("quality")
update = addon.getSettingInt("update")
interval = addon.getSettingInt("interval")
dgs = addon.getSettingBool("dgs")

refresh_timer = None


def addEpisodes():
    episodes = getEpisodes(episodes_url, quality, dgs)
    episode_list = []
    for episode in episodes:
        episode_list.append((episode["stream"], getListItem(episode), False))

    xbmcplugin.addDirectoryItems(addon_handle, episode_list, len(episode_list))


def getListItem(item):
    li = xbmcgui.ListItem(label=item["title"])
    li.setArt({
        "thumb": item["thumb"],
        "fanart": item["fanart"]
    })
    li.setInfo(
        type="video",
        infoLabels={
            "title": item["title"],
            "plot": item["desc"],
            "duration": item["duration"]
        }
    )
    li.setProperty("IsPlayable", "true")
    return li


def reload():
    xbmc.executebuiltin("Container.Refresh()")


if update == 0:
    global refresh_timer
    # xbmc.executebuiltin("Notification(%s, %s, %d, %s)" %
    #                     (addon_name, "Updating...", 5000, addon_icon))
    refresh_timer = Timer(interval * 60 * 60, reload)
    refresh_timer.start()
    # refresh_timer.cancel()


if update == 1:
    li_refresh = xbmcgui.ListItem(
        label=addon.getLocalizedString(30020))
    xbmcplugin.addDirectoryItem(addon_handle, base_path, li_refresh, True)


addEpisodes()
xbmcplugin.endOfDirectory(addon_handle)
