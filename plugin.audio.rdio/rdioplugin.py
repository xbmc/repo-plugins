# Copyright 2012 Charles Blaxland
# This file is part of rdio-xbmc.
#
# rdio-xbmc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rdio-xbmc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rdio-xbmc.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import traceback
import inspect
import time
import urllib
import sqlite3
import xbmcplugin
import xbmcgui
from t0mm0.common.addon import Addon
import rdiocommon

from rdioradio import RdioRadio


ADDON_ID = 'plugin.audio.rdio'
addon = Addon(ADDON_ID, argv=sys.argv)
sys.path.append(os.path.join(addon.get_path(), 'resources', 'lib'))

from rdioxbmc import RdioApi, RdioAuthenticationException


class XbmcRdioOperation:
  _TYPE_ALBUM = 'a'
  _TYPE_ARTIST = 'r'
  _TYPE_PLAYLIST = 'p'
  _TYPE_USER = 's'
  _TYPE_TRACK = 't'
  _TYPE_ALBUM_IN_COLLECTION = 'al'
  _TYPE_ARTIST_IN_COLLECTION = 'rl'

  _PAGE_SIZE_ALBUMS = 100
  _PAGE_SIZE_HEAVY_ROTATION = 14

  def __init__(self, addon):
    self._addon = addon
    self._rdio_api = RdioApi(self._addon)

  def main(self):

    # TODO should get rid of the recursive references to 'mode=main' here as they mess up the ".." nav
    if self._mandatory_settings_are_valid():
      if not self._rdio_api.authenticated():
        try:
          self._rdio_api.authenticate()
        except RdioAuthenticationException, rae:
          self._addon.show_error_dialog([self._addon.get_string(30903), str(rae)])
          self._addon.add_directory({'mode': 'main'}, {'title': self._addon.get_string(30206).encode('UTF-8')})

      if self._rdio_api.authenticated():
        self._addon.add_directory({'mode': 'albums_in_collection'}, {'title': self._addon.get_string(30204).encode('UTF-8')})
        self._addon.add_directory({'mode': 'artists_in_collection'}, {'title': self._addon.get_string(30203).encode('UTF-8')})
        self._addon.add_directory({'mode': 'playlists'}, {'title': self._addon.get_string(30200).encode('UTF-8')})
        self._addon.add_directory({'mode': 'new_releases'}, {'title': self._addon.get_string(30215).encode('UTF-8')})
        self._addon.add_directory({'mode': 'heavy_rotation'}, {'title': self._addon.get_string(30216).encode('UTF-8')})
        self._addon.add_directory({'mode': 'top_charts'}, {'title': self._addon.get_string(30223).encode('UTF-8')})
        self._addon.add_directory({'mode': 'following'}, {'title': self._addon.get_string(30208).encode('UTF-8')})
        self._addon.add_directory({'mode': 'search_artist_album'}, {'title': self._addon.get_string(30209).encode('UTF-8')})
        self._addon.add_directory({'mode': 'search_playlist'}, {'title': self._addon.get_string(30218).encode('UTF-8')})
        self._addon.add_directory({'mode': 'reauthenticate'}, {'title': self._addon.get_string(30207).encode('UTF-8')})
    else:
      self._addon.show_ok_dialog([self._addon.get_string(30900).encode('UTF-8'), self._addon.get_string(30901).encode('UTF-8'), self._addon.get_string(30902).encode('UTF-8')])
      self._addon.add_directory({'mode': 'main'}, {'title': self._addon.get_string(30206).encode('UTF-8')})

    self._addon.add_directory({'mode': 'settings'}, {'title': self._addon.get_string(30205).encode('UTF-8')})
    self._addon.end_of_directory()


  def search_artist_album(self):
    self._search('Artist,Album')

  def search_playlist(self):
    self._search('Playlist')

  def _search(self, types_to_search):
    kb = xbmc.Keyboard(heading = self._addon.get_string(30210))
    kb.doModal()
    if kb.isConfirmed():
      query = kb.getText()
      if query:
        search_results = self._rdio_api.call('search', query = query, types = types_to_search, extras = 'playCount,bigIcon')
        for result in search_results['results']:
          if result['type'] == self._TYPE_ARTIST:
            self._add_artist(result)
          elif result['type'] == self._TYPE_ALBUM:
            self._add_album(result)
          elif result['type'] == self._TYPE_PLAYLIST:
            self._add_playlist(result)

        self._addon.end_of_directory()


  def albums_in_collection(self, **params):
    start = int(params['start']) if 'start' in params else 0
    if 'key' in params:
      albums = self._rdio_api.call('getAlbumsInCollection', user = params['key'], extras = 'playCount,bigIcon', count = self._PAGE_SIZE_ALBUMS, start = start)
    else:
      albums = self._rdio_api.call('getAlbumsInCollection', extras = 'playCount,bigIcon', count = self._PAGE_SIZE_ALBUMS, start = start)

    self._add_albums(albums)

    # Add a "More..." menu option if there are too many albums
    if len(albums) == self._PAGE_SIZE_ALBUMS:
      queries = params.copy()
      queries['start'] = start + self._PAGE_SIZE_ALBUMS
      self._addon.add_item(queries, {'title': self._addon.get_string(30214).encode('UTF-8')}, is_folder = True)

    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ALBUM)
    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ARTIST)
    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def all_albums_for_artist(self, **params):
    self._albums_for_artist(**params)

  def top_albums_for_artist(self, **params):
    self._albums_for_artist(True, **params)

  def _albums_for_artist(self, top_only = False, **params):
    if top_only:
      albums = self._rdio_api.call('getAlbumsForArtist', artist = params['key'], extras = 'playCount,bigIcon', start = 0, count = 9)
    else:
      albums = self._rdio_api.call('getAlbumsForArtist', artist = params['key'], extras = 'playCount,bigIcon')

    self._add_albums(albums)

    if not top_only:
      xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ALBUM)
      xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_DATE)
    else:
      self._addon.add_directory({'mode': 'all_albums_for_artist', 'key': params['key']}, {'title': self._addon.get_string(30222).encode('UTF-8')})

    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def new_releases(self, **params):
    time_frame = params['time'] if 'time' in params else None
    if time_frame:
      albums = self._rdio_api.call('getNewReleases', time = time_frame, extras = 'playCount,bigIcon')
    else:
      albums = self._rdio_api.call('getNewReleases', extras = 'playCount,bigIcon')

    if not time_frame:
      self._addon.add_directory({'mode': 'new_releases', 'time': 'thisweek'}, {'title': self._addon.get_string(30234).encode('UTF-8')})
      self._addon.add_directory({'mode': 'new_releases', 'time': 'lastweek'}, {'title': self._addon.get_string(30235).encode('UTF-8')})
      self._addon.add_directory({'mode': 'new_releases', 'time': 'twoweeks'}, {'title': self._addon.get_string(30236).encode('UTF-8')})

    self._add_albums(albums)
    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def heavy_rotation(self):
    albums = self._rdio_api.call('getHeavyRotation', user = self._rdio_api.current_user(),
      friends = True, type = 'albums', start = 0, count = self._PAGE_SIZE_HEAVY_ROTATION, extras = 'playCount,bigIcon')
    self._add_albums(albums)
    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def top_charts(self):
    self._addon.add_directory({'mode': 'top_albums'}, {'title': self._addon.get_string(30224).encode('UTF-8')})
    self._addon.add_directory({'mode': 'top_artists'}, {'title': self._addon.get_string(30225).encode('UTF-8')})
    self._addon.add_directory({'mode': 'top_playlists'}, {'title': self._addon.get_string(30226).encode('UTF-8')})
    self._addon.add_directory({'mode': 'top_tracks'}, {'title': self._addon.get_string(30227).encode('UTF-8')})
    self._addon.end_of_directory()

  def top_albums(self):
    albums = self._rdio_api.call('getTopCharts', type = 'Album', count = 50, extras = 'playCount,bigIcon')
    self._add_albums(albums)
    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def top_artists(self):
    artists = self._rdio_api.call('getTopCharts', type = 'Artist', count = 50, extras = 'playCount')
    self._add_artists(artists)
    xbmcplugin.setContent(self._addon.handle, 'artists')
    self._addon.end_of_directory()

  def top_playlists(self):
    playlists = self._rdio_api.call('getTopCharts', type = 'Playlist', count = 50, extras = 'playCount')
    self._add_playlists(playlists)
    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def top_tracks(self):
    tracks = self._rdio_api.call('getTopCharts', type = 'Track', count = 50, extras = 'playCount,bigIcon,isInCollection')
    self._add_tracks(tracks)
    self._addon.end_of_directory()


  def _add_albums(self, albums):
    for album in albums:
      self._add_album(album)

  def _add_album(self, album):
    album_key = album['albumKey'] if 'albumKey' in album else album['key']
    add_collection_context_menu_item = self._build_context_menu_item(self._addon.get_string(30219), mode = 'add_to_collection', key = album_key)
    remove_collection_context_menu_item = self._build_context_menu_item(self._addon.get_string(30220), mode = 'remove_from_collection', key = album_key)
    playCount = album['playCount'] if album['playCount'] else 0
    title = '%s (%s)' % (album['name'], album['artist'])
    if not album['canStream']:
      title += '  :('

    self._addon.add_item({'mode': 'tracks', 'key': album['key']},
    {
      'title': title.encode('UTF-8'),
      'album': album['name'],
      'artist': album['artist'],
      'date': rdiocommon.iso_date_to_xbmc_date(album['releaseDate']),
      'duration': album['duration'],
      'playCount': playCount
    },
    item_type = 'music',
    contextmenu_items = [add_collection_context_menu_item, remove_collection_context_menu_item],
    img = album['bigIcon'] if 'bigIcon' in album else album['icon'],
    total_items = album['length'],
    is_folder = True)


  def artist(self, **params):
    key = params['key']
    self._addon.add_directory({'mode': 'top_albums_for_artist', 'key': key}, {'title': self._addon.get_string(30211).encode('UTF-8')})
    self._addon.add_directory({'mode': 'tracks_for_artist', 'key': key}, {'title': self._addon.get_string(30212).encode('UTF-8')})
    self._addon.add_directory({'mode': 'all_albums_for_artist', 'key': key}, {'title': self._addon.get_string(30221).encode('UTF-8')})
    self._addon.add_directory({'mode': 'related_artists', 'key': key}, {'title': self._addon.get_string(30213).encode('UTF-8')})
    self._addon.add_directory({'mode': 'play_artist_radio', 'key': key}, {'title': self._addon.get_string(30232).encode('UTF-8')})
    # self._addon.add_directory({'mode': 'artist_biography', 'key': key}, {'title': self._addon.get_string(30237).encode('UTF-8')})
    self._addon.end_of_directory()

  def artists_in_collection(self, **params):
    if 'key' in params:
      artists = self._rdio_api.call('getArtistsInCollection', user = params['key'])
    else:
      artists = self._rdio_api.call('getArtistsInCollection')

    for artist in artists:
      self._add_artist(artist)

    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ARTIST)
    xbmcplugin.setContent(self._addon.handle, 'artists')
    self._addon.end_of_directory()

  def albums_for_artist_in_collection(self, **params):
    artist = params['artist']
    user = params['key'] if 'key' in params else self._rdio_api.current_user()

    if user:
      albums = self._rdio_api.call('getAlbumsForArtistInCollection', artist = artist, user = user, extras = 'playCount,bigIcon,Track.isInCollection')
    else:
      albums = self._rdio_api.call('getAlbumsForArtistInCollection', artist = artist, extras = 'playCount,bigIcon,Track.isInCollection')

    self._add_albums(albums)
    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ALBUM)
    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.setContent(self._addon.handle, 'albums')

    self._addon.add_directory({'mode': 'play_artist_radio', 'key': artist, 'user': user}, {'title': self._addon.get_string(30233).encode('UTF-8')})
    self._addon.add_directory({'mode': 'artist', 'key': artist}, {'title': self._addon.get_string(30217).encode('UTF-8')})
    self._addon.end_of_directory()

  def related_artists(self, **params):
    artists = self._rdio_api.call('getRelatedArtists', artist = params['key'])
    self._add_artists(artists)
    xbmcplugin.setContent(self._addon.handle, 'artists')
    self._addon.end_of_directory()

  def artist_biography(self, **params):
    key = params['key']
    artist = self._rdio_api.call("get", keys = key, extras = '[{"field": "*", "exclude": true}, {"field": "review"}]')[key]
    biography = artist['review'] if 'review' in artist else self._addon.get_string(30238).encode('UTF-8')
    window = xbmcgui.Window()
    control = xbmcgui.ControlTextBox(0, 0, 500, 500)
    control.setText(biography)
    window.addControl(control)
    window.doModal()



  def _add_artists(self, artists):
    for artist in artists:
      self._add_artist(artist)

  def _add_artist(self, artist):
    queries = {'mode': 'artist', 'key': artist['key']}
    if artist['type'] == self._TYPE_ARTIST_IN_COLLECTION:
      queries['mode'] = 'albums_for_artist_in_collection'
      queries['key'] = artist['userKey']
      queries['artist'] = artist['artistKey']

    self._addon.add_item(queries,
      {
        'title': artist['name'].encode('UTF-8'),
        'artist': artist['name']
      },
      item_type = 'music',
      img = artist['icon'],
      is_folder = True)


  def playlists(self, **params):
    if 'key' in params:
      playlists = self._rdio_api.call('getPlaylists', user = params['key'], extras = 'description')
    else:
      playlists = self._rdio_api.call('getPlaylists', extras = 'description')

    self._add_playlists(playlists['owned'], True)
    self._add_playlists(playlists['collab'], True)
    self._add_playlists(playlists['subscribed'], False)

    xbmcplugin.setContent(self._addon.handle, 'albums')
    self._addon.end_of_directory()

  def _add_playlists(self, playlists, editable_playlist = False):
    for playlist in playlists:
      self._add_playlist(playlist, editable_playlist)

  def _add_playlist(self, playlist, editable_playlist = False):
    playlist_title = '%s (%s)' % (playlist['name'], playlist['owner'])
    subscribe_playlist_context_menu_item = self._build_context_menu_item(self._addon.get_string(30228), mode = 'add_to_collection', key = playlist['key'])
    unsubscribe_playlist_context_menu_item = self._build_context_menu_item(self._addon.get_string(30229), mode = 'remove_from_collection', key = playlist['key'])
    img = playlist['icon'] if 'icon' in playlist else ''
    length = playlist['length'] if 'length' in playlist else 0

    self._addon.add_item({'mode': 'tracks', 'key': playlist['key'], 'editable_playlist': editable_playlist},
      {
        'title': playlist_title.encode('UTF-8'),
        'album': playlist['name'],
        'artist': playlist['owner']
      },
      item_type = 'music',
      contextmenu_items = [subscribe_playlist_context_menu_item, unsubscribe_playlist_context_menu_item],
      img = img,
      total_items = length,
      is_folder = True)


  def following(self):
    followed_users = self._rdio_api.call('userFollowing', user = self._rdio_api.current_user())
    for followed_user in followed_users:
      self._add_user(followed_user)

    xbmcplugin.addSortMethod(self._addon.handle, xbmcplugin.SORT_METHOD_ARTIST)
    xbmcplugin.setContent(self._addon.handle, 'artists')
    self._addon.end_of_directory()


  def user(self, **params):
    key = params['key']
    self._addon.add_directory({'mode': 'albums_in_collection', 'key': key}, {'title': self._addon.get_string(30204).encode('UTF-8')})
    self._addon.add_directory({'mode': 'artists_in_collection', 'key': key}, {'title': self._addon.get_string(30203).encode('UTF-8')})
    self._addon.add_directory({'mode': 'playlists', 'key': key}, {'title': self._addon.get_string(30200).encode('UTF-8')})
    self._addon.end_of_directory()

  def _add_user(self, user):
    name = user['firstName']
    if user['lastName']:
      name += ' ' + user['lastName']

    self._addon.add_item({'mode': 'user', 'key': user['key']},
      {
        'title': name.encode('UTF-8'),
        'artist': name
      },
      item_type = 'music',
      img = user['icon'],
      is_folder = True)


  def tracks(self, **params):
    key = params['key']
    track_container = self._rdio_api.call('get', keys = key, extras = 'tracks,Track.isInCollection,playCount,bigIcon,Track.bigIcon')[key]
    if 'editable_playlist' in params and params['editable_playlist'] == 'True':
      self._add_tracks(track_container['tracks'], playlist_key = key)
    else:
      self._add_tracks(track_container['tracks'])

    # Add "More from this artist" link if container is an album or artist
    if track_container['type'][0] == self._TYPE_ALBUM or track_container['type'][0] == self._TYPE_ARTIST:
      self._addon.add_directory({'mode': 'artist', 'key': track_container['artistKey']}, {'title': self._addon.get_string(30217).encode('UTF-8')})

    self._addon.end_of_directory()

  def tracks_for_artist(self, **params):
    tracks = self._rdio_api.call('getTracksForArtist', artist = params['key'], extras = 'playCount,bigIcon,isInCollection', start = 0, count = 20)
    self._add_tracks(tracks)
    self._addon.add_directory({'mode': 'artist', 'key': params['key']}, {'title': self._addon.get_string(30217).encode('UTF-8')})
    self._addon.end_of_directory()


  def _add_tracks(self, tracks, show_artist = False, playlist_key = None, xbmc_playlist = False, extra_queries = None):
    i = 0
    for track in tracks:

      context_menus = []
      if 'isInCollection' in track and track['isInCollection']:
        context_menus.append(self._build_context_menu_item(self._addon.get_string(30220), mode = 'remove_from_collection', key = track['key']))
      else:
        context_menus.append(self._build_context_menu_item(self._addon.get_string(30219), mode = 'add_to_collection', key = track['key']))

      context_menus.append(self._build_context_menu_item(self._addon.get_string(30230), mode = 'add_to_playlist', key = track['key']))
      if playlist_key:
        context_menus.append(self._build_context_menu_item(self._addon.get_string(30231), mode = 'remove_from_playlist', key = track['key'], playlist = playlist_key))

      if not 'playCount' in track:
        track['playCount'] = 0

      title = track['name']
      if show_artist:
        title += ' (%s)' % track['artist']
      if not track['canStream']:
        title += '  :('

      queries = {'mode': 'play', 'key': track['key']}
      if extra_queries:
        queries.update(extra_queries)

      self._addon.add_item(queries,
        {
          'title': title.encode('UTF-8'),
          'artist': track['artist'],
          'album': track['album'],
          'duration': track['duration'],
          'tracknumber': track['trackNum'],
          'playCount': track['playCount']
        },
        playlist = xbmc_playlist,
        item_type = 'music',
        contextmenu_items = context_menus,
        img = track['bigIcon'] if 'bigIcon' in track else track['icon'])

      i += 1


  def play(self, **params):
    key = params['key']
    stream_url = self._rdio_api.resolve_playback_url(key)
    if stream_url:
      self._addon.resolve_url(stream_url)


  def add_to_collection(self, **params):
    key = params['key']
    if self._can_be_added_to_collection(key):
      track_keys= [key]
    else:
      track_keys = self._get_track_keys_not_in_collection(key)

    if track_keys:
      self._rdio_api.call('addToCollection', keys = ','.join(track_keys))

  def remove_from_collection(self, **params):
    key = params['key']
    if self._can_be_added_to_collection(key):
      track_keys= [key]
    else:
      track_keys = self._get_track_keys_in_collection(key)

    if track_keys:
      self._rdio_api.call('removeFromCollection', keys = ','.join(track_keys))

  def add_to_playlist(self, **params):
    playlist = self._get_user_selected_playlist()
    if playlist:
      self._rdio_api.call('addToPlaylist', playlist = playlist, tracks = params['key'])

  def remove_from_playlist(self, **params):
    track_to_remove = params['key']
    playlist = params['playlist']
    track_container = self._rdio_api.call('get', keys = playlist, extras = 'tracks')[playlist]
    i = 0
    index_to_remove = None
    for track in track_container['tracks']:
      if track['key'] == track_to_remove:
        index_to_remove = i
        break

      i += 1

    if index_to_remove:
      self._rdio_api.call('removeFromPlaylist', playlist = playlist, tracks = track_to_remove, index = index_to_remove, count = 1)


  def _get_user_selected_playlist(self):
    playlists = self._rdio_api.call('getPlaylists', extras = 'description')
    playlist_map = {}
    playlist_names = []
    for playlist in playlists['owned']:
      playlist_map[playlist['name']] = playlist['key']
      playlist_names.append(playlist['name'])

    for playlist in playlists['collab']:
      playlist_map[playlist['name']] = playlist['key']
      playlist_names.append(playlist['name'])

    dialog = xbmcgui.Dialog()
    selection = dialog.select("Select Playlist", playlist_names)
    result = None
    if selection >= 0:
      result = playlist_map[playlist_names[selection]]

    return result


  def _get_track_keys_in_collection(self, key):
    return self._get_track_keys(key, in_collection = True, not_in_collection = False)

  def _get_track_keys_not_in_collection(self, key):
    return self._get_track_keys(key, in_collection = False, not_in_collection = True)

  def _get_track_keys(self, key, in_collection = True, not_in_collection = True):
    track_keys = []
    track_container = self._rdio_api.call('get', keys = key, extras = 'tracks,Track.isInCollection')
    for track in track_container[key]['tracks']:
      if ((in_collection and track['isInCollection']) or (not_in_collection and not track['isInCollection'])):
        track_keys.append(track['key'])

    return track_keys


  def play_artist_radio(self, **params):
    artist = params['key']
    user = params['user'] if 'user' in params else None
    radio = RdioRadio(self._addon, self._rdio_api)
    radio.start_radio(artist, user)
    track = radio.next_track()
    if track:
      playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
      playlist.clear()
      self._add_tracks([track], xbmc_playlist = playlist, extra_queries = {'mode': 'play_artist_radio_track'})
      xbmc.Player().play(playlist)

  def play_artist_radio_track(self, **params):
    self.play(**params)

    radio = RdioRadio(self._addon, self._rdio_api)
    track = radio.next_track()
    if track:
      playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
      self._add_tracks([track], xbmc_playlist = playlist, extra_queries = {'mode': 'play_artist_radio_track'})


  def reauthenticate(self):
    self._rdio_api.logout()
    self.main()


  def settings(self):
    self._addon.show_settings()

  def _mandatory_settings_are_valid(self):
    return self._addon.get_setting('username') and self._addon.get_setting('password') and self._addon.get_setting('apikey') and self._addon.get_setting('apisecret')


  def _build_context_menu_item(self, menu_text, **queries):
    url = 'special://home/addons/%s/%s' % (ADDON_ID, os.path.basename(__file__))
    params = str(self._addon.handle) + ",?" + urllib.urlencode(queries)
    return (menu_text, 'XBMC.RunScript(%s, %s)' % (url, params))


  def _can_be_added_to_collection(self, key):
    return (key[0] == self._TYPE_TRACK and key[1].isdigit()) or (key[0] == self._TYPE_PLAYLIST)


  def execute(self):
    start_time = time.clock()
    mode = self._addon.queries['mode']
    self._addon.log_notice("Executing Rdio %s addon operation %s with params %s" % (self._addon.get_version(), mode, str(self._addon.queries)))
    handler = getattr(self, mode)
    handler_args = inspect.getargspec(handler)
    if handler_args.keywords and len(handler_args.keywords) > 1:
      handler(**self._addon.queries)
    else:
      handler()

    time_ms = (time.clock() - start_time) * 1000
    self._addon.log_notice("Executed Rdio addon operation %s in %i ms" % (mode, time_ms))


XbmcRdioOperation(addon).execute()
