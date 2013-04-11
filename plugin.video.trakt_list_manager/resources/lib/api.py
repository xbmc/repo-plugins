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

import json
from urllib import quote_plus as quote
from urllib2 import urlopen, Request, HTTPError, URLError
from hashlib import sha1


API_URL = 'api.trakt.tv/'
USER_AGENT = 'XBMC Add-on Trakt.tv List Manager'

LIST_PRIVACY_IDS = (
    'private',
    'friends',
    'public'
)


class AuthenticationError(Exception):
    pass


class ConnectionError(Exception):
    pass


class TraktListApi():

    def __init__(self, *args, **kwargs):
        self._reset_connection()
        if args or kwargs:
            self.connect(*args, **kwargs)

    def _reset_connection(self):
        self.connected = False
        self._username = None
        self._password = None
        self._api_key = None
        self._use_https = True

    def connect(self, username=None, password=None, api_key=None,
                use_https=True):
        self._username = username
        self._password = sha1(password).hexdigest()
        self._api_key = api_key
        self._use_https = use_https
        self.connected = self._test_credentials()
        if not self.connected:
            self._reset_connection()
        return self.connected

    def get_watchlist(self):
        path = 'user/watchlist/movies.json/%(api_key)s/%(username)s'
        return self._api_call(path, auth=True)

    def get_lists(self):
        path = 'user/lists.json/%(api_key)s/%(username)s'
        return self._api_call(path, auth=True)

    def search_movie(self, query):
        path = 'search/movies.json/%(api_key)s/' + quote(query)
        return self._api_call(path)

    def get_list(self, list_slug):
        path = 'user/list.json/%(api_key)s/%(username)s/' + quote(list_slug)
        return self._api_call(path, auth=True)

    def add_list(self, name, privacy_id=None, description=None):
        path = 'lists/add/%(api_key)s'
        post = {
            'name': name,
            'description': description or '',
            'privacy': privacy_id or LIST_PRIVACY_IDS[0]
        }
        return self._api_call(path, post=post, auth=True)

    def del_list(self, list_slug):
        path = 'lists/delete/%(api_key)s'
        post = {
            'slug': list_slug
        }
        return self._api_call(path, post=post, auth=True)

    def add_movie_to_list(self, list_slug, imdb_id=None, tmdb_id=None):
        if not tmdb_id and not imdb_id:
            raise AttributeError('Need one of tmdb_id, imdb_id')
        item = {'type': 'movie'}
        if tmdb_id:
            item['tmdb_id'] = tmdb_id
        if imdb_id:
            item['imdb_id'] = imdb_id
        path = 'lists/items/add/%(api_key)s'
        post = {
            'slug': list_slug,
            'items': [item],
        }
        return self._api_call(path, post=post, auth=True)

    def add_movie_to_watchlist(self, imdb_id=None, tmdb_id=None):
        if not tmdb_id and not imdb_id:
            raise AttributeError('Need one of tmdb_id, imdb_id')
        item = {'type': 'movie'}
        if tmdb_id:
            item['tmdb_id'] = tmdb_id
        if imdb_id:
            item['imdb_id'] = imdb_id
        path = 'movie/watchlist/%(api_key)s'
        post = {
            'movies': [item],
        }
        return self._api_call(path, post=post, auth=True)

    def del_movie_from_list(self, list_slug, imdb_id=None, tmdb_id=None):
        if not tmdb_id and not imdb_id:
            raise AttributeError('Need one of tmdb_id, imdb_id')
        item = {'type': 'movie'}
        if tmdb_id:
            item['tmdb_id'] = tmdb_id
        if imdb_id:
            item['imdb_id'] = imdb_id
        path = 'lists/items/delete/%(api_key)s'
        post = {
            'slug': list_slug,
            'items': [item],
        }
        return self._api_call(path, post=post, auth=True)

    def del_movie_from_watchlist(self, imdb_id=None, tmdb_id=None):
        if not tmdb_id and not imdb_id:
            raise AttributeError('Need one of tmdb_id, imdb_id')
        item = {'type': 'movie'}
        if tmdb_id:
            item['tmdb_id'] = tmdb_id
        if imdb_id:
            item['imdb_id'] = imdb_id
        path = 'movie/unwatchlist/%(api_key)s'
        post = {
            'movies': [item],
        }
        return self._api_call(path, post=post, auth=True)

    def _test_credentials(self):
        path = 'account/test/%(api_key)s'
        return self._api_call(path, auth=True).get('status') == 'success'

    def _api_call(self, path, post={}, auth=False):
        url = self._api_url + path % {
            'api_key': self._api_key,
            'username': self._username
        }
        self.log('_api_call using url: %s' % url)
        if auth:
            post.update({
                'username': self._username,
                'password': self._password
            })
        if post:
            request = Request(url, json.dumps(post))
        else:
            request = Request(url)
        request.add_header('User-Agent', USER_AGENT)
        request.add_header('content-type', 'application/json')
        try:
            response = urlopen(request)
            json_data = json.loads(response.read())
        except HTTPError, error:
            self.log('HTTPError: %s' % error)
            if error.code == 401:
                raise AuthenticationError(error)
            else:
                raise HTTPError(error)
        except URLError, error:
            self.log('URLError: %s' % error)
            raise ConnectionError(error)
        self.log('_api_call response: %s' % repr(json_data))
        return json_data

    @property
    def _api_url(self):
        return '%s://%s' % ('https' if self._use_https else 'http', API_URL)

    def log(self, text):
        print u'[%s]: %s' % (self.__class__.__name__, repr(text))
