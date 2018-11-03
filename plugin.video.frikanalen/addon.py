# -*- coding: utf-8 -*-
#
# Copyright (C) 2016 Petter Reinholdtsen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import routing
import xbmcplugin
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem
from xbmcplugin import addDirectoryItems
from xbmcplugin import endOfDirectory

import frikanalen

plugin = routing.Plugin()

@plugin.route('/')
def root():
    items = [
        (plugin.url_for(live), ListItem("Direkte"), True),
        (plugin.url_for(schedule), ListItem("Sendeplan"), True),
    ]
    addDirectoryItems(plugin.handle, items)
    endOfDirectory(plugin.handle)

@plugin.route('/live')
def live():
    addon_handle = plugin.handle

    xbmcplugin.setContent(addon_handle, 'videos')

    li = ListItem('Frikanalen-sending (SD)', iconImage='DefaultVideo.png')
    li.setProperty('IsPlayable', 'true')

    info = {'mediatype': 'video'}
    # info['plot'] = ''
    li.setInfo('video', info)

    addDirectoryItem(handle=addon_handle, url=frikanalen.stream_url(), listitem=li)

    li = ListItem('Frikanalen-sending (HD)', iconImage='DefaultVideo.png')
    li.setProperty('IsPlayable', 'true')

    info = {'mediatype': 'video'}
    # info['plot'] = ''
    li.setInfo('video', info)

    addDirectoryItem(handle=addon_handle, url=frikanalen.stream_url_hd(), listitem=li)

    endOfDirectory(addon_handle)

@plugin.route('/schedule')
def schedule():
    today_program = frikanalen.today_programs()
    addon_handle = plugin.handle
    xbmcplugin.setContent(addon_handle, 'videos')

    for s in today_program:
        video = s.video
        li = ListItem(video.name, iconImage=video.large_thumbnail_url)
        li.setProperty('IsPlayable', 'true')
        info = {'mediatype': 'video', 'plot': video.header}
        li.setInfo('video', info)
        addDirectoryItem(handle=addon_handle, url=video.ogv_url, listitem=li)
    endOfDirectory(plugin.handle)

def run():
    plugin.run()
