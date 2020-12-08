#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
 *  Copyright (C) 2019- enen92 (enen92@kodi.tv)
 *  Copyright (C) 2012-2019 Tristan Fischer (sphere@dersphere.de)
 *  This file is part of plugin.audio.radio_de
 *
 *  SPDX-License-Identifier: GPL-2.0-only
 *  See LICENSE.txt for more information.
'''

import json
import sys
import random
import xbmc

from urllib.parse import urlencode
from urllib.request import urlopen, Request, HTTPError, URLError


class RadioApiError(Exception):
    pass


class RadioApi():

    MAIN_URLS = {
        'english': 'http://api.rad.io/info',
        'german': 'http://api.radio.de/info',
        'french': 'http://api.radio.fr/info',
        'portuguese': 'http://api.radio.pt/info',
        'spanish': 'http://api.radio.es/info',
    }

    USER_AGENT = 'XBMC Addon Radio'

    PLAYLIST_PREFIXES = ('m3u', 'pls', 'asx', 'xml')

    def __init__(self, language='english', user_agent=USER_AGENT):
        self.set_language(language)
        self.user_agent = user_agent

    def set_language(self, language):
        if not language in RadioApi.MAIN_URLS.keys():
            raise ValueError('Invalid language')
        self.api_url = RadioApi.MAIN_URLS[language]

    def get_genres(self):
        self.log('get_genres started')
        path = 'v2/search/getgenres'
        return self.__api_call(path)

    def get_topics(self):
        self.log('get_topics started')
        path = 'v2/search/gettopics'
        return self.__api_call(path)

    def get_languages(self):
        self.log('get_topics started')
        path = 'v2/search/getlanguages'
        return self.__api_call(path)

    def get_countries(self):
        self.log('get_countries started')
        path = 'v2/search/getcountries'
        return self.__api_call(path)

    def get_cities(self, country=None):
        self.log('get_cities_by_country started with country = %s' % country)
        path = 'v2/search/getcities'
        if country:
            param = {
                'country': country
            }
            return self.__api_call(path, param)
        else:
            return self.__api_call(path)

    def get_recommendation_stations(self):
        self.log('get_recommendation_stations started')
        path = 'v2/search/editorstips'
        return self.__format_stations_v2(self.__api_call(path))

    def get_stations_by_genre(self, genre, sorttype, sizeperpage, pageindex):
        self.log(('get_stations_by_genre started with genre=%s, '
                  'sorttype=%s, sizeperpage=%s, pageindex=%s') % (
                      genre, sorttype, sizeperpage, pageindex))
        path = 'v2/search/stationsbygenre'
        param = {
            'genre': genre,
            'sorttype': sorttype,
            'sizeperpage': sizeperpage,
            'pageindex': pageindex
        }
        response = self.__api_call(path, param)
        if not response.get('categories'):
            raise ValueError('Bad category_type')
        return response.get('numberPages'), self.__format_stations_v2(response.get('categories')[0].get('matches'))

    def get_station_by_station_id(self, station_id, resolve_playlists=True, force_http=False):
        self.log('get_station_by_station_id started with station_id=%s'
                 % station_id)
        path = 'v2/search/station'
        param = {'station': str(station_id)}
        station = self.__api_call(path, param)

        streams = station.get('streamUrls')

        if streams:
            station['streamUrl'] = streams[0].get('streamUrl')

            if force_http:
                for stream in streams:
                    if "http://" in stream.get('streamUrl'):
                        station['streamUrl'] = stream['streamUrl']
                        break

        if not station.get('streamUrl'):
            self.log('Unable to detect a playable stream for station')
            return None

        if resolve_playlists and self.__check_paylist(station['streamUrl']):
            station['streamUrl'] = self.__resolve_playlist(station)
        stations = (station, )
        return self.__format_stations_v2(stations)[0]

    def internal_resolver(self, station, ):
        if station.get('is_custom', False):
            stream_url = station['stream_url']
        else:
            stream_url = station['streamUrl']

        if self.__check_paylist(stream_url):
            return self.__resolve_playlist(station)
        else:
            return stream_url

    def get_top_stations(self, sizeperpage, pageindex):
        self.log(('get_top_stations started with '
                  'sizeperpage=%s, pageindex=%s') % (
                      sizeperpage, pageindex))
        path = 'v2/search/topstations'
        param = {
            'sizeperpage': sizeperpage,
            'pageindex': pageindex
        }
        response = self.__api_call(path, param)
        if not response.get('categories'):
            raise ValueError('Bad category_type')
        return response.get('numberPages'), self.__format_stations_v2(response.get('categories')[0].get('matches'))

    def get_stations_by_country(self, country, sorttype, sizeperpage, pageindex):
        self.log(('get_stations_by_country started with country=%s, '
                  'sorttype=%s, sizeperpage=%s, pageindex=%s') % (
                      country, sorttype, sizeperpage, pageindex))
        path = 'v2/search/stationsbycountry'
        param = {
            'country': country,
            'sorttype': sorttype,
            'sizeperpage': sizeperpage,
            'pageindex': pageindex
        }
        response = self.__api_call(path, param)
        if not response.get('categories'):
            raise ValueError('Bad category_type')
        return response.get('numberPages'), self.__format_stations_v2(response.get('categories')[0].get('matches'))

    def get_stations_by_city(self, city, sorttype, sizeperpage, pageindex):
        self.log(('get_stations_by_city started with city=%s, '
                  'sorttype=%s, sizeperpage=%s, pageindex=%s') % (
                      city, sorttype, sizeperpage, pageindex))
        path = 'v2/search/stationsbycity'
        param = {
            'city': city,
            'sorttype': sorttype,
            'sizeperpage': sizeperpage,
            'pageindex': pageindex
        }
        response = self.__api_call(path, param)
        if not response.get('categories'):
            raise ValueError('Bad category_type')
        return response.get('numberPages'), self.__format_stations_v2(response.get('categories')[0].get('matches'))

    def get_stations_by_topic(self, topic, sorttype, sizeperpage, pageindex):
        self.log(('get_stations_by_topic started with topic=%s, '
                  'sorttype=%s, sizeperpage=%s, pageindex=%s') % (
                      topic, sorttype, sizeperpage, pageindex))
        path = 'v2/search/stationsbytopic'
        param = {
            'topic': topic,
            'sorttype': sorttype,
            'sizeperpage': sizeperpage,
            'pageindex': pageindex
        }
        response = self.__api_call(path, param)
        if not response.get('categories'):
            raise ValueError('Bad category_type')
        return response.get('numberPages'), self.__format_stations_v2(response.get('categories')[0].get('matches'))

    def get_stations_by_language(self, language, sorttype, sizeperpage, pageindex):
        self.log(('get_stations_by_language started with language=%s, '
                  'sorttype=%s, sizeperpage=%s, pageindex=%s') % (
                      language, sorttype, sizeperpage, pageindex))
        path = 'v2/search/stationsbylanguage'
        param = {
            'language': language,
            'sorttype': sorttype,
            'sizeperpage': sizeperpage,
            'pageindex': pageindex
        }
        response = self.__api_call(path, param)
        if not response.get('categories'):
            raise ValueError('Bad category_type')
        return response.get('numberPages'), self.__format_stations_v2(response.get('categories')[0].get('matches'))

    def get_stations_nearby(self, sizeperpage, pageindex):
        self.log(('get_stations_nearby started with, '
                  'sizeperpage=%s, pageindex=%s') % (sizeperpage, pageindex))
        path = 'v2/search/localstations'
        param = {
            'sizeperpage': sizeperpage,
            'pageindex': pageindex
        }
        response = self.__api_call(path, param)
        if not response.get('categories'):
            raise ValueError('Bad category_type')
        return response.get('numberPages'), self.__format_stations_v2(response.get('categories')[0].get('matches'))

    def search_stations_by_string(self, search_string, sizeperpage, pageindex):
        self.log('search_stations_by_string started with search_string=%s'
                 % search_string)
        path = 'v2/search/stations'
        param = {
            'query': search_string,
            'sizeperpage': sizeperpage,
            'pageindex': pageindex
        }
        response = self.__api_call(path, param)
        if not response.get('categories'):
            raise ValueError('Bad category_type')
        return response.get('numberPages'), self.__format_stations_v2(response.get('categories')[0].get('matches'))

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

        # Check if it is a custom station
        if station.get('is_custom', False):
            stream_url = station['stream_url']
        else:
            stream_url = station['streamUrl']

        if stream_url.lower().endswith('m3u'):
            response = self.__urlopen(stream_url)
            self.log('__resolve_playlist found .m3u file')
            servers = [
                l for l in response.splitlines()
                if l.strip() and not l.strip().startswith(self.__versioned_string('#'))
            ]
        elif stream_url.lower().endswith('pls'):
            response = self.__urlopen(stream_url)
            self.log('__resolve_playlist found .pls file')
            servers = [
                l.split(self.__versioned_string('='))[1] for l in response.splitlines()
                if l.lower().startswith(self.__versioned_string('file'))
            ]
        elif stream_url.lower().endswith('asx'):
            response = self.__urlopen(stream_url)
            self.log('__resolve_playlist found .asx file')
            servers = [
                l.split(self.__versioned_string('href="'))[1].split('"')[0]
                for l in response.splitlines() if self.__versioned_string('href') in l
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
        except HTTPError as error:
            self.log('__urlopen HTTPError: %s' % error)
            raise RadioApiError('HTTPError: %s' % error)
        except URLError as error:
            self.log('__urlopen URLError: %s' % error)
            raise RadioApiError('URLError: %s' % error)
        return response

    @staticmethod
    def __format_stations_v2(stations):
        formated_stations = []
        for station in stations:
            thumbnail = (
                station.get('logo300x300') or
                station.get('logo175x175') or
                station.get('logo100x100') or
                station.get('logo44x44')
            )

            try:
                genre = [g['value'] for g in station.get('genres')]
            except:
                genre = [g for g in station.get('genres')]

            try:
                description = station.get('description')['value'] if station.get('description') else ''
            except:
                description = station.get('description')

            try:
                name = station['name']['value'] if station.get('name') else ''
            except:
                name = station.get('name')

            formated_stations.append({
                'name': name,
                'thumbnail': thumbnail,
                'rating': station.get('rank', ''),
                'genre': ','.join(genre),
                'mediatype': 'song',
                'id': station['id'],
                'current_track': station.get('nowPlaying', ''),
                'stream_url': station.get('streamUrl', ''),
                'description': description
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
    def __versioned_string(string):
        return bytearray(string, 'utf-8')

    @staticmethod
    def log(text):
        xbmc.log('RadioApi: %s' % repr(text))
