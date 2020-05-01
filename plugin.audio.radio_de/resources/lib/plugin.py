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
from xbmcswift2 import Plugin, xbmc, listitem
from resources.lib.api import RadioApi, RadioApiError, PY3

STRINGS = {
    'editorials_recommendations': 30100,
    'top_stations': 30101,
    'browse_by_genre': 30102,
    'browse_by_topic': 30103,
    'browse_by_country': 30104,
    'browse_by_city': 30105,
    'browse_by_language': 30106,
    'local_stations': 30107,
    'my_stations': 30108,
    'search_for_station': 30200,
    'add_to_my_stations': 30400,
    'remove_from_my_stations': 30401,
    'edit_custom_station': 30402,
    'please_enter': 30500,
    'name': 30501,
    'thumbnail': 30502,
    'stream_url': 30503,
    'add_custom': 30504,
    'most_popular': 30603,
    'az': 30604,
    'next_page': 30605,
    'by_country': 30606
}

SORT_TYPES = {
    'popular': 'RANK',
    'az': 'STATION_NAME'
}

STATIONS_PER_PAGE = 50

plugin = Plugin()
radio_api = RadioApi()
my_stations = plugin.get_storage('my_stations.json', file_format='json')


@plugin.route('/')
def show_root_menu():
    items = (
        {'label': _('local_stations'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for('show_local_stations', page=1)},
        {'label': _('editorials_recommendations'),  'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for('show_recommendation_stations')},
        {'label': _('top_stations'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for('show_top_stations', page=1)},
        {'label': _('browse_by_genre'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for('show_genres')},
        {'label': _('browse_by_topic'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for('show_topics')},
        {'label': _('browse_by_country'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for('show_countries')},
        {'label': _('browse_by_city'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for('show_cities_submenu')},
        {'label': _('browse_by_language'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for('show_languages')},
        {'label': _('search_for_station'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for('search')},
        {'label': _('my_stations'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for('show_my_stations')},
    )
    return plugin.finish(items)


@plugin.route('/stations/local/<page>')
def show_local_stations(page=1):
    total_pages, stations = radio_api.get_stations_nearby(STATIONS_PER_PAGE, page)

    next_page = None
    if int(page) < (total_pages):
        next_page = {
            'url': plugin.url_for(
                'show_local_stations',
                page = int(page) + 1),
            'page': page,
            'total_pages': total_pages,
            'icon': plugin.icon,
            'fanart': __get_plugin_fanart()
        }

    return __add_stations(stations, browse_more=next_page)


@plugin.route('/stations/recommended')
def show_recommendation_stations():
    stations = radio_api.get_recommendation_stations()
    return __add_stations(stations)


@plugin.route('/stations/top/<page>')
def show_top_stations(page=1):
    total_pages, stations = radio_api.get_top_stations(STATIONS_PER_PAGE, page)
    next_page = None
    if int(page) < (total_pages):
        next_page = {
            'url': plugin.url_for(
                'show_top_stations',
                page = int(page) + 1),
            'page': page,
            'total_pages': total_pages,
            'icon': plugin.icon,
            'fanart': __get_plugin_fanart()
        }
    return __add_stations(stations, browse_more=next_page)


@plugin.route('/stations/search/')
def search():
    query = plugin.keyboard(heading=_('search_for_station'))
    if query:
        url = plugin.url_for('search_result', search_string=query, page=1)
        plugin.redirect(url)


@plugin.route('/stations/search/<search_string>/<page>')
def search_result(search_string, page):
    total_pages, stations = radio_api.search_stations_by_string(search_string, STATIONS_PER_PAGE, page)
    next_page = None
    if int(page) < (total_pages):
        next_page = {
            'url': plugin.url_for(
                'search_result',
                search_string = search_string,
                page = int(page) + 1),
            'page': page,
            'total_pages': total_pages,
            'icon': plugin.icon,
            'fanart': __get_plugin_fanart()
        }
    return __add_stations(stations, browse_more=next_page)


@plugin.route('/stations/my/')
def show_my_stations():
    stations = my_stations.values()
    return __add_stations(stations, add_custom=True)


@plugin.route('/stations/my/custom/<station_id>')
def custom_my_station(station_id):
    if station_id == 'new':
        station = {}
    else:
        stations = my_stations.values()
        station = [s for s in stations if s['id'] == station_id][0]
    for param in ('name', 'thumbnail', 'stream_url'):
        heading = _('please_enter') % _(param)
        station[param] = plugin.keyboard(station.get(param, ''), heading) or ''
    station_name = station.get('name', 'custom')
    station_id = station_name if PY3 else station_name.decode('ascii', 'ignore').encode('ascii')
    station['id'] = station_id
    station['is_custom'] = '1'
    if station_id:
        my_stations[station_id] = station
        url = plugin.url_for('show_my_stations')
        plugin.redirect(url)


@plugin.route('/stations/my/add/<station_id>')
def add_to_my_stations(station_id):
    station = radio_api.get_station_by_station_id(station_id)
    my_stations[station_id] = station
    my_stations.sync()


@plugin.route('/stations/my/del/<station_id>')
def del_from_my_stations(station_id):
    if station_id in my_stations:
        del my_stations[station_id]
        my_stations.sync()


@plugin.route('/stations/genres')
def show_genres():
    genres = radio_api.get_genres()
    items = []
    for genre in genres:
        items.append({
            'label': __encode(genre["systemEnglish"]),
            'icon': plugin.icon,
            'fanart': __get_plugin_fanart(),
            'path': plugin.url_for(
                'show_popular_and_az',
                category='genres',
                value=__encode(genre["systemEnglish"])
            ),
        })
    finish_kwargs = {
        'sort_methods': [
            ('LABEL', '%X'),
        ],
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/stations/topics')
def show_topics():
    topics = radio_api.get_topics()
    items = []
    for topic in topics:
        items.append({
            'label': __encode(topic["systemEnglish"]),
            'icon': plugin.icon,
            'fanart': __get_plugin_fanart(),
            'path': plugin.url_for(
                'show_popular_and_az',
                category='topics',
                value=__encode(topic["systemEnglish"])
            ),
        })
    finish_kwargs = {
        'sort_methods': [
            ('LABEL', '%X'),
        ],
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/stations/countries')
def show_countries():
    countries = radio_api.get_countries()
    items = []
    for country in countries:
        items.append({
            'label': __encode(country["systemEnglish"]),
            'icon': plugin.icon,
            'fanart': __get_plugin_fanart(),
            'path': plugin.url_for(
                'show_popular_and_az',
                category='countries',
                value=__encode(country["systemEnglish"])
            ),
        })
    finish_kwargs = {
        'sort_methods': [
            ('LABEL', '%X'),
        ],
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/menu/languages')
def show_languages():
    languages = radio_api.get_languages()
    items = []
    for lang in languages:
        items.append({
            'label': __encode(lang["systemEnglish"]),
            'icon': plugin.icon,
            'fanart': __get_plugin_fanart(),
            'path': plugin.url_for(
                'show_popular_and_az',
                category='languages',
                value=__encode(lang["systemEnglish"])
            ),
        })
    finish_kwargs = {
        'sort_methods': [
            ('LABEL', '%X'),
        ],
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/menu/cities')
def show_cities_submenu():
    items = (
        {'label': _('by_country'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for(
             'show_cities_list',
             option = 'country')},
        {'label': _('az'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for(
             'show_cities_list',
             option = 'az')}
    )
    finish_kwargs = {
        'sort_methods': [
            ('LABEL', '%X'),
        ],
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/menu/cities/select/<option>')
def show_cities_list(option):
    items = []
    if option == "country":
        countries = radio_api.get_countries()
        for country in countries:
            items.append({
                'label': __encode(country["systemEnglish"]),
                'icon': plugin.icon,
                'fanart': __get_plugin_fanart(),
                'path': plugin.url_for(
                    'show_cities_by_country',
                    country = __encode(country["systemEnglish"]),
                ),
            })
    else:
        cities = radio_api.get_cities()
        for city in cities:
            items.append({
                'label': __encode(city["systemEnglish"]),
                'icon': plugin.icon,
                'fanart': __get_plugin_fanart(),
                'path': plugin.url_for(
                    'show_popular_and_az',
                    category = 'cities',
                    value = __encode(city["systemEnglish"]),
                ),
            })
    finish_kwargs = {
        'sort_methods': [
            ('LABEL', '%X'),
        ],
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/menu/cities/list/<country>')
def show_cities_by_country(country):
    items = []
    cities = radio_api.get_cities(country=country)
    for city in cities:
        items.append({
            'label': __encode(city["systemEnglish"]),
            'icon': plugin.icon,
            'fanart': __get_plugin_fanart(),
            'path': plugin.url_for(
                'show_popular_and_az',
                category = 'cities',
                value = __encode(city["systemEnglish"]),
            )
        })
    finish_kwargs = {
        'sort_methods': [
            ('LABEL', '%X'),
        ],
    }
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/menu/<category>/<value>')
def show_popular_and_az(category, value):
    items = (
        {'label': _('most_popular'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for(
             'sub_menu_entry',
             option = 'popular',
             category = category,
             value = value,
             page = 1)},
        {'label': _('az'), 'icon': plugin.icon,
         'fanart': __get_plugin_fanart(),
         'path': plugin.url_for(
             'sub_menu_entry',
             option = 'az',
             category=category,
             value = value,
             page=1)}
    )
    finish_kwargs = {
        'sort_methods': [
            ('LABEL', '%X'),
        ],
    }
    return plugin.finish(items, **finish_kwargs)

@plugin.route('/stations/city/<city>/<option>/<page>')
def list_stations_by_city(city, option, page=1):
    total_pages, stations = radio_api.get_stations_by_city(
            city,
            SORT_TYPES[option],
            STATIONS_PER_PAGE,
            page)
    next_page = None
    if int(page) < (total_pages):
        next_page = {
            'url': plugin.url_for(
                'list_stations_by_city',
                city = city,
                option= option,
                page = int(page) + 1),
            'page': page,
            'total_pages': total_pages,
            'icon': plugin.icon,
            'fanart': __get_plugin_fanart()
        }
    return __add_stations(stations, browse_more=next_page)


@plugin.route('/stations/<option>/<category>/<value>/<page>')
def sub_menu_entry(option, category, value, page=1):
    if category == 'genres':
        total_pages, stations = radio_api.get_stations_by_genre(
            value,
            SORT_TYPES[option],
            STATIONS_PER_PAGE,
            page)

    elif category == 'countries':
        total_pages, stations = radio_api.get_stations_by_country(
            value,
            SORT_TYPES[option],
            STATIONS_PER_PAGE,
            page)

    elif category == 'cities':
        total_pages, stations = radio_api.get_stations_by_city(
            value,
            SORT_TYPES[option],
            STATIONS_PER_PAGE,
            page)

    elif category == 'topics':
        total_pages, stations = radio_api.get_stations_by_topic(
            value,
            SORT_TYPES[option],
            STATIONS_PER_PAGE,
            page)

    elif category == 'languages':
        total_pages, stations = radio_api.get_stations_by_language(
            value,
            SORT_TYPES[option],
            STATIONS_PER_PAGE,
            page)

    next_page = None
    if int(page) < (total_pages):
        next_page = {
            'url': plugin.url_for(
                'sub_menu_entry',
                option = option,
                category = category,
                value = value,
                page = int(page) + 1),
            'page': page,
            'total_pages': total_pages,
            'icon': plugin.icon,
            'fanart': __get_plugin_fanart()
        }
    return __add_stations(stations, browse_more=next_page)


@plugin.route('/station/<station_id>')
def get_stream_url(station_id):
    if my_stations.get(station_id, {}).get('is_custom', False):
        station = my_stations[station_id]
        stream_url = radio_api.internal_resolver(station)
        current_track = ''
    else:
        station = radio_api.get_station_by_station_id(
            station_id,
            force_http=plugin.get_setting('prefer-http', bool)
        )
        if station:
            stream_url = station['stream_url']
            current_track = station['current_track']
    if station:
        __log('get_stream_url result: %s' % stream_url)
        return plugin.set_resolved_url(
            listitem.ListItem(
                label=station['name'],
                label2=current_track,
                path=stream_url,
                icon=station['thumbnail'],
                thumbnail=station['thumbnail'],
                fanart=__get_plugin_fanart(),
            )
        )


def __add_stations(stations, add_custom=False, browse_more=None):
    items = []
    my_station_ids = my_stations.keys()
    for i, station in enumerate(stations):
        station_id = str(station['id'])
        if not station_id in my_station_ids:
            context_menu = [(
                _('add_to_my_stations'),
                'RunPlugin(%s)' % plugin.url_for('add_to_my_stations',
                                                      station_id=station_id),
            )]
        else:
            context_menu = [(
                _('remove_from_my_stations'),
                'RunPlugin(%s)' % plugin.url_for('del_from_my_stations',
                                                      station_id=station_id),
            )]
        if station.get('is_custom', False):
            context_menu.append((
                _('edit_custom_station'),
                'RunPlugin(%s)' % plugin.url_for('custom_my_station',
                                                      station_id=station_id),
            ))

        items.append({
            'label': station.get('name', ''),
            'thumbnail': station['thumbnail'],
            'fanart': __get_plugin_fanart(),
            'info': {
                'title': station.get('name', ''),
                'rating': (10.0 - 0.0)*((float(station.get('rating', 0.0))-30.000)/(1.0-30.000)), # linear interpolation
                'genre': station.get('genre', ''),
                'size': int(station.get('bitrate', 0)),
                'comment': station.get('description', ''),
                'count': i,
            },
            'context_menu': context_menu,
            'path': plugin.url_for(
                'get_stream_url',
                station_id=station_id,
            ),
            'is_playable': True,
        })
    if add_custom:
        items.append({
            'label': _('add_custom'),
            'path': plugin.url_for('custom_my_station', station_id='new'),
        })

    if browse_more:
        items.append({
            'label': '[B]%s[/B]' % _('next_page') % (browse_more['page'], browse_more['total_pages']),
            'path': browse_more['url'],
            'icon': browse_more['icon'],
            'fanart': browse_more['fanart']
        })


    finish_kwargs = {
        'sort_methods': [
            ('UNSORTED', '%X'),
            ('TITLE', '%X'),
            'SONG_RATING',
        ],
    }

    plugin.set_content('songs')

    return plugin.finish(items, **finish_kwargs)


def __get_language():
    languages = ('english', 'german', 'french', 'portuguese', 'spanish')
    if not plugin.get_setting('not_first_run', str):
        xbmc_language = xbmc.getLanguage().lower()
        __log('__get_language has first run with xbmc_language=%s'
              % xbmc_language)
        for i, lang in enumerate(languages):
            if xbmc_language.lower().startswith(lang):
                plugin.set_setting('language', str(i))
                __log('__get_language detected: %s' % languages[i])
                break
        plugin.set_setting('not_first_run', '1')
    return plugin.get_setting('language', choices=languages)


def __log(text):
    plugin.log.info(text)


def __get_plugin_fanart():
    return plugin.fanart if not plugin.get_setting('hide-fanart', bool) else ''

def __encode(string):
    if PY3:
        return string
    return string.encode('utf-8')

def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        __log('String is missing: %s' % string_id)
        return string_id


def run():
    radio_api.set_language(__get_language())
    radio_api.log = __log
    try:
        plugin.run()
    except RadioApiError:
        plugin.notify(msg=_('network_error'))
