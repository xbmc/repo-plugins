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
        addDirectoryItem(plugin.handle, ch.media_url, li, False)

    url = "https://nrktegnsprak-lh.akamaihd.net/i/nrktegnsprak_0@111177/master.m3u8"
    li = ListItem("Tegnspråk")
    li.setArt({'thumb': "http://gfx.nrk.no/R4LFuTHBHWPMmv1dkqvPGQY4-ZZTKdNKAFPg_LHhoEFA"})
    li.setProperty('isplayable', 'true')
    addDirectoryItem(plugin.handle, url, li, False)

    add_radio_channels()
    endOfDirectory(plugin.handle)


def add_radio_channels():
    radio_channels = [
        ("NRK P1", "http://lyd.nrk.no/nrk_radio_p1_ostlandssendingen_mp3_h"),
        ("NRK P1+", "http://lyd.nrk.no/nrk_radio_p1pluss_mp3_h.m3u"),
        ("NRK P2", "http://lyd.nrk.no/nrk_radio_p2_mp3_h"),
        ("NRK P3", "http://lyd.nrk.no/nrk_radio_p3_mp3_h"),
        ("NRK P13", "http://lyd.nrk.no/nrk_radio_p13_mp3_h"),
        ("Alltid nyheter", "http://lyd.nrk.no/nrk_radio_alltid_nyheter_mp3_h"),
        ("Alltid RR", "http://lyd.nrk.no/nrk_radio_p3_radioresepsjonen_mp3_h"),
        ("Jazz", "http://lyd.nrk.no/nrk_radio_jazz_mp3_h"),
        ("Klassisk", "http://lyd.nrk.no/nrk_radio_klassisk_mp3_h"),
        ("Folkemusikk", "http://lyd.nrk.no/nrk_radio_folkemusikk_mp3_h"),
        ("mP3", "http://lyd.nrk.no/nrk_radio_mp3_mp3_h"),
        ("P3 Urørt", "http://lyd.nrk.no/nrk_radio_p3_urort_mp3_h"),
        ("Sport", "http://lyd.nrk.no/nrk_radio_sport_mp3_h"),
        ("Sápmi", "http://lyd.nrk.no/nrk_radio_sami_mp3_h"),
        ("Super", "http://lyd.nrk.no/nrk_radio_super_mp3_h"),
        ("P1 Buskerud", "http://lyd.nrk.no/nrk_radio_p1_buskerud_mp3_h"),
        ("P1 Finnmark", "http://lyd.nrk.no/nrk_radio_p1_finnmark_mp3_h"),
        ("P1 Hedemark og Oppland", "http://lyd.nrk.no/nrk_radio_p1_hedmark_og_oppland_mp3_h"),
        ("P1 Hordaland", "http://lyd.nrk.no/nrk_radio_p1_hordaland_mp3_h"),
        ("P1 Møre og Romsdal", "http://lyd.nrk.no/nrk_radio_p1_more_og_romsdal_mp3_h"),
        ("P1 Nordland", "http://lyd.nrk.no/nrk_radio_p1_nordland_mp3_h"),
        ("P1 Oslo og Akershus", "http://lyd.nrk.no/nrk_radio_p1_ostlandssendingen_mp3_h"),
        ("P1 Rogaland", "http://lyd.nrk.no/nrk_radio_p1_rogaland_mp3_h"),
        ("P1 Sogn og Fjordane", "http://lyd.nrk.no/nrk_radio_p1_sogn_og_fjordane_mp3_h"),
        ("P1 Sørlandet", "http://lyd.nrk.no/nrk_radio_p1_sorlandet_mp3_h"),
        ("P1 Telemark", "http://lyd.nrk.no/nrk_radio_p1_telemark_mp3_h"),
        ("P1 Troms", "http://lyd.nrk.no/nrk_radio_p1_troms_mp3_h"),
        ("P1 Trøndelag", "http://lyd.nrk.no/nrk_radio_p1_trondelag_mp3_h"),
        ("P1 Vestfold", "http://lyd.nrk.no/nrk_radio_p1_vestfold_mp3_h"),
        ("P1 Østfold", "http://lyd.nrk.no/nrk_radio_p1_ostfold_mp3_h"),
    ]
    for title, url in radio_channels:
        li = ListItem(title,)
        li.setProperty('mimetype', "audio/mpeg")
        li.setProperty('isplayable', 'true')
        addDirectoryItem(plugin.handle, url, li, False)


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


def show_episode_list(episodes):
    episodes = filter(lambda ep: getattr(ep, 'available', True), episodes)
    for i, item in enumerate(episodes):
        li = ListItem(item.episode)
        set_common_properties(item, li)
        set_steam_details(item, li)
        li.setInfo('video', {
            'title': item.episode,
            'count': i,
            'mediatype': 'episode',
            'tvshowtitle': item.title})

        url = plugin.url_for(play, item.id)
        addDirectoryItem(plugin.handle, url, li, False)
    endOfDirectory(plugin.handle)


def show_plug_list(items):
    items = filter(lambda ep: getattr(ep, 'available', True), items)
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
    view(items, urls=map(_to_series_or_program_url, items))


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
        items = nrktv.search(query.decode('utf-8'))
        view(items, urls=map(_to_series_or_program_url, items))


@plugin.route('/series/<series_id>')
def series_view(series_id):
    set_content_type_videos()
    programs = nrktv.episodes(series_id)
    show_episode_list(programs)


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
