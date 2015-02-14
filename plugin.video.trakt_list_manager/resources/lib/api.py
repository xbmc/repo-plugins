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
from urllib import urlencode
from urllib2 import urlopen, Request, HTTPError, URLError

API_URL = 'api-v2launch.trakt.tv'
USER_AGENT = 'XBMC Add-on Trakt.tv List Manager'
NONE = 'NONE'
PAGE_LIMIT = 30

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
        self._username = None
        self._password = None
        self._token = ''
        self._api_key = None
        self._use_https = True

    def connect(self, username=None, password=None, token='', api_key=None,
                use_https=True):
        self._username = username
        self._password = password
        self._api_key = api_key
        self._use_https = use_https
        if not token:
            self._token = self.login()
            if not self._token:
                self._reset_connection()
        else:
            self._token = token
        return self._token

    def get_watchlist(self):
        path = '/users/me/watchlist/movies?extended=full,images'
        return self._api_call(path, auth=True)

    def get_lists(self):
        path = '/users/me/lists'
        return self._api_call(path, auth=True)

    def search_movie(self, query):
        path = '/search?' + urlencode({'type': 'movie', 'query': query, 'limit': PAGE_LIMIT})
        return self._api_call(path)

    def get_list(self, list_slug):
        path = '/users/me/lists/%s/items?extended=full,images' % (list_slug)
        return self._api_call(path, auth=True)

    def add_list(self, name, privacy_id=None, description=None):
        path = '/users/me/lists'
        post = {
            'name': name,
            'description': description or '',
            'privacy': privacy_id or LIST_PRIVACY_IDS[0]
        }
        return self._api_call(path, post=post, auth=True)

    def del_list(self, list_slug):
        path = '/users/me/lists/%s' % (list_slug)
        return self._api_call(path, delete=True, auth=True)

    def add_movie_to_list(self, list_slug, imdb_id=None, tmdb_id=None):
        if not tmdb_id and not imdb_id:
            raise AttributeError('Need one of tmdb_id, imdb_id')
        item = {'ids': {}}
        if tmdb_id and tmdb_id != NONE:
            item['ids']['tmdb'] = tmdb_id
        if imdb_id and imdb_id != NONE:
            item['ids']['imdb'] = imdb_id
        path = '/users/me/lists/%s/items' % (list_slug)
        post = {
            'movies': [item],
        }
        return self._api_call(path, post=post, auth=True)

    def add_movie_to_watchlist(self, imdb_id=None, tmdb_id=None):
        if not tmdb_id and not imdb_id:
            raise AttributeError('Need one of tmdb_id, imdb_id')
        item = {'ids': {}}
        if tmdb_id and tmdb_id != NONE:
            item['ids']['tmdb'] = tmdb_id
        if imdb_id and imdb_id != NONE:
            item['ids']['imdb'] = imdb_id
        path = '/sync/watchlist'
        post = {
            'movies': [item],
        }
        return self._api_call(path, post=post, auth=True)

    def del_movie_from_list(self, list_slug, imdb_id=None, tmdb_id=None):
        if not tmdb_id and not imdb_id:
            raise AttributeError('Need one of tmdb_id, imdb_id')
        item = {'ids': {}}
        if tmdb_id and tmdb_id != NONE:
            item['ids']['tmdb'] = tmdb_id
        if imdb_id and imdb_id != NONE:
            item['ids']['imdb'] = imdb_id
        path = '/users/me/lists/%s/items/remove' % (list_slug)
        post = {
            'movies': [item],
        }
        return self._api_call(path, post=post, auth=True)

    def del_movie_from_watchlist(self, imdb_id=None, tmdb_id=None):
        if not tmdb_id and not imdb_id:
            raise AttributeError('Need one of tmdb_id, imdb_id')
        item = {'ids': {}}
        if tmdb_id and tmdb_id != NONE:
            item['ids']['tmdb'] = tmdb_id
        if imdb_id and imdb_id != NONE:
            item['ids']['imdb'] = imdb_id
        path = '/sync/watchlist/remove'
        post = {
            'movies': [item],
        }
        return self._api_call(path, post=post, auth=True)

    def login(self):
        path = '/auth/login'
        post = {
                'login': self._username,
                'password': self._password}
        result = self._api_call(path, post = post)
        if 'token' in result:
            self._token = result['token']
            return result['token']
        else:
            return '' 

    def _api_call(self, path, delete= False, post=None, auth=False):
        if post is None: post = {}
        url = self._api_url + path
        headers = {
                   'User-Agent': USER_AGENT,
                   'Content-Type': 'application/json', 
                   'trakt-api-key': self._api_key,
                   'trakt-api-version': 2}
        
        auth_retry = False
        while True:
            if auth:
                if not self._token:
                    self.login()
                headers.update({
                    'trakt-user-login': self._username,
                    'trakt-user-token': self._token})
    
            self.log('_api_call using url: |%s| headers: |%s| post: |%s|' % (url, headers, post))
            if post:
                request = Request(url, json.dumps(post), headers=headers)
            else:
                request = Request(url, headers=headers)
            
            if delete:
                request.get_method = lambda: 'DELETE'
            
            try:
                response = urlopen(request)
                data = response.read()
                if data:
                    json_data = json.loads(data)
                else:
                    json_data = {}
                break
                    
            except HTTPError as error:
                self.log('HTTPError: %s' % error)
                if error.code == 401:
                    if not auth or auth_retry:
                        raise AuthenticationError(error)
                    else:
                        auth_retry = True
                        self._token = ''
                else:
                    raise
            except URLError as error:
                self.log('URLError: %s' % error)
                raise ConnectionError(error)
        self.log('_api_call response: %s' % repr(json_data))
        return json_data

    @property
    def _api_url(self):
        return '%s://%s' % ('https' if self._use_https else 'http', API_URL)

    def log(self, text):
        print u'[%s]: %s' % (self.__class__.__name__, repr(text))
