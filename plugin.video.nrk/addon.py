# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2015 Thomas Amland
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
from xbmcplugin import setResolvedUrl
from xbmcgui import ListItem
import routing
import nrktv
import subs

plugin = routing.Plugin()


@plugin.route('/')
def root():
    items = [
        (plugin.url_for(live), ListItem("Direkte"), True),
        (plugin.url_for(recommended), ListItem("Anbefalt"), True),
        (plugin.url_for(popular), ListItem("Mest sett"), True),
        (plugin.url_for(mostrecent), ListItem("Sist sendt"), True),
        (plugin.url_for(browse), ListItem("Kategorier"), True),
        (plugin.url_for(search), ListItem("Søk"), True),
    ]
    addDirectoryItems(plugin.handle, items)
    endOfDirectory(plugin.handle)


@plugin.route('/live')
def live():
    for ch in nrktv.channels():
        li = ListItem(ch.title)
        li.setProperty('mimetype', "application/vnd.apple.mpegurl")
        li.setProperty('isplayable', 'true')
        li.setArt({'thumb': ch.thumb, 'fanart': ch.fanart})
        li.setInfo('video', {'title': ch.title})
        li.addStreamInfo('video', {'codec': 'h264', 'width': 1280, 'height': 720})
        li.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
        addDirectoryItem(plugin.handle,
                         plugin.url_for(live_resolve, ch.manifest.split('/')[-1]), li, False)

    for rd in nrktv.radios():
        li = ListItem(rd.title)
        li.setProperty('mimetype', "audio/mpeg")
        li.setProperty('isplayable', 'true')
        li.setArt({'thumb': rd.thumb, 'fanart': rd.fanart})
        li.setInfo('video', {'title': ch.title})
        li.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})
        addDirectoryItem(plugin.handle,
                         plugin.url_for(live_resolve, rd.manifest.split('/')[-1]), li, False)

    endOfDirectory(plugin.handle)

@plugin.route('/live_resolve/<id>')
def live_resolve(id):
    success = False
    media_url = nrktv.get_playback_url("/playback/manifest/channel/%s" % id);
    if (media_url):
        success = True
    li = ListItem(path=media_url)
    setResolvedUrl(plugin.handle, success, li)


def set_steam_details(item, li):
    li.setProperty('isplayable', 'true')
    li.addStreamInfo('video', {'codec': 'h264', 'width': 1280, 'height': 720, 'duration': item.duration})
    li.addStreamInfo('audio', {'codec': 'aac', 'channels': 2})


def set_common_properties(item, li):
    li.setArt({
        'thumb': getattr(item, 'thumb', ''),
        'fanart': getattr(item, 'fanart', ''),
    })
    info = {}
    if hasattr(item, 'description'):
        info['plot'] = item.description
    if hasattr(item, 'category') and item.category:
        info['genre'] = item.category.title
    if hasattr(item, 'legal_age'):
        info['mpaa'] = item.legal_age
    if hasattr(item, 'aired'):
        info['aired'] = item.aired.strftime('%Y-%m-%d')
    li.setInfo('video', info)


def view(items, update_listing=False, urls=None):
    total = len(items)
    for i, (item, url) in enumerate(zip(items, urls)):
        if not getattr(item, 'available', True):
            continue
        li = ListItem(item.title)
        set_common_properties(item, li)
        playable = plugin.route_for(url) == play
        if playable:
            set_steam_details(item, li)
        li.setInfo('video', {'count': i, 'title': item.title, 'mediatype': 'video'})
        addDirectoryItem(plugin.handle, url, li, not playable, total)
    endOfDirectory(plugin.handle, updateListing=update_listing)


def show_season_list(series_id, seasons):
    for item in seasons:
        li = ListItem(item.title)
        url = plugin.url_for(episodes_view, series_id, item.id)
        addDirectoryItem(plugin.handle, url, li, True)
    endOfDirectory(plugin.handle)

def show_episode_list(episodes):
    episodes = [ep for ep in episodes if getattr(ep, 'available', True)]
    for i, item in enumerate(episodes):
        li = ListItem("%s - %s" % (item.episode, item.title))
        set_common_properties(item, li)
        set_steam_details(item, li)
        li.setInfo('video', {
            'title': item.title,
            'count': i,
            'mediatype': 'episode',
            'tvshowtitle': item.title})

        url = plugin.url_for(play, item.id)
        addDirectoryItem(plugin.handle, url, li, False)
    endOfDirectory(plugin.handle)


def show_plug_list(items):
    items = [ep for ep in items if getattr(ep, 'available', True)]
    for i, item in enumerate(items):
        title = item.title
        if item.episode:
            title += " (%s)" % item.episode
        li = ListItem(title)
        set_common_properties(item, li)
        set_steam_details(item, li)
        li.setInfo('video', {
            'title': title,
            'count': i,
            'mediatype': 'video'})

        if getattr(item, 'series_id', None):
            action = "container.update(\"%s\")" % plugin.url_for(series_view, item.series_id)
            li.addContextMenuItems([("Gå til serie", action)])

        url = plugin.url_for(play, item.id)
        addDirectoryItem(plugin.handle, url, li, False)
    endOfDirectory(plugin.handle)


def set_content_type_videos():
    t = 'videos' if tuple(map(int, xbmc.__version__.split('.'))) >= (2, 25, 0) else 'episodes'
    xbmcplugin.setContent(plugin.handle, t)


@plugin.route('/recommended')
def recommended():
    set_content_type_videos()
    programs = nrktv.recommended_programs()
    show_plug_list(programs)


@plugin.route('/mostrecent')
def mostrecent():
    set_content_type_videos()
    programs = nrktv.recent_programs()
    show_plug_list(programs)


@plugin.route('/popular')
def popular():
    set_content_type_videos()
    programs = nrktv.popular_programs()
    show_plug_list(programs)


def _to_series_or_program_url(item):
    return plugin.url_for((series_view if item.is_series else play), item.id)


@plugin.route('/category/<category_id>')
def category(category_id):
    set_content_type_videos()
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_PLAYLIST_ORDER)
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    items = nrktv.programs(category_id)
    view(items, urls=list(map(_to_series_or_program_url, items)))


@plugin.route('/browse')
def browse():
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
    items = nrktv.categories()
    urls = [plugin.url_for(category, item.id) for item in items]
    view(items, urls=urls)


@plugin.route('/search')
def search():
    keyboard = xbmc.Keyboard()
    keyboard.setHeading("Søk")
    keyboard.doModal()
    query = keyboard.getText()
    if query:
        items = nrktv.search(query)
        view(items, urls=list(map(_to_series_or_program_url, items)))


@plugin.route('/series/<series_id>')
def series_view(series_id):
    seasons = nrktv.seasons(series_id)
    show_season_list(series_id, seasons)

@plugin.route('/episodes/<series_id>/<season_id>')
def episodes_view(series_id, season_id):
    # set_content_type_videos()
    episodes = nrktv.episodes(series_id, season_id)
    show_episode_list(episodes)


@plugin.route('/play/<video_id>')
def play(video_id):
    urls = nrktv.program(video_id).media_urls
    if not urls:
        raise Exception("could not find any streams")
    url = urls[0] if len(urls) == 1 else "stack://" + ' , '.join(urls)

    xbmcplugin.setResolvedUrl(plugin.handle, True, ListItem(path=url))
    player = xbmc.Player()
    subtitle = subs.get_subtitles(video_id)
    if subtitle:
        # Wait for stream to start
        start_time = time.time()
        while not player.isPlaying() and time.time() - start_time < 10:
            time.sleep(1.)
        player.setSubtitles(subtitle)
        if xbmcaddon.Addon().getSetting('showsubtitles') != '1':
            player.showSubtitles(False)


@plugin.route('/play')
def play_url():
    url = plugin.args['url'][0]
    xbmcplugin.setResolvedUrl(plugin.handle, True, ListItem(path=url))


def run():
    plugin.run()
