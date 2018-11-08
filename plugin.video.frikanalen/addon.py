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
import urllib
import xbmc
import xbmcplugin
from xbmcaddon import Addon
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem
from xbmcplugin import addDirectoryItems
from xbmcplugin import endOfDirectory

import frikanalen

plugin = routing.Plugin()

# fake gettext style translation using kodi approach with IDs
def _(msg):
    map = {
        "Direkte":                    30001,
        "Sendeplan":                  30002,
        "Kategorier":                 30003,
        "Søk":                        30004,
        "Frikanalen akkurat nå (SD)": 30005,
        "Frikanalen akkurat nå (HD)": 30006,
    }
    if msg in map:
        return Addon().getLocalizedString(map[msg])
    else:
        return msg


@plugin.route('/')
def root():
    items = [
        (plugin.url_for(live), ListItem(_("Direkte")), True),
        (plugin.url_for(schedule), ListItem(_("Sendeplan")), True),
        (plugin.url_for(categories), ListItem(_("Kategorier")), True),
        (plugin.url_for(search), ListItem(_("Søk")), True),
    ]
    addDirectoryItems(plugin.handle, items)
    endOfDirectory(plugin.handle)

@plugin.route('/live')
def live():
    xbmcplugin.setContent(plugin.handle, 'videos')

    li = ListItem(_('Frikanalen akkurat nå (SD)'))
    li.setArt({'icon':'DefaultVideo.png'})
    li.setProperty('IsPlayable', 'true')

    info = {'mediatype': 'video'}
    # info['plot'] = ''
    li.setInfo('video', info)

    addDirectoryItem(handle=plugin.handle, url=frikanalen.stream_url(), listitem=li)

    li = ListItem(_('Frikanalen akkurat nå (HD)'))
    li.setArt({'icon':'DefaultVideo.png'})
    li.setProperty('IsPlayable', 'true')

    info = {'mediatype': 'video'}
    # info['plot'] = ''
    li.setInfo('video', info)

    addDirectoryItem(handle=plugin.handle, url=frikanalen.stream_url_hd(), listitem=li)

    endOfDirectory(plugin.handle)

def video_list(addon_handle, videos):
    xbmcplugin.setContent(addon_handle, 'videos')

    for video in videos:
        li = ListItem(video.name)
        li.setArt({'icon':video.large_thumbnail_url})
        li.setProperty('IsPlayable', 'true')
        # See https://mirrors.kodi.tv/docs/python-docs/16.x-jarvis/xbmcgui.html#ListItem
        info = {
            'mediatype': 'video',
            'plot': video.header,
            'duration': video.duration,
            'studio': video.organization,
        }
        li.setInfo('video', info)
        addDirectoryItem(handle=addon_handle, url=video.ogv_url, listitem=li)
    endOfDirectory(addon_handle)


@plugin.route('/schedule')
def schedule():
    today_program = frikanalen.today_programs()
    video_list(plugin.handle, [s.video for s in today_program])


@plugin.route('/category/<category>')
def category(category):
    category = urllib.unquote_plus(category)
    videos_in_category = frikanalen.in_category(category)
    video_list(plugin.handle, videos_in_category)


@plugin.route('/category')
def categories():
    categories = frikanalen.categories()
    xbmcplugin.setContent(plugin.handle, 'videos')
    items = [ (plugin.url_for(category, urllib.quote_plus(c)),  ListItem(c), True)
              for c in categories]
    addDirectoryItems(plugin.handle, items)
    endOfDirectory(plugin.handle)


@plugin.route('/search')
def search():
    keyboard = xbmc.Keyboard()
    keyboard.setHeading(_("Søk"))
    keyboard.doModal()
    query = keyboard.getText()
    if query:
        items = frikanalen.videosearch(query.decode('utf-8'))
        video_list(plugin.handle, items)


def run():
    plugin.run()
