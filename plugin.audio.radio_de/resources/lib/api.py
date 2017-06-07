#!/usr/bin/env python
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
import json
from urllib import urlencode
from urllib2 import urlopen, Request, HTTPError, URLError
import random


class RadioApiError(Exception):
    pass


class RadioApi():

    MAIN_URLS = {
        'english': 'http://rad.io/info',
        'german': 'http://radio.de/info',
        'french': 'http://radio.fr/info',
    }

    CATEGORY_TYPES = (
        'genre', 'topic', 'country', 'city', 'language',
    )

    USER_AGENT = 'XBMC Addon Radio'

    PLAYLIST_PREFIXES = ('m3u', 'pls', 'asx', 'xml')

    def __init__(self, language='english', user_agent=USER_AGENT):
        self.set_language(language)
        self.user_agent = user_agent

    def set_language(self, language):
        if not language in RadioApi.MAIN_URLS.keys():
            raise ValueError('Invalid language')
        self.api_url = RadioApi.MAIN_URLS[language]

    def get_recommendation_stations(self):
        self.log('get_recommendation_stations started')
        path = 'broadcast/editorialreccomendationsembedded'
        stations = self.__api_call(path)
        return self.__format_stations(stations)

    def get_top_stations(self):
        self.log('get_top_stations started')
        path = 'menu/broadcastsofcategory'
        param = {'category': '_top'}
        stations = self.__api_call(path, param)
        return self.__format_stations(stations)

    def get_local_stations(self, num_entries=25):
        self.log('get_local_stations started with num_entries=%d'
                 % num_entries)
        most_wanted_stations = self._get_most_wanted(num_entries)
        return self.__format_stations(most_wanted_stations['localBroadcasts'])

    def get_category_types(self):
        self.log('get_category_types started')
        return RadioApi.CATEGORY_TYPES

    def get_categories(self, category_type):
        self.log('get_categories started with category_type=%s'
                 % category_type)
        if not category_type in RadioApi.CATEGORY_TYPES:
            raise ValueError('Bad category_type')
        path = 'menu/valuesofcategory'
        param = {'category': '_%s' % category_type}
        categories = self.__api_call(path, param)
        return categories

    def get_stations_by_category(self, category_type, category_value):
        self.log(('get_stations_by_category started with category_type=%s, '
                  'category_value=%s') % (category_type, category_value))
        if not category_type in self.get_category_types():
            raise ValueError('Bad category_type')
        path = 'menu/broadcastsofcategory'
        param = {
            'category': '_%s' % category_type,
            'value': category_value,
        }
        stations = self.__api_call(path, param)
        return self.__format_stations(stations)

    def search_stations_by_string(self, search_string):
        self.log('search_stations_by_string started with search_string=%s'
                 % search_string)
        path = 'index/searchembeddedbroadcast'
        param = {
            'q': search_string,
            'start': '0',
            'rows': '10000',
            'streamcontentformats': 'aac,mp3',
        }
        stations = self.__api_call(path, param)
        return self.__format_stations(stations)

    def get_station_by_station_id(self, station_id, resolve_playlists=True):
        self.log('get_station_by_station_id started with station_id=%s'
                 % station_id)
        path = 'broadcast/getbroadcastembedded'
        param = {'broadcast': str(station_id)}
        station = self.__api_call(path, param)
        if self.__check_redirect(station['streamURL']):
            station['streamURL'] = self.__follow_redirect(station['streamURL'])
        if resolve_playlists and self.__check_paylist(station['streamURL']):
            playlist_url = station['streamURL']
            station['streamURL'] = self.__resolve_playlist(station)
        stations = (station, )
        return self.__format_stations(stations)[0]

    def _get_most_wanted(self, num_entries=25):
        self.log('get_most_wanted started with num_entries=%d'
                 % num_entries)
        if not isinstance(num_entries, int):
            raise TypeError('Need int')
        path = 'account/getmostwantedbroadcastlists'
        param = {'sizeoflists': str(num_entries)}
        stations_lists = self.__api_call(path, param)
        return stations_lists

    def __api_call(self, path, param=None):
        self.log('__api_call started with path=%s, param=%s'
                 % (path, param))
        url = '%s/%s' % (self.api_url, path)
        if param:
            url += '?%s' % urlencode(param)
        response = self.__urlopen(url)
        json_data = json.loads(response)
        return json_data

    def __resolve_playlist(self, station):
        self.log('__resolve_playlist started with station=%s'
                 % station['id'])
        servers = []
        stream_url = station['streamURL']
        if stream_url.lower().endswith('m3u'):
            response = self.__urlopen(stream_url)
            self.log('__resolve_playlist found .m3u file')
            servers = [
                l for l in response.splitlines()
                if l.strip() and not l.strip().startswith('#')
            ]
        elif stream_url.lower().endswith('pls'):
            response = self.__urlopen(stream_url)
            self.log('__resolve_playlist found .pls file')
            servers = [
                l.split('=')[1] for l in response.splitlines()
                if l.lower().startswith('file')
            ]
        elif stream_url.lower().endswith('asx'):
            response = self.__urlopen(stream_url)
            self.log('__resolve_playlist found .asx file')
            servers = [
                l.split('href="')[1].split('"')[0]
                for l in response.splitlines() if 'href' in l
            ]
        elif stream_url.lower().endswith('xml'):
            self.log('__resolve_playlist found .xml file')
            servers = [
                stream_url['streamUrl']
                for stream_url in station.get('streamUrls', [])
                if 'streamUrl' in stream_url
            ]
        if servers:
            self.log('__resolve_playlist found %d servers' % len(servers))
            return random.choice(servers)
        return stream_url

    def __follow_redirect(self, url):
        self.log('__follow_redirect probing url=%s' % url)
        req = Request(url)
        req.add_header('User-Agent', self.user_agent)
        response = urlopen(req)
        return response.geturl()

    def __urlopen(self, url):
        self.log('__urlopen opening url=%s' % url)
        req = Request(url)
        req.add_header('User-Agent', self.user_agent)
        try:
            response = urlopen(req).read()
        except HTTPError, error:
            self.log('__urlopen HTTPError: %s' % error)
            raise RadioApiError('HTTPError: %s' % error)
        except URLError, error:
            self.log('__urlopen URLError: %s' % error)
            raise RadioApiError('URLError: %s' % error)
        return response

    @staticmethod
    def __format_stations(stations):
        formated_stations = []
        for station in stations:
            thumbnail = (
                station.get('picture4TransName') or
                station.get('picture4Name') or
                station.get('picture1TransName').replace('_1_', '_4_') or
                station.get('picture1Name').replace('_1_', '_4_')
            )
            genre = station.get('genresAndTopics') or ','.join(
                station.get('genres', []) + station.get('topics', []),
            )
            formated_stations.append({
                'name': station['name'],
                'thumbnail': station['pictureBaseURL'] + thumbnail,
                'rating': station['rating'],
                'genre': genre,
                'bitrate': station['bitrate'],
                'id': station['id'],
                'current_track': station['currentTrack'],
                'stream_url': station.get('streamURL', ''),
                'description': station.get('description', '')
            })
        return formated_stations

    @staticmethod
    def __check_paylist(stream_url):
        for prefix in RadioApi.PLAYLIST_PREFIXES:
            if stream_url.lower().endswith(prefix):
                return True
        return False

    @staticmethod
    def __check_redirect(stream_url):
        if 'addrad.io' in stream_url:
            return True
        if '.nsv' in stream_url:
            return True
        return False

    @staticmethod
    def log(text):
        print 'RadioApi: %s' % repr(text)
