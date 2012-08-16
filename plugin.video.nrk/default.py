# -*- coding: utf-8 -*-
'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import os
import sys
import time
import xbmc, xbmcaddon, xbmcplugin
import data
import subs

from itertools import repeat
from xbmcplugin import addDirectoryItem
from xbmcplugin import endOfDirectory
from xbmcgui import ListItem
from plugin import plugin

ADDON = xbmcaddon.Addon()
ADDON_PATH = ADDON.getAddonInfo('path')
BITRATE = int(ADDON.getSetting('bitrate')) + 1
SHOW_SUBS = ADDON.getSetting('showsubtitles')


@plugin.route('/')
def view_top():
  addDirectoryItem(plugin.handle, plugin.url_for("/live"), ListItem("Direkte"), True)
  addDirectoryItem(plugin.handle, plugin.url_for("/recommended"), ListItem("Aktuelt"), True)
  addDirectoryItem(plugin.handle, plugin.url_for("/mostrecent"), ListItem("Siste"), True)
  addDirectoryItem(plugin.handle, plugin.url_for("/categories"), ListItem("Kategorier"), True)
  addDirectoryItem(plugin.handle, plugin.url_for("/letters"), ListItem("A-Å"), True)
  endOfDirectory(plugin.handle)

@plugin.route('/live')
def live():
  img_path = os.path.join(ADDON_PATH, "resources/images")
  add_item("NRK 1", "mms://a1377.l11673952706.c116739.g.lm.akamaistream.net/D/1377/116739/v0001/reflector:52706",os.path.join(img_path, "nrk1.png"))
  add_item("NRK 2", "mms://a746.l11674151924.c116741.g.lm.akamaistream.net/D/746/116741/v0001/reflector:51924", os.path.join(img_path, "nrk2.png"))
  add_item("NRK 3", "mms://a1372.l11674333102.c116743.g.lm.akamaistream.net/D/1372/116743/v0001/reflector:33102", os.path.join(img_path, "nrk3.png"))
  endOfDirectory(plugin.handle)

def add_item(title, url, thumb=""):
  li =  ListItem(title, thumbnailImage=thumb)
  li.setProperty('mimetype', 'application/x-mpegURL')
  addDirectoryItem(plugin.handle, url, li, False)


def view(titles, urls, descr=repeat(''), thumbs=repeat(''), bgs=repeat('')):
  total = len(titles)
  for title, url, descr, thumb, bg in zip(titles, urls, descr, thumbs, bgs):
    descr = descr() if callable(descr) else descr
    thumb = thumb() if callable(thumb) else thumb
    bg = bg() if callable(bg) else bg
    li = ListItem(title, thumbnailImage=thumb)
    playable = plugin.route_for(url) == play
    li.setProperty('isplayable', str(playable))
    li.setProperty('fanart_image', bg)
    if playable:
      li.setInfo('video', {'plot':descr})
    addDirectoryItem(plugin.handle, plugin.url_for(url), li, not playable, total)
  endOfDirectory(plugin.handle)


@plugin.route('/recommended')
def recommended():
  titles, urls, bgs = data.parse_recommended()
  view(titles, urls, bgs=bgs)

@plugin.route('/mostrecent')
def mostrecent():
  titles, urls, thumbs = data.parse_most_recent()
  view(titles, urls, thumbs=thumbs)

@plugin.route('/categories')
def categories():
  titles, urls = data.parse_categories()
  view(titles, urls)

@plugin.route('/kategori/<arg>')
def category(arg):
  titles, urls = data.parse_by_category(arg)
  view(titles, urls)

@plugin.route('/letters')
def letters():
  common = ['0-9'] + map(chr, range(97, 123))
  titles = common + [ u'æ', u'ø', u'å' ]
  titles = [ e.upper() for e in titles ]
  urls = [ '/letters/%s' % l for l in (common + ['ae', 'oe', 'aa']) ]
  view(titles, urls)

@plugin.route('/letters/<arg>')
def letter(arg):
  titles, urls = data.parse_by_letter(arg)
  view(titles, urls)

@plugin.route('/serie/<arg>')
def seasons(arg):
  titles, urls = data.parse_seasons(arg)
  if len(titles) == 1:
    plugin.redirect(plugin.url_for(urls[0]))
    return
  view(titles, urls)

@plugin.route('/program/Episodes/<series_id>/<season_id>')
def episodes(series_id, season_id):
  titles, urls, descr = data.parse_episodes(series_id, season_id)
  view(titles, urls, descr=descr)

@plugin.route('/serie/<series_id>/<video_id>/.*')
@plugin.route('/program/<video_id>')
@plugin.route('/program/<video_id>/.*')
def play(video_id, series_id=""):
  url = data.parse_media_url(video_id, BITRATE)
  xbmcplugin.setResolvedUrl(plugin.handle, True, ListItem(path=url))
  player = xbmc.Player()
  subtitle = subs.get_subtitles(video_id)
  #Wait for stream to start
  start_time = time.time()
  while not player.isPlaying() and time.time() - start_time < 10:
    time.sleep(1.)
    player.setSubtitles(subtitle)
    if not SHOW_SUBS:
      player.showSubtitles(False)

if ( __name__ == "__main__" ):
  plugin.run()

