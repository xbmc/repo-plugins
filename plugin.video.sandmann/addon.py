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

from sandmann import getEpisodeData

# import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon

episodes_url = "https://appdata.ardmediathek.de/appdata/servlet/tv/Sendung?documentId=6503982&json"

addon = xbmcaddon.Addon()
quality = int(addon.getSetting("quality"))

title, thumbnail_image, fanart_image, stream = getEpisodeData(
    episodes_url, quality)

li = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail_image)
li.setProperty("fanart_image", fanart_image)

addon_handle = int(sys.argv[1])
xbmcplugin.addDirectoryItem(addon_handle, stream, li, False)
xbmcplugin.endOfDirectory(addon_handle)
