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

from xbmcswift2 import Plugin, xbmc
from resources.lib.api import ShoutcastApi, NetworkError

plugin = Plugin()
api = ShoutcastApi('sh1t7hyn3Kh0jhlV')
my_stations = plugin.get_storage('my_stations.json', file_format='json')

STRINGS = {
    'all': 30000,
    'top500_stations': 30001,
    'browse_by_genre': 30002,
    'my_stations': 30003,
    'search_station': 30004,
    'search_current_track': 30005,
    'add_to_my_stations': 30010,
    'remove_from_my_stations': 30011,
    'network_error': 30200
}


@plugin.route('/')
def show_root_menu():
    items = (
        {'label': _('top500_stations'),
         'path': plugin.url_for('show_top500_stations')},
        {'label': _('browse_by_genre'),
         'path': plugin.url_for('show_genre')},
        {'label': _('search_station'),
         'path': plugin.url_for('search_station')},
        {'label': _('search_current_track'),
         'path': plugin.url_for('search_current_track')},
        {'label': _('my_stations'),
         'path': plugin.url_for('show_my_stations')},
    )
    return plugin.finish(items)


@plugin.route('/top500/')
def show_top500_stations():
    items = get_cached(api.get_top500_stations, TTL=60)
    return __add_stations(items)


@plugin.route('/genres/', name='show_genre')
@plugin.route('/genres/<parent_genre_id>/', name='show_subgenre')
def show_genre(parent_genre_id=None):
    show_subgenres = plugin.get_setting('show_subgenres', bool)
    genres = get_cached(api.get_genres, parent_genre_id, TTL=1440)
    items = []
    if show_subgenres and parent_genre_id:
        items.append({
            'label': '[[ %s ]]' % _('all'),
            'path': plugin.url_for(
                endpoint='show_stations',
                genre_id=str(parent_genre_id)
            )
        })
    for genre in genres:
        item = {'label': genre.get('name')}
        if show_subgenres and genre.get('has_childs'):
            item['path'] = plugin.url_for(
                endpoint='show_subgenre',
                parent_genre_id=str(genre['id'])
            )
        else:
            item['path'] = plugin.url_for(
                endpoint='show_stations',
                genre_id=str(genre['id'])
            )
        items.append(item)
    return plugin.finish(items)


@plugin.route('/stations/<genre_id>/')
def show_stations(genre_id):
    items = get_cached(api.get_stations, genre_id, TTL=60)
    return __add_stations(items)


@plugin.route('/resolve_playlist/<playlist_url>')
def resolve_playlist(playlist_url):
    stream_url = api.resolve_playlist(playlist_url)
    if stream_url:
        plugin.set_resolved_url(stream_url)
    else:
        plugin.set_resolved_url(playlist_url)


@plugin.route('/search/station/')
def search_station():
    search_string = plugin.keyboard(heading=_('search_station'))
    if search_string:
        url = plugin.url_for(
            endpoint='search_station_result',
            search_string=search_string
        )
        plugin.redirect(url)


@plugin.route('/search/station/<search_string>/')
def search_station_result(search_string):
    stations = api.search_stations(search_string)
    return __add_stations(stations)


@plugin.route('/search/current_track/')
def search_current_track():
    search_string = plugin.keyboard(heading=_('search_current_track'))
    if search_string:
        url = plugin.url_for(
            endpoint='search_current_track_result',
            search_string=search_string
        )
        plugin.redirect(url)


@plugin.route('/search/current_track/<search_string>/')
def search_current_track_result(search_string):
    stations = api.search_current_track(search_string)
    return __add_stations(stations)


@plugin.route('/my/')
def show_my_stations():
    stations = my_stations.values()
    return __add_stations(stations)


@plugin.route('/my/add/<station_id>/<station_name>')
def add_to_my_stations(station_id, station_name):
    station = api.get_station(station_id, station_name)
    my_stations[station_id] = station
    my_stations.sync()


@plugin.route('/my/del/<station_id>')
def del_from_my_stations(station_id):
    if station_id in my_stations:
        del my_stations[station_id]
        my_stations.sync()


def __add_stations(stations):
    addon_id = plugin._addon.getAddonInfo('id')
    icon = 'special://home/addons/%s/icon.png' % addon_id
    my_stations_ids = my_stations.keys()
    items = []
    show_bitrate = plugin.get_setting('show_bitrate_in_title', bool)
    choose_random = plugin.get_setting('choose_random_server', bool)
    if plugin.get_setting('bitrate_filter_enabled', bool):
        bitrates = (96, 128, 160, 192)
        min_bitrate = plugin.get_setting('bitrate_filter', choices=bitrates)
    else:
        min_bitrate = None
    for i, station in enumerate(stations):
        if min_bitrate and int(station.get('bitrate', 0)) < min_bitrate:
            continue
        station_id = str(station['id'])
        if not station_id in my_stations_ids:
            context_menu = [(
                _('add_to_my_stations'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='add_to_my_stations',
                    station_id=station_id,
                    station_name=station['name'].encode('utf-8')
                )
            )]
        else:
            context_menu = [(
                _('remove_from_my_stations'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='del_from_my_stations',
                    station_id=station_id
                )
            )]
        if show_bitrate and station.get('bitrate'):
            name = '%s  [%s kbps]' % (station['name'], station['bitrate'])
        else:
            name = station['name']
        item = {
            'label': name,
            'thumbnail': icon,
            'info': {
                'count': i,
                'genre': station.get('genre') or '',
                'size': station.get('bitrate') or 0,
                'listeners': station.get('listeners') or 0,
                'artist': station.get('current_track') or '',
                'tracknumber': station['id'],
                'comment': station.get('media_type') or ''
            },
            'context_menu': context_menu,
            'is_playable': True,
            'path': plugin.url_for(
                endpoint='resolve_playlist',
                playlist_url=station['playlist_url']
            )
        }
        if choose_random:
            item['path'] = plugin.url_for(
                endpoint='resolve_playlist',
                playlist_url=station['playlist_url']
            )
        else:
            item['path'] = station['playlist_url']
            item['properties'] = [('mimetype', 'audio/x-scpls'), ]
        items.append(item)
    finish_kwargs = {
        'sort_methods': [
            'LISTENERS',
            'BITRATE',
            ('LABEL', '%X'),
        ],
    }
    return plugin.finish(items, **finish_kwargs)


def get_cached(func, *args, **kwargs):
    '''Return the result of func with the given args and kwargs
    from cache or execute it if needed'''
    @plugin.cached(kwargs.pop('TTL', 1440))
    def wrap(func_name, *args, **kwargs):
        return func(*args, **kwargs)
    return wrap(func.__name__, *args, **kwargs)


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


if __name__ == '__main__':
    limit = plugin.get_setting('limit', int)
    api.set_limit(limit)
    try:
        plugin.run()
    except NetworkError:
        plugin.notify(msg=_('network_error'))
