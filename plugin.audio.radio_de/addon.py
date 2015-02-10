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
from xbmcswift2 import Plugin, xbmc
from resources.lib.api import RadioApi, RadioApiError

STRINGS = {
    'editorials_recommendations': 30100,
    'top_100_stations': 30101,
    'browse_by_genre': 30102,
    'browse_by_topic': 30103,
    'browse_by_country': 30104,
    'browse_by_city': 30105,
    'browse_by_language': 30106,
    'local_stations': 30107,
    'my_stations': 30108,
    'search_for_station': 30200,
    'enter_name_country_or_language': 30201,
    'add_to_my_stations': 30400,
    'remove_from_my_stations': 30401,
    'edit_custom_station': 30402,
    'please_enter': 30500,
    'name': 30501,
    'thumbnail': 30502,
    'stream_url': 30503,
    'add_custom': 30504
}


plugin = Plugin()
radio_api = RadioApi()
my_stations = plugin.get_storage('my_stations.json', file_format='json')


@plugin.route('/')
def show_root_menu():
    items = (
        {'label': _('local_stations'),
         'path': plugin.url_for('show_local_stations')},
        {'label': _('editorials_recommendations'),
         'path': plugin.url_for('show_recommendation_stations')},
        {'label': _('top_100_stations'),
         'path': plugin.url_for('show_top_stations')},
        {'label': _('browse_by_genre'),
         'path': plugin.url_for('show_station_categories',
                                category_type='genre')},
        {'label': _('browse_by_topic'),
         'path': plugin.url_for('show_station_categories',
                                category_type='topic')},
        {'label': _('browse_by_country'),
         'path': plugin.url_for('show_station_categories',
                                category_type='country')},
        {'label': _('browse_by_city'),
         'path': plugin.url_for('show_station_categories',
                                category_type='city')},
        {'label': _('browse_by_language'),
         'path': plugin.url_for('show_station_categories',
                                category_type='language')},
        {'label': _('search_for_station'),
         'path': plugin.url_for('search')},
        {'label': _('my_stations'),
         'path': plugin.url_for('show_my_stations')},
    )
    return plugin.finish(items)


@plugin.route('/stations/local/')
def show_local_stations():
    stations = radio_api.get_local_stations()
    return __add_stations(stations)


@plugin.route('/stations/recommended/')
def show_recommendation_stations():
    stations = radio_api.get_recommendation_stations()
    return __add_stations(stations)


@plugin.route('/stations/top/')
def show_top_stations():
    stations = radio_api.get_top_stations()
    return __add_stations(stations)


@plugin.route('/stations/search/')
def search():
    query = plugin.keyboard(heading=_('enter_name_country_or_language'))
    if query:
        url = plugin.url_for('search_result', search_string=query)
        plugin.redirect(url)


@plugin.route('/stations/search/<search_string>/')
def search_result(search_string):
    stations = radio_api.search_stations_by_string(search_string)
    return __add_stations(stations)


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
    station_id = station_name.decode('ascii', 'ignore').encode('ascii')
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


@plugin.route('/stations/<category_type>/')
def show_station_categories(category_type):
    categories = radio_api.get_categories(category_type)
    items = []
    for category in categories:
        category = category.encode('utf-8')
        items.append({
            'label': category,
            'path': plugin.url_for(
                'show_stations_by_category',
                category_type=category_type,
                category=category,
            ),
        })
    return plugin.finish(items)


@plugin.route('/stations/<category_type>/<category>/')
def show_stations_by_category(category_type, category):
    stations = radio_api.get_stations_by_category(category_type,
                                                  category)
    return __add_stations(stations)


@plugin.route('/station/<station_id>')
def get_stream_url(station_id):
    if my_stations.get(station_id, {}).get('is_custom', False):
        stream_url = my_stations[station_id]['stream_url']
    else:
        station = radio_api.get_station_by_station_id(station_id)
        stream_url = station['stream_url']
    __log('get_stream_url result: %s' % stream_url)
    return plugin.set_resolved_url(stream_url)


def __add_stations(stations, add_custom=False):
    __log('__add_stations started with %d items' % len(stations))
    items = []
    my_station_ids = my_stations.keys()
    for i, station in enumerate(stations):
        station_id = str(station['id'])
        if not station_id in my_station_ids:
            context_menu = [(
                _('add_to_my_stations'),
                'XBMC.RunPlugin(%s)' % plugin.url_for('add_to_my_stations',
                                                      station_id=station_id),
            )]
        else:
            context_menu = [(
                _('remove_from_my_stations'),
                'XBMC.RunPlugin(%s)' % plugin.url_for('del_from_my_stations',
                                                      station_id=station_id),
            )]
        if station.get('is_custom', False):
            context_menu.append((
                _('edit_custom_station'),
                'XBMC.RunPlugin(%s)' % plugin.url_for('custom_my_station',
                                                      station_id=station_id),
            ))
        items.append({
            'label': station.get('name', ''),
            'thumbnail': station['thumbnail'],
            'info': {
                'title': station.get('name', ''),
                'rating': str(station.get('rating', '0.0')),
                'genre': station.get('genre', ''),
                'size': int(station.get('bitrate', 0)),
                'comment': station.get('current_track', ''),
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
    finish_kwargs = {
        'sort_methods': [
            ('UNSORTED', '%X'),
            ('TITLE', '%X'),
            'SONG_RATING',
        ],
    }
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


def __get_language():
    languages = ('english', 'german', 'french')
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


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        __log('String is missing: %s' % string_id)
        return string_id

if __name__ == '__main__':
    radio_api.set_language(__get_language())
    radio_api.log = __log
    try:
        plugin.run()
    except RadioApiError:
        plugin.notify(msg=_('network_error'))
