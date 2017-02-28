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
from xbmcplugin import addDirectoryItem
from xbmcplugin import addDirectoryItems
from xbmcplugin import endOfDirectory
from xbmcgui import ListItem
import routing

plugin = routing.Plugin()


@plugin.route('/')
def root():
    li = ListItem("Fatstone Live")
    li.setProperty('mimetype', "application/vnd.apple.mpegurl")
    li.setProperty('isplayable', 'true')
    li.setArt({'thumb': "http://dump.no/files/ea040880feb3/fatstonethumb.png"})
    li.setInfo('video', {'title': "Fatstone Live"})
    li.addStreamInfo('video', {'codec': 'h264', 'width': 1024, 'height': 576})
    li.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
    addDirectoryItem(plugin.handle, "http://usa1.cdn.trippelm.tv/fs/live/ngrp:live_all/manifest.m3u8", li, False)

    endOfDirectory(plugin.handle)

if __name__ == '__main__':
    plugin.run()
