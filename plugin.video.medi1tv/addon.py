#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# coding: utf-8
# Copyright 2012 Ayoub DARDORY.
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
from BeautifulSoup import BeautifulSoup as BS
from Medi1TVScraper import Medi1Shows, ShowEpisodes
from xbmcswift import Plugin, download_page, xbmc, xbmcgui
from xbmcswift.ext.playlist import playlist
from xml.sax.saxutils import unescape

try:
    import json
except ImportError:
    import simplejson as json


PLUGIN_NAME = 'Medi1TV'
PLUGIN_ID = 'plugin.video.medi1tv'

plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)
plugin.register_module(playlist, url_prefix='/_playlist')


@plugin.route('/', default=True)
def emission_ar():
    # Show's attributs :
    # ID
    # Title
    # Resume
    # Link
    # Thumbnail
    items = []
    
    Shows = Medi1Shows.load_shows('ar')
    for Show in Shows:
        items.append({'label': Show['title'],
                      'label2': Show['title'],
                      'url': plugin.url_for('list_episodes', Lang='ar', ID=Show['id']),
                      'thumbnail': Show['thumbnail'],
                      'icon': Show['thumbnail']})
    
    plugin.add_items(items)
    return []

@plugin.route('/list_episodes/<Lang>/<ID>')
def list_episodes(Lang, ID):
    # Title
    # Description
    # Date
    # Link
    # Thumbnail
    items = []
    
    Episodes = ShowEpisodes.load_videos(Lang, Medi1Shows.generate_link_show_randtitle(ID, Lang))

    for Episode in Episodes:
        items.append({'label': Episode['title'],
                      'label2': Episode['description'],
                      'url': plugin.url_for('play', title=Episode['title'], icon=Episode['thumbnail'], idShow=ID, idEpisode=Episode['id']),
                      'thumbnail': Episode['thumbnail']})
    
    plugin.add_items(items)
    return []
    
@plugin.route('/play/<title>/<icon>/<idShow>/<idEpisode>')
def play(title, icon, idShow, idEpisode):
    li = xbmcgui.ListItem(title, title, icon, icon)
    li.setInfo('video', {'Title':title})
    rtmplink = ShowEpisodes.episode_stream(idShow,idEpisode)
    xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(rtmplink, li)
    # Return an empty list so we can test with plugin.crawl() and
    # plugin.interactive()
    return []


if __name__ == '__main__': 
    plugin.run()
