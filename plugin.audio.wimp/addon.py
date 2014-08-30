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

import xbmc, xbmcgui, xbmcaddon, xbmcplugin
from xbmcgui import ListItem
from lib import wimpy
from lib.wimpy.models import Album, Artist
from routing import Plugin

plugin = Plugin()
addon = xbmcaddon.Addon()
wimp = wimpy.Session(
    session_id=addon.getSetting('session_id'),
    country_code=addon.getSetting('country_code'),
    user_id=addon.getSetting('user_id')
)


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
        list_items.append((url, li, False))
    xbmcplugin.addDirectoryItems(plugin.handle, list_items)
    xbmcplugin.endOfDirectory(plugin.handle)


def add_directory(title, view_func):
    xbmcplugin.addDirectoryItem(
        plugin.handle, plugin.url_for(view_func), ListItem(title), True)


def urls_from_id(view_func, items):
    return [plugin.url_for(view_func, item.id) for item in items]


@plugin.route('/')
def root():
    add_directory('My music', my_music)
    add_directory('Search', search)
    add_directory('Login', login)
    add_directory('Logout', logout)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/my_music')
def my_music():
    add_directory('My Playlists', my_playlists)
    add_directory('Favourite Playlists', favourite_playlists)
    add_directory('Favourite Artists', favourite_artists)
    add_directory('Favourite Albums', favourite_albums)
    add_directory('Favourite Tracks', favourite_tracks)
    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/not_implemented')
def not_implemented():
    raise NotImplementedError()


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
    dialog = xbmcgui.Dialog()
    fields = ['artist', 'album', 'playlist', 'track']
    names = ['Artists', 'Albums', 'Playlists', 'Tracks']
    idx = dialog.select('Search for', names)
    if idx != -1:
        field = fields[idx]
        query = dialog.input('Search')
        if query:
            res = wimp.search(field, query)
            view(res.artists, urls_from_id(artist_view, res.artists), end=False)
            view(res.albums, urls_from_id(album_view, res.albums), end=False)
            view(res.playlists, urls_from_id(playlist_view, res.playlists), end=False)
            track_list(res.tracks)


@plugin.route('/login')
def login():
    dialog = xbmcgui.Dialog()
    username = dialog.input('Username')
    if username:
        password = dialog.input('Password')
        if password:
            if wimp.login(username, password):
                addon.setSetting('session_id', wimp.session_id)
                addon.setSetting('country_code', wimp.country_code)
                addon.setSetting('user_id', unicode(wimp.user.id))
                return
    raise Exception('failed to login')


@plugin.route('/logout')
def logout():
    addon.setSetting('session_id', '')
    addon.setSetting('country_code', '')
    addon.setSetting('user_id', '')


@plugin.route('/play/<track_id>')
def play(track_id):
    media_url = wimp.get_media_url(track_id)
    host, app, playpath = media_url.split('/', 3)
    rtmp_url = 'rtmp://%s app=%s playpath=%s' % (host, app, playpath)
    li = ListItem(path=rtmp_url)
    xbmcplugin.setResolvedUrl(plugin.handle, True, li)


if __name__ == '__main__':
    plugin.run()
