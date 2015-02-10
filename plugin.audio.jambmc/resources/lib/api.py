#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import requests


API_URL = '%(scheme)s://api.jamendo.com/v3.0/'
USER_AGENT = 'XBMC Jamendo API'
SORT_METHODS = {
    'albums': (
        'releasedate_desc', 'releasedate_asc', 'popularity_total',
        'popularity_month', 'popularity_week'
    ),
    'artists': (
        'name', 'joindate_asc', 'joindate_desc', 'popularity_total',
        'popularity_month', 'popularity_week'
    ),
    'tracks': (
        'buzzrate', 'downloads_week', 'downloads_month', 'downloads_total',
        'listens_week', 'listens_month', 'listens_total', 'popularity_week',
        'popularity_month', 'popularity_total', 'releasedate_asc',
        'releasedate_desc'
    ),
}
AUDIO_FORMATS = {
    'mp3': 'mp32',
    'ogg': 'ogg',
    'flac': 'flac'
}
USER_TRACK_RELATIONS = (
    'like', 'favorite', 'review'
)
IMAGE_SIZES = {
    'big': '600',
    'medium': '400',
    'small': '200',
}
TAGS = (
    ('genres', (
        'electronic', 'rock', 'ambient', 'experimental', 'pop', 'techno',
        'metal', 'dance', 'hiphop', 'trance', 'classical', 'indie', 'punk',
        'jazz', 'folk',
        # 'industrial', 'lounge', 'funk', 'triphop', 'blues',
        # 'newage', 'world', 'reggae', 'poprock', 'easylistening', 'ska',
        # 'grunge', 'disco', 'country', 'rnb', 'latin', 'celtic', 'african',
        # 'island', 'asian', 'middleeastern'
    )),
    ('instruments', (
        'piano', 'synthesizer', 'electricguitar', 'bass', 'drum', 'computer',
        'acousticguitar', 'keyboard', 'violin', 'cello', 'saxophone', 'organ',
        # 'trumpet', 'flute', 'classicalguitar', 'viola', 'harmonica',
        # 'accordion', 'horn', 'clarinet', 'harp', 'oboe', 'slideguitar',
        # 'sitar', 'mandolin', 'harpsichord', 'banjo', 'steelpan', 'xylophone',
        # 'oud', 'cowbell', 'bagpipes'
    )),
    ('moods', (
        'soundtrack', 'emotion', 'soft', 'horror', 'comedy', 'political',
        'nature', 'drama', 'children', 'documentary', 'scifi', 'travel',
        # 'entertainment', 'adventure', 'videogame', 'religious', 'western',
        # 'culture', 'health', 'history', 'sport', 'silentfilm',
        # 'communication', 'education', 'adult', 'society', 'fashion',
        # 'wedding', 'news', 'crime'
    )),
)


class AuthError(Exception):
    pass


class ApiError(Exception):
    pass


class ConnectionError(Exception):
    pass


class JamendoApi():

    def __init__(self, client_id, use_https=True, limit=100,
                 audioformat=None, image_size=None):
        self._client_id = client_id
        self._use_https = bool(use_https)
        self._audioformat = AUDIO_FORMATS.get(audioformat, 'mp32')
        self._limit = min(int(limit), 100)
        self._image_size = IMAGE_SIZES.get(image_size, '400')

    def get_albums(self, page=1, artist_id=None, sort_method=None,
                   search_terms=None, ids=None):
        path = 'albums'
        params = {
            'imagesize': self._image_size,
            'limit': self._limit,
            'offset': self._limit * (int(page) - 1),
        }
        if artist_id:
            params['artist_id'] = [artist_id]
        if sort_method:
            params['order'] = sort_method
        if search_terms:
            params['namesearch'] = search_terms
        if ids:
            params['id'] = '+'.join(ids)
        albums = self._api_call(path, params)
        return albums

    def get_playlists(self, page=1, search_terms=None, user_id=None):
        path = 'playlists'
        params = {
            'limit': self._limit,
            'offset': self._limit * (int(page) - 1)
        }
        if search_terms:
            params['namesearch'] = search_terms
        if user_id:
            params['user_id'] = user_id
        playlists = self._api_call(path, params)
        return playlists

    def get_artists(self, page=1, sort_method=None, search_terms=None,
                    ids=None):
        path = 'artists'
        params = {
            'limit': self._limit,
            'offset': self._limit * (int(page) - 1),
        }
        if sort_method:
            params['order'] = sort_method
        if search_terms:
            params['namesearch'] = search_terms
        if ids:
            params['id'] = '+'.join(ids)
        artists = self._api_call(path, params)
        return artists

    def get_artists_by_location(self, coords, radius=100):
        path = 'artists/locations'
        params = {
            'location_coords': coords,
            'location_radius': radius,
            'haslocation': True,
        }
        artists = self._api_call(path, params)
        return artists

    def get_tracks(self, page=1, sort_method=None, filter_dict=None, tags=None,
                   audioformat=None, album_id=None, ids=None, featured=False):
        path = 'tracks'
        params = {
            'limit': self._limit,
            'offset': self._limit * (int(page) - 1),
            'include': 'musicinfo',
            'audioformat': AUDIO_FORMATS.get(audioformat) or self._audioformat,
            'imagesize': self._image_size,
        }
        if sort_method:
            params['order'] = sort_method
        if filter_dict:
            params.update(filter_dict)
        if album_id:
            params['album_id'] = album_id
        if ids:
            params['id'] = '+'.join(ids)
        if featured:
            params['featured'] = 1
        if tags:
            params['tags'] = tags
        tracks = self._api_call(path, params)
        return tracks

    def get_radios(self, page=1):
        path = 'radios'
        params = {
            'limit': self._limit,
            'offset': self._limit * (int(page) - 1),
            'imagesize': 150,
            'type': 'www'
        }
        radios = self._api_call(path, params)
        return radios

    def get_playlist_tracks(self, playlist_id):
        path = 'playlists/tracks'
        params = {'id': [playlist_id]}
        playlists = self._api_call(path, params)
        playlist = playlists[0] if playlists else {}
        tracks = playlist.get('tracks', [])
        return playlist, tracks

    def get_similar_tracks(self, track_id, page=1):
        path = 'tracks/similar'
        params = {
            'id': track_id,
            'limit': self._limit,
            'offset': self._limit * (int(page) - 1),
            'imagesize': self._image_size,
        }
        tracks = self._api_call(path, params)
        return tracks

    def search_tracks(self, search_terms, page=1):
        filter_dict = {
            'search': search_terms
        }
        return self.get_tracks(page=page, filter_dict=filter_dict)

    def get_track(self, track_id, audioformat=None):
        tracks = self.get_tracks(
            ids=[track_id], audioformat=audioformat
        )
        return tracks[0]

    def get_album(self, album_id):
        albums = self.get_albums(
            ids=[album_id]
        )
        return albums[0]

    def get_track_url(self, track_id, audioformat=None):
        path = 'tracks/file'
        params = {
            'audioformat': AUDIO_FORMATS.get(audioformat) or self._audioformat,
            'id': track_id
        }
        track_url = self._get_redirect_location(path, params)
        self.log('get_track_url track_url: %s' % track_url)
        return track_url

    def get_radio_url(self, radio_id):
        path = 'radios/stream'
        params = {
            'id': radio_id
        }
        radios = self._api_call(path, params)
        radio = radios[0] if radios else {}
        return radio.get('stream')

    def get_users(self, search_terms, page=1):
        path = 'users'
        params = {
            'name': search_terms,
            'limit': self._limit,
            'offset': self._limit * (int(page) - 1),
        }
        users = self._api_call(path, params)
        return users

    def get_user_artists(self, user_id, page=1):
        path = 'users/artists'
        params = {
            'id': user_id,
            'relation': 'fan',
            'limit': self._limit,
            'offset': self._limit * (int(page) - 1),
        }
        users = self._api_call(path, params)
        if users and users[0].get('artists'):
            artist_ids = set((a['id'] for a in users[0]['artists']))
            return self.get_artists(ids=artist_ids)
        return []

    def get_user_albums(self, user_id, page=1):
        path = 'users/albums'
        params = {
            'id': user_id,
            'relation': 'myalbums',
            'limit': self._limit,
            'offset': self._limit * (int(page) - 1),
        }
        users = self._api_call(path, params)
        if users and users[0].get('albums'):
            album_ids = set((a['id'] for a in users[0]['albums']))
            return self.get_albums(ids=album_ids)
        return []

    def get_user_tracks(self, user_id, relations=None, page=1):
        path = 'users/tracks'
        params = {
            'id': user_id,
            'relation': '+'.join(relations or USER_TRACK_RELATIONS),
            'limit': self._limit,
            'offset': self._limit * (int(page) - 1),
        }
        users = self._api_call(path, params)
        if users and users[0].get('tracks'):
            track_ids = set((a['id'] for a in users[0]['tracks']))
            return self.get_tracks(ids=track_ids)
        return []

    def _get_redirect_location(self, path, params={}):
        headers = {
            'user-agent': USER_AGENT
        }
        params.update({
            'client_id': self._client_id,
        })
        request = requests.get(
            self._api_url + path,
            headers=headers,
            params=params,
            verify=False,
            allow_redirects=False
        )
        return request.headers['Location']

    def _api_call(self, path, params={}):
        headers = {
            'content-type': 'application/json',
            'user-agent': USER_AGENT
        }
        params.update({
            'client_id': self._client_id,
            'format': 'json'
        })
        request = requests.get(
            self._api_url + path,
            headers=headers,
            params=params,
            verify=False  # XBMCs requests' SSL certificates are too old
        )
        self.log(u'_api_call using URL: %s' % request.url)
        json_data = request.json()
        return_code = json_data.get('headers', {}).get('code')
        if not return_code == 0:
            if return_code == 5:
                raise AuthError(json_data['headers']['error_message'])
            else:
                raise ApiError(json_data['headers']['error_message'])
        if json_data.get('headers', {}).get('warnings'):
            self.log('API-Warning: %s' % json_data['headers']['warnings'])
        self.log(u'_api_call got %d bytes response' % len(request.text))
        return json_data.get('results', [])

    @property
    def current_limit(self):
        return self._limit

    @property
    def _api_url(self):
        scheme = 'https' if self._use_https else 'http'
        return API_URL % {'scheme': scheme}

    @staticmethod
    def get_sort_methods(entity):
        return SORT_METHODS.get(entity, [])

    @staticmethod
    def get_tags():
        return TAGS

    def log(self, message):
        print u'[%s]: %s' % (self.__class__.__name__, repr(message))
