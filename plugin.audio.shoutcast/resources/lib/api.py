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

from urllib import urlencode
from urllib2 import urlopen, Request, HTTPError, URLError
import random
import simplejson as json
import xmltodict

API_URL = 'http://api.shoutcast.com/'
PLAYLIST_URL = 'http://yp.shoutcast.com/sbin/tunein-station.m3u?id={station_id}'


class NetworkError(Exception):
    pass


class ShoutcastApi():

    # Thanks for blocking XBMC, eat this.
    USER_AGENT = (
        'Mozilla/5.0 (Windows NT 6.1; WOW64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/40.0.2214.111 Safari/537.36'
    )

    def __init__(self, api_key, limit=500):
        self.api_key = api_key
        self.set_limit(limit)

    def set_limit(self, limit):
        self.limit = int(limit)

    def get_top500_stations(self):
        path = 'legacy/Top500'
        data = self.__api_call(path)
        return self._parse_stations(data['stationlist'])

    def get_genres(self, parent_id=None):
        params = {'f': 'json'}
        if parent_id:
            path = 'genre/secondary'
            params['parentid'] = int(parent_id)
        else:
            path = 'genre/primary'
        data = self.__api_call(path, params)
        return self._parse_genre(data['response']['data']['genrelist'])

    def get_stations(self, genre_id, page=0):
        params = {
            'f': 'xml',
            'genre_id': int(genre_id),
            'limit': '%d,%d' % (self.limit * page, self.limit)
        }
        path = 'station/advancedsearch'
        data = self.__api_call(path, params)
        return self._parse_stations(data['response']['data']['stationlist'])

    def get_station(self, station_id, station_name):
        # This is hacky but there is no other way to get a single station by id
        stations = self.search_stations(station_name)
        station = [s for s in stations if int(s['id']) == int(station_id)]
        return station[0]

    def search_stations(self, search_string, page=0):
        params = {
            'f': 'xml',
            'search': search_string,
            'limit': '%d,%d' % (self.limit * page, self.limit)
        }
        path = 'legacy/stationsearch'
        data = self.__api_call(path, params)
        return self._parse_stations(data['stationlist'])

    def search_current_track(self, search_string, page=0):
        params = {
            'f': 'xml',
            'ct': search_string,
            'limit': '%d,%d' % (self.limit * page, self.limit)
        }
        path = 'station/nowplaying'
        data = self.__api_call(path, params)
        return self._parse_stations(data['response']['data']['stationlist'])

    @staticmethod
    def _parse_stations(stations):

        def __clean(title):
            s = ' - a SHOUTcast.com member station'
            return unicode(title).replace(s, '')

        items = stations.get('station', [])
        if not isinstance(items, list):
            items = [items, ]
        return [{
            'id': int(station['@id']),
            'name': __clean(station.get('@name', '')),
            'bitrate': int(station.get('@br', 0)),
            'listeners': int(station.get('@lc', 0)),
            'current_track': station.get('@ct', ''),
            'genre': station.get('@genre', ''),
            'media_type': station.get('@mt', ''),
        } for station in items]

    @staticmethod
    def _parse_genre(genres):
        return [{
            'id': int(genre['id']),
            'name': genre.get('name', ''),
            'has_childs': genre.get('haschildren'),
            'has_parent': int(genre.get('parentid', 0)) != 0
        } for genre in genres.get('genre', [])]

    def resolve(self, station_id):
        response = self.__urlopen(PLAYLIST_URL.format(station_id=station_id))
        stream_urls = [
            l for l in response.splitlines()
            if l.strip() and not l.strip().startswith('#')
        ]
        if stream_urls:
            return random.choice(stream_urls)

    def __api_call(self, path, params=None):
        if not params:
            params = {}
        params['k'] = self.api_key
        url = API_URL + path
        if params:
            url += '?%s' % urlencode(params)
        response = self.__urlopen(url)
        if params.get('f') == 'json':
            data = json.loads(response)
        else:
            data = xmltodict.parse(response)
        return data

    def __urlopen(self, url):
        print 'Opening url: %s' % url
        req = Request(url)
        req.add_header('User Agent', self.USER_AGENT)
        try:
            response = urlopen(req).read()
        except HTTPError, error:
            raise NetworkError('HTTPError: %s' % error)
        except URLError, error:
            raise NetworkError('URLError: %s' % error)
        return response


def test():
    api = ShoutcastApi('sh1t7hyn3Kh0jhlV')
    assert api.get_top500_stations()
    genres = api.get_genres()
    assert genres
    for genre in genres[0:4]:
        stations = api.get_stations(genre['id'])
        assert stations
        subgenres = api.get_genres(genre['id'])
        assert subgenres
        for subgenre in subgenres[0:1]:
            stations = api.get_stations(subgenre['id'])
            assert stations
    assert api.search_stations('sky.fm')
    assert api.search_current_track('Rihanna')


if __name__ == '__main__':
    test()
