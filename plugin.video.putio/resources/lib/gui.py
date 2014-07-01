# coding: utf-8
#
# put.io xbmc addon
# Copyright (C) 2009  Alper Kanat <tunix@raptiye.org>
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import os

import xbmc
import xbmcaddon as xa
import xbmcgui as xg
import xbmcplugin as xp
from resources import PLUGIN_ID

__all__ = ("populateDir", "play")

addon = xa.Addon(PLUGIN_ID)


def populateDir(pluginUrl, pluginId, listing):
    for item in listing:
        if item.screenshot:
            screenshot = item.screenshot
        else:
            screenshot = os.path.join(
                addon.getAddonInfo("path"),
                "resources",
                "images",
                "mid-folder.png"
            )

        url = "%s?%s" % (pluginUrl, item.id)
        listItem = xg.ListItem(
            item.name,
            item.name,
            screenshot,
            screenshot
        )

        listItem.setInfo(item.content_type, {
            'originaltitle': item.name,
            'title': item.name,
            'sorttitle': item.name
        })

        xp.addDirectoryItem(
            pluginId,
            url,
            listItem,
            "application/x-directory" == item.content_type
        )

    xp.endOfDirectory(pluginId)


def play(item, subtitle=None):
    player = xbmc.Player()

    if item.screenshot:
        screenshot = item.screenshot
    else:
        screenshot = item.icon

    listItem = xg.ListItem(
        item.name,
        item.name,
        screenshot,
        screenshot
    )

    listItem.setInfo('video', {'Title': item.name})
    player.play(item.stream_url, listItem)

    if subtitle:
        print "Adding subtitle to player!"
        player.setSubtitles(subtitle)
