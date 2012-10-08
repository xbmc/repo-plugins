#!/usr/bin/env python
# -*- coding: UTF-8 -*-
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

from xbmcswift import Plugin, download_page, xbmc, xbmcgui
from xbmcswift.ext.playlist import playlist


PLUGIN_NAME = 'OffeneKanaele'
PLUGIN_ID = 'plugin.video.offene_kanaele'


plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)
plugin.register_module(playlist, url_prefix='/_playlist')


@plugin.route('/', default=True)
def show_homepage():
    items = [
        # Berlin
        {'label': 'Berlin',
         'url': plugin.url_for('berlin')},
        # Dessau
        {'label': 'Dessau',
         'url': plugin.url_for('dessau')},
        # Landau, Neustadt & Haßloch
        {'label': 'Landau, Neustadt & Haßloch',
         'url': plugin.url_for('landau')},
        # Magdeburg
        {'label': 'Magdeburg',
         'url': plugin.url_for('magdeburg')},                  
        # Merseburg
        {'label': 'Merseburg',
         'url': plugin.url_for('merseburg')},                           
        # Pirmasens, Rodalben & Zweibrücken
        {'label': 'Pirmasens, Rodalben & Zweibrücken',
         'url': plugin.url_for('pirmasens')},
        # Salzwedel
        {'label': 'Salzwedel',
         'url': plugin.url_for('salzwedel')},
        # Speyer
        {'label': 'Speyer',
         'url': plugin.url_for('speyer')},
        # Stendal
        {'label': 'Stendal',
         'url': plugin.url_for('stendal')},                  
        # Trier
        {'label': 'Trier',
         'url': plugin.url_for('trier')},                  
        # Wernigerode
        {'label': 'Wernigerode',
         'url': plugin.url_for('wernigerode')}
    ]
    return plugin.add_items(items)


@plugin.route('/berlin/')
def berlin():
    url = 'http://alex-stream.rosebud-media.de:1935/live/alexlivetv.smil/playlist.m3u8'
    li = xbmcgui.ListItem('Berlin')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []

@plugin.route('/dessau/')
def dessau():
    url = 'http://62.113.210.250/medienasa-live/_definst_/mp4:ok-dessau_high/playlist.m3u8'
    li = xbmcgui.ListItem('Dessau')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []

@plugin.route('/landau/')
def landau():
    url = 'mms://streaming.ok54.de/okweinstrasse'
    li = xbmcgui.ListItem('Landau, Neustadt & Haßloch')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []

@plugin.route('/magdeburg/')
def magdeburg():
    url = 'http://62.113.210.250/medienasa-live/_definst_/mp4:ok-magdeburg_high/playlist.m3u8'
    li = xbmcgui.ListItem('Magdeburg')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []

@plugin.route('/merseburg/')
def merseburg():
    url = 'http://62.113.210.250/medienasa-live/_definst_/mp4:ok-merseburg_high/playlist.m3u8'
    li = xbmcgui.ListItem('Merseburg')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []

@plugin.route('/pirmasens/')
def pirmasens():
    url = 'mms://streaming.ok54.de/suedwestpfalz-tv'
    li = xbmcgui.ListItem('Pirmasens, Rodalben & Zweibrücken')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []                

@plugin.route('/salzwedel/')
def salzwedel():
    url = 'http://62.113.210.250/medienasa-live/_definst_/mp4:ok-salzwedel_high/playlist.m3u8'
    li = xbmcgui.ListItem('Salzwedel')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []

@plugin.route('/speyer/')
def speyer():
    url = 'http://s2.fairprice-streams.de:9420/;stream.nsv'
    li = xbmcgui.ListItem('Speyer')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []

@plugin.route('/stendal/')
def stendal():
    url = 'http://62.113.210.250/medienasa-live/_definst_/mp4:ok-stendal_high/playlist.m3u8'
    li = xbmcgui.ListItem('Stendal')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []

@plugin.route('/trier/')
def trier():
    url = 'mms://streaming.ok54.de/ok54'
    li = xbmcgui.ListItem('Trier')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []

@plugin.route('/wernigerode/')
def wernigerode():
    url = 'http://62.113.210.250/medienasa-live/_definst_/mp4:ok-wernigerode_high/playlist.m3u8'
    li = xbmcgui.ListItem('Wernigerode')
    xbmc.Player(xbmc.PLAYER_CORE_AUTO).play(url, li)
    return []

if __name__ == '__main__':
    plugin.run()
    