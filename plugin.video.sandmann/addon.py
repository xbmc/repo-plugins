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
import threading

from sandmann import getEpisodeData

import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon

episodes_url = "https://appdata.ardmediathek.de/appdata/servlet/tv/Sendung?documentId=6503982&json"

addon = xbmcaddon.Addon()
# addon_name = addon.getAddonInfo('name')
# addon_icon = addon.getAddonInfo('icon')

addon_handle = int(sys.argv[1])
base_path = sys.argv[0]

quality = addon.getSettingInt("quality")
update = addon.getSettingInt("update")
interval = addon.getSettingInt("interval")

title, description, thumbnail_image, fanart_image, stream = getEpisodeData(
    episodes_url, quality)

li_episode = xbmcgui.ListItem(label=title)
li_episode.setArt({'thumb': thumbnail_image, 'fanart': fanart_image})
li_episode.setInfo(type="Video", infoLabels={
    "Title": title, "Plot": description
})
xbmcplugin.addDirectoryItem(addon_handle, stream, li_episode, False)


def reload():
    # xbmc.executebuiltin('Notification(%s, %s, %d, %s)' %
    #                     (addon_name, "Updating...", 5000, addon_icon))
    xbmc.executebuiltin('Container.Refresh()')
    threading.Timer(interval * 60 * 60, reload).start()


if update == 0:
    threading.Timer(interval * 60 * 60, reload).start()


if update == 1:
    li_refresh = xbmcgui.ListItem(
        label=addon.getLocalizedString(30020))
    xbmcplugin.addDirectoryItem(addon_handle, base_path, li_refresh, True)


xbmcplugin.endOfDirectory(addon_handle)
