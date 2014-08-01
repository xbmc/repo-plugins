# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Thomas Amland
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

import os
import time
import xbmc
import xbmcplugin
import xbmcaddon
from itertools import repeat
from urllib import quote, unquote
from collections import namedtuple
from xbmcplugin import addDirectoryItem
from xbmcplugin import endOfDirectory
from xbmcgui import ListItem, Dialog
import routing
plugin = routing.Plugin()

SHOW_SUBS = int(xbmcaddon.Addon().getSetting('showsubtitles')) == 1

Node = namedtuple('Node', ['title', 'url'])


@plugin.route('/')
def view_top():
    addDirectoryItem(plugin.handle, plugin.url_for(live), ListItem("Direkte"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(recommended), ListItem("Aktuelt"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(mostrecent), ListItem("Nytt"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(mostpopularweek), ListItem("Populært siste uke"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(mostpopularmonth), ListItem("Populært siste måned"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(browse), ListItem("Bla"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(search), ListItem("Søk"), True)
    endOfDirectory(plugin.handle)


@plugin.route('/live')
def live():
    import nrktv
    res = os.path.join(plugin.path, "resources/images")
    for ch in [1, 2, 3]:
        url, fanart = nrktv.get_live_stream(ch)
        url = plugin.url_for(play_url, url=url)
        add("NRK %s" % ch, url, "application/vnd.apple.mpegurl", os.path.join(res, "nrk%d.png" % ch), fanart)
    add("NRK P1", "http://lyd.nrk.no/nrk_radio_p1_ostlandssendingen_mp3_h", "audio/mpeg")
    add("NRK P2", "http://lyd.nrk.no/nrk_radio_p2_mp3_h", "audio/mpeg")
    add("NRK P3", "http://lyd.nrk.no/nrk_radio_p3_mp3_h", "audio/mpeg")
    add("Alltid nyheter", "http://lyd.nrk.no/nrk_radio_alltid_nyheter_mp3_h", "audio/mpeg")
    add("Alltid RR", "http://lyd.nrk.no/nrk_radio_p3_radioresepsjonen_mp3_h", "audio/mpeg")
    add("Jazz", "http://lyd.nrk.no/nrk_radio_jazz_mp3_h", "audio/mpeg")
    add("Klassisk", "http://lyd.nrk.no/nrk_radio_klassisk_mp3_h", "audio/mpeg")
    add("Folkemusikk", "http://lyd.nrk.no/nrk_radio_folkemusikk_mp3_h", "audio/mpeg")
    add("Gull", "http://lyd.nrk.no/nrk_radio_gull_mp3_h", "audio/mpeg")
    add("mP3", "http://lyd.nrk.no/nrk_radio_mp3_mp3_h", "audio/mpeg")
    add("P3 Urørt", "http://lyd.nrk.no/nrk_radio_p3_urort_mp3_h", "audio/mpeg")
    add("Sport", "http://lyd.nrk.no/nrk_radio_sport_mp3_h", "audio/mpeg")
    add("Sápmi", "http://lyd.nrk.no/nrk_radio_sami_mp3_h", "audio/mpeg")
    add("Super", "http://lyd.nrk.no/nrk_radio_super_mp3_h", "audio/mpeg")
    endOfDirectory(plugin.handle)


def add(title, url, mimetype, thumb="", fanart=""):
    li = ListItem(title, thumbnailImage=thumb)
    li.setProperty('mimetype', mimetype)
    li.setProperty('fanart_image', fanart)
    li.setProperty('isplayable', 'true')
    addDirectoryItem(plugin.handle, url, li, False)


def view(items, update_listing=False):
    total = len(items)
    for item in items:
        li = ListItem(item.title, thumbnailImage=getattr(item, 'thumb', ''))
        playable = plugin.route_for(item.url) == play
        li.setProperty('isplayable', str(playable))
        if hasattr(item, 'fanart'):
            li.setProperty('fanart_image', item.fanart)
        if playable:
            li.setInfo('video', {'title': item.title, 'plot': getattr(item, 'description', '')})
            li.addStreamInfo('video', {'codec': 'h264', 'width': 1280, 'height': 720})
            li.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
        addDirectoryItem(plugin.handle, plugin.url_for_path(item.url), li, not playable, total)
    endOfDirectory(plugin.handle, updateListing=update_listing)


@plugin.route('/recommended')
def recommended():
    import nrktv
    view(nrktv.get_recommended())


@plugin.route('/mostrecent')
def mostrecent():
    import nrktv
    view(nrktv.get_most_recent())


@plugin.route('/mostpopularweek')
def mostpopularweek():
    import nrktv
    view(nrktv.get_most_popular_week())


@plugin.route('/mostpopularmonth')
def mostpopularmonth():
    import nrktv
    view(nrktv.get_most_popular_month())


@plugin.route('/category/<id>')
def category1(id):
    view_letter_list("/category/%s" % id)


@plugin.route('/category/<id>/<letter>')
def category2(id, letter):
    import nrktv
    view(nrktv.get_by_category(id, letter))


@plugin.route('/letters')
def letters():
    view_letter_list('/letter')


@plugin.route('/letter/<arg>')
def letter(arg):
    import nrktv
    view(nrktv.get_by_letter(arg))


@plugin.route('/browse')
def browse():
    import nrktv
    titles, ids = nrktv.get_categories()
    titles = ["Alle"] + titles
    urls = ["/letters"] + ["/category/%s" % i for i in ids]
    view([Node(title, url) for title, url in zip(titles, urls)])


def view_letter_list(base_url):
    common = ['0-9'] + map(chr, range(97, 123))
    titles = common + [u'æ', u'ø', u'å']
    titles = [e.upper() for e in titles]
    urls = ["%s/%s" % (base_url, l) for l in (common + ['ae', 'oe', 'aa'])]
    view([Node(title, url) for title, url in zip(titles, urls)])


@plugin.route('/search')
def search():
    keyboard = xbmc.Keyboard(heading="Søk")
    keyboard.doModal()
    query = keyboard.getText()
    if query:
        plugin.redirect('/search/%s/0' % quote(query))


@plugin.route('/search/<query>/<page>')
def search_results(query, page):
    import nrktv
    results = nrktv.get_search_results(query, page)
    more_node = Node("Flere", '/search/%s/%s' % (query, int(page) + 1))
    view(results + [more_node], update_listing=int(page) > 1)


@plugin.route('/serie/<arg>')
def seasons(arg):
    import nrktv
    items = nrktv.get_seasons(arg)
    if len(items) == 1:
        return plugin.redirect(items[0].url)
    view(items)


@plugin.route('/program/Episodes/<series_id>/<path:season_id>')
def episodes(series_id, season_id):
    import nrktv
    view(nrktv.get_episodes(series_id, season_id))


@plugin.route('/serie/<series_id>/<video_id>')
@plugin.route('/serie/<series_id>/<video_id>/.*')
@plugin.route('/program/<video_id>')
@plugin.route('/program/<video_id>/.*')
def play(video_id, series_id=""):
    import nrktv
    import subs
    url = nrktv.get_media_url(video_id)
    xbmcplugin.setResolvedUrl(plugin.handle, True, ListItem(path=url))
    player = xbmc.Player()
    subtitle = subs.get_subtitles(video_id)
    if subtitle:
        # Wait for stream to start
        start_time = time.time()
        while not player.isPlaying() and time.time() - start_time < 10:
            time.sleep(1.)
        player.setSubtitles(subtitle)
        if not SHOW_SUBS:
            player.showSubtitles(False)


@plugin.route('/play')
def play_url():
    url = plugin.args['url'][0]

    if url.startswith('https://') and (
            xbmc.getCondVisibility('system.platform.android') or
            xbmc.getCondVisibility('system.platform.ios')):
        dialog = Dialog()
        dialog.ok("NRK Nett-TV", "Direktestrømmer er ikke støttet på iOS/Android")

    xbmcplugin.setResolvedUrl(plugin.handle, True, ListItem(path=url))


if __name__ == '__main__':
    plugin.run()
