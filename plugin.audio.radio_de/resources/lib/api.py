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

import random
import xbmc

from urllib.request import urlopen, Request, HTTPError, URLError

from resources.lib.radiobrowser_client import RadioBrowserClient, RadioBrowserError


class RadioApiError(Exception):
    pass


class RadioApi():

    SUPPORTED_LANGUAGES = ('english', 'german', 'french', 'portuguese', 'spanish')

    USER_AGENT = 'XBMC Addon Radio'

    PLAYLIST_PREFIXES = ('m3u', 'pls', 'asx', 'xml')

    CACHED_FIELDS = ('name', 'thumbnail', 'stream_url', 'current_track')

    def __init__(self, language='english', user_agent=USER_AGENT):
        self.user_agent = user_agent
        self.client = RadioBrowserClient(user_agent=user_agent)
        self.language = 'english'
        self.set_language(language)

    def set_language(self, language):
        if language not in RadioApi.SUPPORTED_LANGUAGES:
            raise ValueError('Invalid language')
        self.language = language

    def __sort_key(self, sorttype):
        if sorttype == 'STATION_NAME':
            return 'name'
        return 'clickcount'

    @staticmethod
    def __page_count_from_has_more(pageindex, has_more):
        if has_more:
            return int(pageindex) + 1
        return int(pageindex)

    @staticmethod
    def __normalize_category(items, key='name'):
        categories = []
        seen = set()
        for item in items:
            value = item.get(key, '').strip()
            if value and value.lower() not in seen:
                categories.append({'systemEnglish': value})
                seen.add(value.lower())
        return categories

    def get_genres(self):
        self.log('get_genres started')
        tags = self.client.get_tags()
        return self.__normalize_category(tags)

    def get_topics(self):
        self.log('get_topics started')
        tags = self.client.get_tags()
        return self.__normalize_category(tags)

    def get_languages(self):
        self.log('get_topics started')
        languages = self.client.get_languages()
        return self.__normalize_category(languages)

    def get_countries(self):
        self.log('get_countries started')
        countries = self.client.get_countries()
        return self.__normalize_category(countries)

    def get_cities(self, country=None):
        self.log('get_cities_by_country started with country = %s' % country)
        states = self.client.get_states(country=country)
        return self.__normalize_category(states)

    def get_recommendation_stations(self):
        self.log('get_recommendation_stations started')
        has_more, stations = self.client.list_stations(50, 1, 'stations/topclick', order='clickcount')
        return self.__format_stations_v2(stations)

    def get_stations_by_genre(self, genre, sorttype, sizeperpage, pageindex):
        self.log(('get_stations_by_genre started with genre=%s, '
                  'sorttype=%s, sizeperpage=%s, pageindex=%s') % (
                      genre, sorttype, sizeperpage, pageindex))
        has_more, stations = self.client.search_stations(
            sizeperpage,
            pageindex,
            order=self.__sort_key(sorttype),
            tag=genre
        )
        return self.__page_count_from_has_more(pageindex, has_more), self.__format_stations_v2(stations)

    def get_station_by_station_id(self, station_id, resolve_playlists=True, force_http=False):
        self.log('get_station_by_station_id started with station_id=%s'
                 % station_id)
        station = self.client.get_station_by_uuid(station_id)
        if not station:
            self.log('Unable to detect a playable stream for station')
            return None

        station['streamUrl'] = station.get('url_resolved') or station.get('url')

        if force_http and station.get('url') and station.get('url').startswith('http://'):
            station['streamUrl'] = station.get('url')

        if not station.get('streamUrl'):
            self.log('Unable to detect a playable stream for station')
            return None

        if resolve_playlists and self.__check_paylist(station['streamUrl']):
            station['streamUrl'] = self.__resolve_playlist(station)
        stations = (station, )
        return self.__format_stations_v2(stations)[0]

    def get_station_cached(self, station_id, cache, resolve_playlists=True, force_http=False):
        '''Like get_station_by_station_id, but remembers the fields needed for
        playback in `cache` (a dict) and falls back to them when the lookup
        fails, so stations that were played before survive a Radio Browser outage.'''
        try:
            station = self.get_station_by_station_id(station_id, resolve_playlists, force_http)
        except RadioApiError as error:
            cached = cache.get(station_id)
            if not cached:
                raise
            self.log('using cached station %s after: %s' % (station_id, error))
            return cached
        if station:
            cache[station_id] = {key: station.get(key, '') for key in RadioApi.CACHED_FIELDS}
        return station

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
        has_more, stations = self.client.list_stations(
            sizeperpage,
            pageindex,
            'stations/topclick',
            order='clickcount'
        )
        return self.__page_count_from_has_more(pageindex, has_more), self.__format_stations_v2(stations)

    def get_stations_by_country(self, country, sorttype, sizeperpage, pageindex):
        self.log(('get_stations_by_country started with country=%s, '
                  'sorttype=%s, sizeperpage=%s, pageindex=%s') % (
                      country, sorttype, sizeperpage, pageindex))
        has_more, stations = self.client.search_stations(
            sizeperpage,
            pageindex,
            order=self.__sort_key(sorttype),
            country=country
        )
        return self.__page_count_from_has_more(pageindex, has_more), self.__format_stations_v2(stations)

    def get_stations_by_city(self, city, sorttype, sizeperpage, pageindex):
        self.log(('get_stations_by_city started with city=%s, '
                  'sorttype=%s, sizeperpage=%s, pageindex=%s') % (
                      city, sorttype, sizeperpage, pageindex))
        has_more, stations = self.client.search_stations(
            sizeperpage,
            pageindex,
            order=self.__sort_key(sorttype),
            state=city
        )
        return self.__page_count_from_has_more(pageindex, has_more), self.__format_stations_v2(stations)

    def get_stations_by_topic(self, topic, sorttype, sizeperpage, pageindex):
        self.log(('get_stations_by_topic started with topic=%s, '
                  'sorttype=%s, sizeperpage=%s, pageindex=%s') % (
                      topic, sorttype, sizeperpage, pageindex))
        has_more, stations = self.client.search_stations(
            sizeperpage,
            pageindex,
            order=self.__sort_key(sorttype),
            tag=topic
        )
        return self.__page_count_from_has_more(pageindex, has_more), self.__format_stations_v2(stations)

    def get_stations_by_language(self, language, sorttype, sizeperpage, pageindex):
        self.log(('get_stations_by_language started with language=%s, '
                  'sorttype=%s, sizeperpage=%s, pageindex=%s') % (
                      language, sorttype, sizeperpage, pageindex))
        has_more, stations = self.client.search_stations(
            sizeperpage,
            pageindex,
            order=self.__sort_key(sorttype),
            language=language
        )
        return self.__page_count_from_has_more(pageindex, has_more), self.__format_stations_v2(stations)

    def get_stations_nearby(self, sizeperpage, pageindex):
        self.log(('get_stations_nearby started with, '
                  'sizeperpage=%s, pageindex=%s') % (sizeperpage, pageindex))
        has_more, stations = self.client.list_stations(
            sizeperpage,
            pageindex,
            'stations/topvote',
            order='votes'
        )
        return self.__page_count_from_has_more(pageindex, has_more), self.__format_stations_v2(stations)

    def search_stations_by_string(self, search_string, sizeperpage, pageindex):
        self.log('search_stations_by_string started with search_string=%s'
                 % search_string)
        has_more, stations = self.client.search_stations(
            sizeperpage,
            pageindex,
            order='clickcount',
            name=search_string
        )
        return self.__page_count_from_has_more(pageindex, has_more), self.__format_stations_v2(stations)

    def __resolve_playlist(self, station):
        self.log('__resolve_playlist started with station=%s'
                 % station.get('id', station.get('stationuuid', 'unknown')))
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
            return self.__ensure_text(random.choice(servers))
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
            thumbnail = station.get('favicon')

            genres_value = station.get('tags', '')
            if isinstance(genres_value, list):
                genre = genres_value
            else:
                genre = [value.strip() for value in genres_value.split(',') if value.strip()]

            description = station.get('homepage') or ''
            name = station.get('name') or ''

            formated_stations.append({
                'name': name,
                'thumbnail': thumbnail,
                'rating': station.get('votes', station.get('clickcount', 0)),
                'genre': ','.join(genre),
                'mediatype': 'song',
                'id': station.get('stationuuid'),
                'current_track': station.get('lastsong', ''),
                'stream_url': station.get('streamUrl', station.get('url_resolved', station.get('url', ''))),
                'description': description,
                'bitrate': station.get('bitrate', 0)
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
    def __ensure_text(value):
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore').strip()
        return str(value).strip()

    @staticmethod
    def log(text):
        xbmc.log('RadioApi: %s' % repr(text))

    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if callable(attr) and (name.startswith('get_') or name.startswith('search_')):
            def wrapped(*args, **kwargs):
                try:
                    return attr(*args, **kwargs)
                except RadioBrowserError as error:
                    raise RadioApiError(str(error))
            return wrapped
        return attr
