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

from __future__ import unicode_literals

import traceback
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
from xbmcgui import ListItem
from requests import HTTPError
from lib import wimpy
from lib.wimpy.models import Album, Artist
from lib.wimpy import Quality
from routing import Plugin

addon = xbmcaddon.Addon()
plugin = Plugin()
plugin.name = addon.getAddonInfo('name')

_addon_id = addon.getAddonInfo('id')

config = wimpy.Config(
    api=wimpy.TIDAL_API if addon.getSetting('site') == '1' else wimpy.WIMP_API,
    quality=[Quality.lossless, Quality.high, Quality.low][int('0' + addon.getSetting('quality'))])

wimp = wimpy.Session(config=config)

is_logged_in = False
_session_id = addon.getSetting('session_id')
_country_code = addon.getSetting('country_code')
_user_id = addon.getSetting('user_id')
if _session_id and _country_code and _user_id:
    wimp.load_session(session_id=_session_id, country_code=_country_code, user_id=_user_id)
    is_logged_in = True


def log(msg):
    xbmc.log(("[%s] %s" % (_addon_id, msg)).encode('utf-8'), level=xbmc.LOGDEBUG)


def view(data_items, urls, end=True):
    list_items = []
    for item, url in zip(data_items, urls):
        li = ListItem(item.name)
        info = {'title': item.name}
        if isinstance(item, Album):
            info.update({'album': item.name, 'artist': item.artist.name})
        elif isinstance(item, Artist):
            info.update({'artist': item.name})
        li.setInfo('music', info)
        if getattr(item, 'image', None):
            li.setThumbnailImage(item.image)
        list_items.append((url, li, True))
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    if end:
        xbmcplugin.endOfDirectory(plugin.handle)


def track_list(tracks):
    xbmcplugin.setContent(plugin.handle, 'songs')
    list_items = []
    for track in tracks:
        if not track.available:
            continue
        url = plugin.url_for(play, track_id=track.id)
        li = ListItem(track.name)
        li.setProperty('isplayable', 'true')
        li.setInfo('music', {
            'title': track.name,
            'tracknumber': track.track_num,
            'discnumber': track.disc_num,
            'artist': track.artist.name,
            'album': track.album.name})
        if track.album:
            li.setThumbnailImage(track.album.image)
        radio_url = plugin.url_for(track_radio, track_id=track.id)
        li.addContextMenuItems(
            [('Track Radio', 'XBMC.Container.Update(%s)' % radio_url,)])
        list_items.append((url, li, False))
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.endOfDirectory(plugin.handle)


def add_directory(title, endpoint,):
    if callable(endpoint):
        endpoint = plugin.url_for(endpoint)
    xbmcplugin.addDirectoryItem(plugin.handle, endpoint, ListItem(title), True)


def urls_from_id(view_func, items):
    return [plugin.url_for(view_func, item.id) for item in items]


@plugin.route('/')
def root():
    if is_logged_in:
        add_directory('My Music', my_music)
        add_directory('Featured Playlists', featured_playlists)
        add_directory("What's New", whats_new)
        add_directory('Genres', genres)
        add_directory('Moods', moods)
        add_directory('Search', search)
        add_directory('Logout', logout)
    else:
        add_directory('Login', login)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/track_radio/<track_id>')
def track_radio(track_id):
    track_list(wimp.get_track_radio(track_id))


@plugin.route('/moods')
def moods():
    items = wimp.get_moods()
    view(items, urls_from_id(moods_playlists, items))


@plugin.route('/moods/<mood>')
def moods_playlists(mood):
    items = wimp.get_mood_playlists(mood)
    view(items, urls_from_id(playlist_view, items))


@plugin.route('/genres')
def genres():
    items = wimp.get_genres()
    view(items, urls_from_id(genre_view, items))


@plugin.route('/genre/<genre_id>')
def genre_view(genre_id):
    add_directory('Playlists', plugin.url_for(genre_playlists, genre_id=genre_id))
    add_directory('Albums', plugin.url_for(genre_albums, genre_id=genre_id))
    add_directory('Tracks', plugin.url_for(genre_tracks, genre_id=genre_id))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/genre/<genre_id>/playlists')
def genre_playlists(genre_id):
    items = wimp.get_genre_items(genre_id, 'playlists')
    view(items, urls_from_id(playlist_view, items))


@plugin.route('/genre/<genre_id>/albums')
def genre_albums(genre_id):
    items = wimp.get_genre_items(genre_id, 'albums')
    view(items, urls_from_id(album_view, items))


@plugin.route('/genre/<genre_id>/tracks')
def genre_tracks(genre_id):
    items = wimp.get_genre_items(genre_id, 'tracks')
    track_list(items)


@plugin.route('/featured_playlists')
def featured_playlists():
    items = wimp.get_featured()
    view(items, urls_from_id(playlist_view, items))


@plugin.route('/whats_new')
def whats_new():
    add_directory('Recommended Playlists', plugin.url_for(featured, group='recommended', content_type='playlists'))
    add_directory('Recommended Albums', plugin.url_for(featured, group='recommended', content_type='albums'))
    add_directory('Recommended Tracks', plugin.url_for(featured, group='recommended', content_type='tracks'))
    add_directory('New Playlists', plugin.url_for(featured, group='new', content_type='playlists'))
    add_directory('New Albums', plugin.url_for(featured, group='new', content_type='albums'))
    add_directory('New Tracks', plugin.url_for(featured, group='new', content_type='tracks'))
    add_directory('Top Albums', plugin.url_for(featured, group='top', content_type='albums'))
    add_directory('Top Tracks', plugin.url_for(featured, group='top', content_type='tracks'))
    if config.api is wimpy.WIMP_API:
        add_directory('Local Playlists', plugin.url_for(featured, group='local', content_type='playlists'))
        add_directory('Local Albums', plugin.url_for(featured, group='local', content_type='albums'))
        add_directory('Local Tracks', plugin.url_for(featured, group='local', content_type='tracks'))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/featured/<group>/<content_type>')
def featured(group=None, content_type=None):
    items = wimp.get_featured_items(content_type, group)
    if content_type == 'tracks':
        track_list(items)
    elif content_type == 'albums':
        view(items, urls_from_id(album_view, items))
    elif content_type == 'playlists':
        view(items, urls_from_id(playlist_view, items))


@plugin.route('/my_music')
def my_music():
    add_directory('My Playlists', my_playlists)
    add_directory('Favourite Playlists', favourite_playlists)
    add_directory('Favourite Artists', favourite_artists)
    add_directory('Favourite Albums', favourite_albums)
    add_directory('Favourite Tracks', favourite_tracks)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/album/<album_id>')
def album_view(album_id):
    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_TRACKNUM)
    track_list(wimp.get_album_tracks(album_id))


@plugin.route('/artist/<artist_id>')
def artist_view(artist_id):
    xbmcplugin.setContent(plugin.handle, 'albums')
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(top_tracks, artist_id),
        ListItem('Top Tracks'), True
    )
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(artist_radio, artist_id),
        ListItem('Artist Radio'), True
    )
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(similar_artists, artist_id),
        ListItem('Similar Artists'), True
    )
    albums = wimp.get_artist_albums(artist_id) + \
             wimp.get_artist_albums_ep_singles(artist_id) + \
             wimp.get_artist_albums_other(artist_id)
    view(albums, urls_from_id(album_view, albums))


@plugin.route('/artist/<artist_id>/radio')
def artist_radio(artist_id):
    track_list(wimp.get_artist_radio(artist_id))


@plugin.route('/artist/<artist_id>/top')
def top_tracks(artist_id):
    track_list(wimp.get_artist_top_tracks(artist_id))


@plugin.route('/artist/<artist_id>/similar')
def similar_artists(artist_id):
    xbmcplugin.setContent(plugin.handle, 'artists')
    artists = wimp.get_artist_similar(artist_id)
    view(artists, urls_from_id(artist_view, artists))


@plugin.route('/playlist/<playlist_id>')
def playlist_view(playlist_id):
    track_list(wimp.get_playlist_tracks(playlist_id))


@plugin.route('/user_playlists')
def my_playlists():
    items = wimp.user.playlists()
    view(items, urls_from_id(playlist_view, items))


@plugin.route('/favourite_playlists')
def favourite_playlists():
    items = wimp.user.favorites.playlists()
    view(items, urls_from_id(playlist_view, items))


@plugin.route('/favourite_artists')
def favourite_artists():
    xbmcplugin.setContent(plugin.handle, 'artists')
    items = wimp.user.favorites.artists()
    view(items, urls_from_id(artist_view, items))


@plugin.route('/favourite_albums')
def favourite_albums():
    xbmcplugin.setContent(plugin.handle, 'albums')
    items = wimp.user.favorites.albums()
    view(items, urls_from_id(album_view, items))


@plugin.route('/favourite_tracks')
def favourite_tracks():
    track_list(wimp.user.favorites.tracks())


@plugin.route('/search')
def search():
    add_directory('Artist', plugin.url_for(search_type, field='artist'))
    add_directory('Album', plugin.url_for(search_type, field='album'))
    add_directory('Playlist', plugin.url_for(search_type, field='playlist'))
    add_directory('Track', plugin.url_for(search_type, field='track'))
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/search_type/<field>')
def search_type(field):
    keyboard = xbmc.Keyboard('', 'Search')
    keyboard.doModal()
    if keyboard.isConfirmed():
        keyboardinput = keyboard.getText()
        if keyboardinput:
            searchresults = wimp.search(field, keyboardinput)
            view(searchresults.artists, urls_from_id(artist_view, searchresults.artists), end=False)
            view(searchresults.albums, urls_from_id(album_view, searchresults.albums), end=False)
            view(searchresults.playlists, urls_from_id(playlist_view, searchresults.playlists), end=False)
            track_list(searchresults.tracks)


@plugin.route('/login')
def login():
    username = addon.getSetting('username')
    password = addon.getSetting('password')

    if not username or not password:
        # Ask for username/password
        dialog = xbmcgui.Dialog()
        username = dialog.input('Username')
        if not username:
            return
        password = dialog.input('Password', option=xbmcgui.ALPHANUM_HIDE_INPUT)
        if not password:
            return

    if wimp.login(username, password):
        addon.setSetting('session_id', wimp.session_id)
        addon.setSetting('country_code', wimp.country_code)
        addon.setSetting('user_id', unicode(wimp.user.id))

        if not addon.getSetting('username') or not addon.getSetting('password'):
            # Ask about remembering username/password
            dialog = xbmcgui.Dialog()
            if dialog.yesno(plugin.name, 'Remember login details?'):
                addon.setSetting('username', username)
                addon.setSetting('password', password)

@plugin.route('/logout')
def logout():
    addon.setSetting('session_id', '')
    addon.setSetting('country_code', '')
    addon.setSetting('user_id', '')


@plugin.route('/play/<track_id>')
def play(track_id):
    media_url = wimp.get_media_url(track_id)
    if not media_url.startswith('http://') and not media_url.startswith('https://'):
        log("media url: %s" % media_url)
        host, tail = media_url.split('/', 1)
        app, playpath = tail.split('/mp4:', 1)
        media_url = 'rtmp://%s app=%s playpath=mp4:%s' % (host, app, playpath)
    li = ListItem(path=media_url)
    mimetype = 'audio/flac' if config.quality == Quality.lossless else 'audio/mpeg'
    li.setProperty('mimetype', mimetype)
    xbmcplugin.setResolvedUrl(plugin.handle, True, li)


if __name__ == '__main__':
    try:
        plugin.run()
    except HTTPError as e:
        if e.response.status_code in [401, 403]:
            dialog = xbmcgui.Dialog()
            dialog.notification(plugin.name, "Authorization problem", xbmcgui.NOTIFICATION_ERROR)
        traceback.print_exc()
