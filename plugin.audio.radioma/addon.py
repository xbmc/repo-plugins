#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright 2011 Ayoub DARDORY.
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
from xbmcswift import Plugin, download_page
from xbmcswift.ext.playlist import playlist
from BeautifulSoup import BeautifulSoup as BS, SoupStrainer as SS

try:
    import json
except ImportError:
    import simplejson as json
from xbmcswift import xbmc, xbmcgui

__plugin__ = 'RadioMA'
__plugin_id__ = 'plugin.audio.radioma'

plugin = Plugin(__plugin__, __plugin_id__, __file__)

plugin.register_module(playlist, url_prefix='/_playlist')


def get_streams():
    url = 'http://radioma.ma/radiomaxbmc/radios.json'
    src = download_page(url)
    resp = json.loads(src)
    #Return a JSON list of the streams
    return resp


#### Plugin Views ####

# Default View
@plugin.route('/', default=True)
def show_homepage():
    Streams = get_streams()
    items = []
    for Station in Streams:
        items.append({'label': Station['Name'], 'url': plugin.url_for('startplay', URLStream=Station['URLStream'], Name=Station['Name'], Icon=Station['Icon']), 'thumbnail':Station['Icon']})
        
    return plugin.add_items(items)

@plugin.route('/live/<Name>/<URLStream>/<Icon>')
def startplay(URLStream, Name, Icon):
    rtmpurl = URLStream
    Thumb = Icon
    li = xbmcgui.ListItem(Name, Name, Thumb, Thumb)
    li.setInfo('music', {'Title':Name})
    xbmc.Player(xbmc.PLAYER_CORE_MPLAYER).play(rtmpurl, li)
    # Return an empty list so we can test with plugin.crawl() and plugin.interactive()
    return []

if __name__ == '__main__': 
    plugin.run()
