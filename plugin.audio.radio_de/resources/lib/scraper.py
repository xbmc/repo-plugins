#!/usr/bin/python

import simplejson as json
from urllib import urlencode
from urllib2 import urlopen, Request, HTTPError, URLError

MAIN_URLS = {'english': 'http://rad.io/info',
             'german': 'http://radio.de/info',
             'french': 'http://radio.fr/info'}
USER_AGENT = 'radio.de 1.9.1 rv:37 (iPhone; iPhone OS 5.0; de_DE)'
VALID_CATEGORY_TYPES = ('genre', 'topic', 'country', 'city', 'language')


def get_recommendation_stations(language):
    """returns a list of 11 editor recommended stations"""
    __log('get_recommendation_stations started with language=%s' % language)
    path = 'broadcast/editorialreccomendationsembedded'
    gets = {}
    stations = __get_json(path, gets, language)
    __log('get_recommendation_stations end')
    return stations


def get_top_stations(language):
    """returns a list of the 100 most listened radio stations"""
    __log('get_top_stations started with language=%s' % language)
    path = 'menu/broadcastsofcategory'
    gets = {'category': '_top'}
    stations = __get_json(path, gets, language)
    __log('get_top_stations end')
    return stations


def get_most_wanted(language, num_entries=25):
    __log('get_most_wanted started with language=%s, num_entries=%d'
          % (language, num_entries))
    path = 'account/getmostwantedbroadcastlists'
    gets = {'sizeoflists': num_entries}
    stations_lists = __get_json(path, gets, language)
    __log('get_most_wanted end')
    return stations_lists


def get_category_types():
    """returns a list of possible values of category_types for
    get_categories_by_category_type(category_type)
    and get_stations_by_category(category_type, category_value)
    """
    __log('get_category_types end')
    return VALID_CATEGORY_TYPES


def get_categories_by_category_type(language, category_type):
    """returns a list of possible values of category for a given category_type
    usable for get_stations_by_category(category_type, category)
    """
    __log(('get_categories_by_category_type started with language=%s, '
           'category_type=%s') % (language, category_type))
    path = 'menu/valuesofcategory'
    if not category_type in get_category_types():
        raise
    gets = {'category': '_%s' % category_type}
    categories = __get_json(path, gets, language)
    __log('get_categories_by_category_type end')
    return categories


def get_stations_by_category(language, category_type, category_value):
    """returns a list of stations for a given category of category_type"""
    __log(('get_stations_by_category started with language=%s, '
           'category_type=%s, category_value=%s') % (language, category_type,
                                                     category_value))
    path = 'menu/broadcastsofcategory'
    if not category_type in get_category_types():
        raise
    if not category_value:
        raise
    gets = {'category': '_%s' % category_type,
            'value': category_value}
    stations = __get_json(path, gets, language)
    __log('get_stations_by_category end')
    return stations


def search_stations_by_string(language, search_string):
    """returns a list of stations for a given search_string.
    search in genresAndTopics, name, country"""
    __log(('search_stations_by_string started with language=%s, '
           'search_string=%s') % (language, search_string))
    path = 'index/searchembeddedbroadcast'
    if not search_string:
        raise
    gets = {'q': search_string,
            'start': 0,
            'rows': 10000}
    stations = __get_json(path, gets, language)
    __log('search_stations_by_string started')
    return stations


def get_station_by_station_id(language, station_id):
    """returns detailed informations (including stream url) of a given station
    by station_id
    """
    __log('get_station_by_station_id started with language=%s, station_id=%s'
          % (language, station_id))
    path = 'broadcast/getbroadcastembedded'
    gets = {'broadcast': station_id}
    station = __get_json(path, gets, language)
    if 'streamURL' in station:
        if station['streamURL'][-3:] in ('m3u', 'pls'):
            station['streamURL'] = __resolve_playlist(station['streamURL'])
        __log('get_station_by_station_id end')
        return station


def __get_json(path, gets, language):
    __log('__get_json started with path=%s, gets=%s, language=%s'
          % (path, gets, language))
    if not language in MAIN_URLS.keys():
        raise
    else:
        MAIN_URL = MAIN_URLS[language]
    if gets:
        full_url = '%s/%s?%s' % (MAIN_URL, path, urlencode(gets))
    else:
        full_url = '%s/%s' % (MAIN_URL, path)
    response = __urlopen(full_url)
    try:
        json_data = json.loads(response)
    except TypeError:
        json_data = None
    return json_data


def __resolve_playlist(playlist_url):
    __log('__resolve_playlist started with playlist_url=%s' % playlist_url)
    response = __urlopen(playlist_url)
    if not response:
        __log('__resolve_playlist failed')
        return playlist_url
    stream_url = None
    if playlist_url.endswith('m3u'):
        __log('__resolve_playlist found .m3u file')
        for entry in response.splitlines():
            if entry and not entry.strip().startswith('#'):
                stream_url = entry.strip()
                break
    elif playlist_url.endswith('pls'):
        __log('__resolve_playlist found .pls file')
        for line in response.splitlines():
            if line.strip().startswith('File1'):
                stream_url = line.split('=')[1]
                break
    if not stream_url:
        __log('__resolve_playlist falling back to playlist')
        stream_url = playlist_url
    __log('__resolve_playlist result=%s' % stream_url)
    return stream_url


def __urlopen(url):
    __log('__urlopen opening url=%s' % url)
    req = Request(url)
    req.add_header('User-Agent', USER_AGENT)
    try:
        response = urlopen(req).read()
    except HTTPError, error:
        __log('__urlopen HTTPError: %s' % error)
        return
    except URLError, error:
        __log('__urlopen URLError: %s' % error)
        return
    __log('__urlopen ended with %d bytes result' % len(response))
    return response


def __log(text):
    print 'Radio.de scraper: %s' % text
