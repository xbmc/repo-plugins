# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Håkon Nessjøen
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

import time
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
from xbmcplugin import addDirectoryItem
from xbmcplugin import addDirectoryItems
from xbmcplugin import endOfDirectory
import routing
import m3u8

__settings__   = xbmcaddon.Addon(id='plugin.video.fatstone')
__language__ = __settings__.getLocalizedString

plugin = routing.Plugin()

M3U_ERROR_TITLE = 30007
M3U_ERROR_MESSAGE = 30008

@plugin.route('/')
def root():
    url = 'http://usa1.cdn.trippelm.tv/fs/live/ngrp:live_all/'
    m3u8_obj = m3u8.load(url + 'manifest.m3u8')
    if m3u8_obj.is_variant:
        for playlist in m3u8_obj.playlists:
            width, height = playlist.stream_info.resolution
            li = xbmcgui.ListItem("Fatstone Live (" + repr(playlist.stream_info.bandwidth / 1024) + " kbps) " + repr(height) + 'p')
            li.setProperty('mimetype', "application/vnd.apple.mpegurl")
            li.setProperty('isplayable', 'true')
            li.setArt({'thumb': "http://dump.no/files/ea040880feb3/fatstonethumb.png"})
            li.setInfo('video', {'title': "Fatstone Live" })
            li.addStreamInfo('video', {'codec': 'h264', 'width': int(width), 'height': int(height) })
            li.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
            addDirectoryItem(plugin.handle, url + playlist.uri, li, False)
    else:
        xbmcgui.Dialog().notification(__language__(M3U_ERROR_TITLE), __language__(M3U_ERROR_MESSAGE), xbmcgui.NOTIFICATION_ERROR)
    
    endOfDirectory(plugin.handle)

if __name__ == '__main__':
    plugin.run()
