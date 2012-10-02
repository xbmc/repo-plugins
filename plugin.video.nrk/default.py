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
  b = ['380','659','1394','2410','3660'][BITRATE-1]
  img_path = os.path.join(ADDON_PATH, "resources/images")
  add("NRK 1", "http://nrk1us-f.akamaihd.net/i/nrk1us_0@79328/index_%s_av-p.m3u8?sd=10&rebase=on" % b,os.path.join(img_path, "nrk1.png"))
  add("NRK 2", "http://nrk2us-f.akamaihd.net/i/nrk2us_0@79327/index_%s_av-p.m3u8?sd=10&rebase=on" % b, os.path.join(img_path, "nrk2.png"))
  add("NRK 3", "http://nrk3us-f.akamaihd.net/i/nrk3us_0@79326/index_%s_av-p.m3u8?sd=10&rebase=on" % b, os.path.join(img_path, "nrk3.png"))
  endOfDirectory(plugin.handle)

def add(title, url, thumb=""):
  li =  ListItem(title, thumbnailImage=thumb)
  li.setProperty('mimetype', 'application/vnd.apple.mpegurl')
  addDirectoryItem(plugin.handle, url, li, False)


def view(titles, urls, thumbs=repeat(''), bgs=repeat(''), descr=repeat('')):
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
  import data
  view(*data.parse_recommended())

@plugin.route('/mostrecent')
def mostrecent():
  import data
  view(*data.parse_most_recent())

@plugin.route('/categories')
def categories():
  import data
  view(*data.parse_categories())

@plugin.route('/kategori/<arg>')
def category(arg):
  import data
  view(*data.parse_by_category(arg))

@plugin.route('/letters')
def letters():
  import data
  common = ['0-9'] + map(chr, range(97, 123))
  titles = common + [ u'æ', u'ø', u'å' ]
  titles = [ e.upper() for e in titles ]
  urls = [ '/letters/%s' % l for l in (common + ['ae', 'oe', 'aa']) ]
  view(titles, urls)

@plugin.route('/letters/<arg>')
def letter(arg):
  import data
  view(*data.parse_by_letter(arg))

@plugin.route('/serie/<arg>')
def seasons(arg):
  import data
  titles, urls, thumbs, bgs = data.parse_seasons(arg)
  if len(titles) == 1:
    plugin.redirect(plugin.url_for(urls[0]))
    return
  view(titles, urls, thumbs=thumbs, bgs=bgs)

@plugin.route('/program/Episodes/<series_id>/<season_id>')
def episodes(series_id, season_id):
  import data
  view(*data.parse_episodes(series_id, season_id))

@plugin.route('/serie/<series_id>/<video_id>/.*')
@plugin.route('/program/<video_id>')
@plugin.route('/program/<video_id>/.*')
def play(video_id, series_id=""):
  import data
  url = data.parse_media_url(video_id, BITRATE)
  xbmcplugin.setResolvedUrl(plugin.handle, True, ListItem(path=url))
  player = xbmc.Player()
  subtitle = data.get_subtitles(video_id)
  if subtitle:
    #Wait for stream to start
    start_time = time.time()
    while not player.isPlaying() and time.time() - start_time < 10:
      time.sleep(1.)
    player.setSubtitles(subtitle)
    if not SHOW_SUBS:
      player.showSubtitles(False)

if ( __name__ == "__main__" ):
  plugin.run()

