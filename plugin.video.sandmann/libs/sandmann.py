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

from libs.show import getEpisodes
from libs.episode import mapEpisode, appendStreams


# -- Addon --
addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
addon_name = addon.getAddonInfo("name")
addon_icon = addon.getAddonInfo("icon")

base_path = sys.argv[0]


# -- Constants --
sources = {
    "rbb": "https://api.ardmediathek.de/page-gateway/widgets/ard/asset/Y3JpZDovL3JiYi1vbmxpbmUuZGUvc2FuZG1hbm4?pageNumber=0&pageSize=18",
    "mdr": "https://api.ardmediathek.de/page-gateway/widgets/ard/asset/Y3JpZDovL21kci5kZS9zZW5kZXJlaWhlbi84NjY2ZjI5OS02ZGU3LTQwNjMtODY4MS01NjA5ZWVlMzI4OGU"
}


# -- Settings --
dgs = addon.getSettingInt("dgs2")
interval = addon.getSettingInt("interval2")
quality = addon.getSettingInt("quality2")
update = addon.getSettingInt("update2")
source = addon.getSettingInt("source2")


def sandmann():
    if update == 1:
        li_refresh = xbmcgui.ListItem(label=addon.getLocalizedString(30020))
        xbmcplugin.addDirectoryItem(addon_handle, base_path, li_refresh, True)

    url = sources["rbb"]
    if source == 1:
        url = sources["mdr"]

    episodes = getEpisodes(url)
    episodes2 = map(mapEpisode, episodes)
    episodes3 = filterDgs(episodes2, dgs)
    episodes4 = map(appendStreams, episodes3)

    item_list = []
    for episode in episodes4:
        item_list.append((getStream(episode, quality), getListItem(episode), False))

    xbmcplugin.addDirectoryItems(addon_handle, item_list, len(item_list))

    xbmcplugin.endOfDirectory(addon_handle)


def filterDgs(episodes, dgs):
    if dgs == 0:
        return [e for e in episodes if e["dgs"] == False]
    elif dgs == 2:
        return [e for e in episodes if e["dgs"] == True]
    else:
        return episodes


def getStream(episode, quality):
    streams = episode["streams"]

    index = quality - 1
    if index in streams:
        return streams[index]
    else:
        return streams["auto"]


def getListItem(item):
    li = xbmcgui.ListItem()
    li.setLabel(item["title"])
    li.setArt({
        "fanart": item["fanart"],
        "thumb": item["thumb"]
    })
    li.setInfo(
        type="video",
        infoLabels={
            "aired": item["date"],
            "duration": item["duration"],
            "plot": item["desc"],
        }
    )
    li.setProperty("IsPlayable", "true")

    return li
