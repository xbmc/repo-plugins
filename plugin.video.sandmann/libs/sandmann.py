# -*- coding: utf-8 -*-
# Copyright 2022 sorax
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

import xbmcaddon
import xbmcgui
import xbmcplugin

import sys

from libs.episodes import getEpisodes


# -- Addon --
addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
addon_name = addon.getAddonInfo("name")
addon_icon = addon.getAddonInfo("icon")

base_path = sys.argv[0]

# -- Constants --
sources = {
    "rbb": "https://api.ardmediathek.de/page-gateway/widgets/ard/asset/Y3JpZDovL3JiYi1vbmxpbmUuZGUvc2FuZG1hbm4",
    "mdr": "https://api.ardmediathek.de/page-gateway/widgets/ard/asset/Y3JpZDovL21kci5kZS9zZW5kZXJlaWhlbi84NjY2ZjI5OS02ZGU3LTQwNjMtODY4MS01NjA5ZWVlMzI4OGU"
}


# -- Settings --
dgs = addon.getSettingInt("dgs2")
interval = addon.getSettingInt("interval2")
quality = addon.getSettingInt("quality2")
update = addon.getSettingInt("update2")
source = addon.getSettingInt("source2")


def sandmann():
    episodes_url = sources["rbb"]
    if source == 1:
        episodes_url = sources["mdr"]

    episodes_list = getEpisodes(episodes_url, quality)

    item_list = []
    for episode in episodes_list:
        if dgs == 0 and episode["dgs"] == False:
            item_list.append((episode["stream"], getListItem(episode), False))
        if dgs == 1:
            item_list.append((episode["stream"], getListItem(episode), False))
        if dgs == 2 and episode["dgs"] == True:
            item_list.append((episode["stream"], getListItem(episode), False))

    xbmcplugin.addDirectoryItems(addon_handle, item_list, len(item_list))

    if update == 1:
        li_refresh = xbmcgui.ListItem(label=addon.getLocalizedString(30020))
        xbmcplugin.addDirectoryItem(addon_handle, base_path, li_refresh, True)

    xbmcplugin.endOfDirectory(addon_handle)


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
