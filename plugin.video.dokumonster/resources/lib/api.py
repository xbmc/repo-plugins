#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer (sphere@dersphere.de)
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

import sys

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

from urllib import urlencode
from urllib2 import urlopen, Request, HTTPError, URLError

API_URL = 'http://dokumonster.de/api/0.1/'


class NetworkError(Exception):
    pass


class ApiError(Exception):
    pass


class DokuMonsterApi():

    USER_AGENT = 'XBMC DokuMonsterApi'

    def __init__(self, default_count=None):
        self.default_count = default_count or 50

    def get_tags(self):
        params = {
            'limit': self.default_count,
            'sort': 'count'
        }
        json_data = self.__api_call(path='get_tags', params=params)
        return [{
            'id': genre.get('id'),
            'name': genre.get('name'),
            'count': genre.get('count'),
        } for genre in json_data.get('items', [])]

    def get_popular_docus(self, page='1'):
        return self._get_items(sort='views', sortorder='desc', page=page)

    def get_top_docus(self, page='1'):
        return self._get_items(sort='fire', sortorder='desc', page=page)

    def get_newest_docus(self, page='1'):
        return self._get_items(sort='id', sortorder='desc', page=page)

    def get_docus_by_initial(self, initial, page='1'):
        return self._get_items(sort='title', initial=initial,
                               sortorder='asc', page=page)

    def get_docus_by_tag(self, tag, page='1'):
        return self._get_items(tag=tag, page=page)

    def get_docus_by_query(self, query, page='1'):
        return self._get_items(query=query, page=page)

    def get_docu(self, docu_id):
        params = {'id': docu_id}
        json_data = self.__api_call(path='get_item', params=params)
        return json_data.get('items', [])[0]

    def _get_items(self, **kwargs):
        params = {}
        valid_kwargs = (
            'sort', 'tag', 'query', 'initial', 'online',
            'sortorder', 'limit', 'offset', 'page'
        )
        for key, val in kwargs.items():
            if key in valid_kwargs:
                params[key] = val
        if not 'limit' in params:
            params['limit'] = self.default_count
        if not 'online' in params:
            params['online'] = 'true'
        page = params.pop('page', False)
        if page:
            params['offset'] = (int(page) - 1) * params['limit']
        json_data = self.__api_call(path='get_items', params=params)
        items = json_data.get('items', [])
        total_count = int(json_data.get('total_count', 0))
        return items, total_count

    def __api_call(self, path, params=None):
        url = API_URL + path
        if params:
            url += '?%s' % urlencode(params)
        req = Request(url)
        req.add_header('User Agent', self.USER_AGENT)
        log('Opening URL: %s' % url)
        try:
            response = urlopen(req).read()
        except HTTPError, error:
            raise NetworkError('HTTPError: %s' % error)
        except URLError, error:
            raise NetworkError('URLError: %s' % error)
        log('got %d bytes' % len(response))
        json_data = json.loads(response)
        if not json_data.get('status', {}).get('success'):
            err = json_data.get('status', {}).get('error')
            log('Error: %s' % repr(err))
            raise ApiError(err)
        return json_data


def log(msg):
    print '[DokuMonsterApi]: %s' % msg


if __name__ == '__main__':
    # API testing
    api = DokuMonsterApi()

    print 'Testing get_tags'
    tags = api.get_tags()
    assert tags
    for tag in tags[0:2]:
        print '<Tag:%s>' % repr(tag)

    print 'Testing get_newest_docus'
    docus = api.get_newest_docus()
    assert docus
    for docu in docus[0:2]:
        print '<Docu:%s>' % repr(docu)

    print 'Testing get_popular_docus'
    docus = api.get_popular_docus()
    assert docus
    for docu in docus[0:2]:
        print '<Docu:%s>' % repr(docu)

    print 'Testing get_top_docus'
    docus = api.get_top_docus()
    assert docus
    for docu in docus[0:2]:
        print '<Docu:%s>' % repr(docu)
