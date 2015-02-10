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
from resources.lib.api import \
    ItunesPodcastApi, NetworkError, NoEnclosureException

plugin = Plugin()
api = ItunesPodcastApi()
my_podcasts = plugin.get_storage('my_podcasts.json', file_format='json')

STRINGS = {
    'all': 30000,
    'browse_by_genre': 30002,
    'show_my_podcasts': 30003,
    'search_podcast': 30004,
    'video': 30005,
    'audio': 30006,
    'add_to_my_podcasts': 30010,
    'remove_from_my_podcasts': 30011,
    'network_error': 30200,
    'no_media_found': 30007,
}


@plugin.route('/')
def show_root():
    content_type = plugin.request.args.get('content_type')
    if not content_type:
        url = plugin.url_for(endpoint='show_content_types')
        return plugin.redirect(url)
    if isinstance(content_type, (list, tuple)):
        content_type = content_type[0]
    items = (
        {'label': _('browse_by_genre'), 'path': plugin.url_for(
            endpoint='show_genres',
            content_type=content_type
        )},
        {'label': _('show_my_podcasts'), 'path': plugin.url_for(
            endpoint='show_my_podcasts',
            content_type=content_type
        )},
        {'label': _('search_podcast'), 'path': plugin.url_for(
            endpoint='search',
            content_type=content_type
        )},
    )
    return plugin.finish(items)


@plugin.route('/content_types/')
def show_content_types():
    items = (
        {'label': _('video'), 'path': plugin.url_for(
            endpoint='show_root',
            content_type='video'
        )},
        {'label': _('audio'), 'path': plugin.url_for(
            endpoint='show_root',
            content_type='audio'
        )}
    )
    return plugin.finish(items)


@plugin.route('/<content_type>/genres/')
def show_genres(content_type):
    show_subgenres = plugin.get_setting('show_subgenres', bool)
    genres = api.get_genres(flat=show_subgenres)
    items = []
    for genre in genres:
        if genre['name'] == 'Podcasts':
            genre['name'] = _('all')
        item = {
            'label': genre['name'],
            'path': plugin.url_for(
                endpoint='show_podcasts',
                content_type=content_type,
                genre_id=genre['id']
            )
        }
        items.append(item)
    return plugin.finish(items)


@plugin.route('/<content_type>/podcasts/by-genre/<genre_id>/')
def show_podcasts(content_type, genre_id):
    num_podcasts_list = plugin.get_setting('num_podcasts_list', int)
    podcasts = api.get_podcasts(
        content_type=content_type,
        genre_id=genre_id,
        limit=num_podcasts_list
    )
    return __add_podcasts(content_type, podcasts)


@plugin.route('/<content_type>/podcast/items/<podcast_id>/')
def show_items(content_type, podcast_id):
    try:
        podcast_items = api.get_podcast_items(
            podcast_id=podcast_id
        )
    except NoEnclosureException:
        plugin.notify(msg=_('no_media_found'))
        return plugin.finish(succeeded=False)
    return __add_podcast_items(content_type, podcast_id, podcast_items)


@plugin.route('/<content_type>/podcast/items/<podcast_id>/<item_url>')
def watch_item(content_type, podcast_id, item_url):
    return plugin.set_resolved_url(item_url)


@plugin.route('/<content_type>/podcasts/my/')
def show_my_podcasts(content_type):
    podcasts = my_podcasts.get(content_type, {}).values()
    return __add_podcasts(content_type, podcasts)


@plugin.route('/<content_type>/podcasts/my/add/<podcast_id>')
def add_to_my_podcasts(content_type, podcast_id):
    podcast = api.get_single_podcast(podcast_id=podcast_id)
    if not content_type in my_podcasts:
        my_podcasts[content_type] = {}
    my_podcasts[content_type][podcast_id] = podcast
    my_podcasts.sync()


@plugin.route('/<content_type>/podcasts/my/del/<podcast_id>')
def del_from_my_podcasts(content_type, podcast_id):
    if podcast_id in my_podcasts.get(content_type, {}):
        del my_podcasts[content_type][podcast_id]
        my_podcasts.sync()


@plugin.route('/<content_type>/podcasts/search/')
def search(content_type):
    search_string = plugin.keyboard(heading=_('search'))
    if search_string:
        url = plugin.url_for(
            endpoint='search_result',
            content_type=content_type,
            search_string=search_string
        )
        plugin.redirect(url)


@plugin.route('/<content_type>/podcasts/search/<search_string>/')
def search_result(content_type, search_string):
    num_podcasts_search = plugin.get_setting('num_podcasts_search', int)
    podcasts = api.search_podcast(
        search_term=search_string,
        limit=num_podcasts_search
    )
    return __add_podcasts(content_type, podcasts)


def __add_podcasts(content_type, podcasts):
    my_podcasts_ids = my_podcasts.get(content_type, {}).keys()
    items = []
    for i, podcast in enumerate(podcasts):
        podcast_id = str(podcast['id'])
        if not podcast_id in my_podcasts_ids:
            context_menu = [(
                _('add_to_my_podcasts'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='add_to_my_podcasts',
                    content_type=content_type,
                    podcast_id=podcast_id
                )
            )]
        else:
            context_menu = [(
                _('remove_from_my_podcasts'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='del_from_my_podcasts',
                    content_type=content_type,
                    podcast_id=podcast_id
                )
            )]
        item = {
            'label': podcast['name'],
            'thumbnail': podcast['thumb'],
            'info': {
                'title': podcast['name'],
                'count': i,
                'plot': podcast['summary'] or '',
                'studio': podcast['author'] or '',
                'genre': podcast['genre'] or '',
                'tagline': podcast['rights'] or '',
                'date': podcast['release_date'] or ''
            },
            'context_menu': context_menu,
            'path': plugin.url_for(
                endpoint='show_items',
                content_type=content_type,
                podcast_id=podcast_id
            )
        }
        items.append(item)
    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'TITLE', 'DATE')
    }
    if plugin.get_setting('force_viewmode_podcasts', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


def __add_podcast_items(content_type, podcast_id, podcast_items):
    items = [{
        'label': item['title'],
        'thumbnail': item['thumb'],
        'info': {
            'title': item['title'],
            'count': i,
            'plot': item['summary'] or '',
            'studio': item['author'] or '',
            'size': item['size'] or 0,
            'date': item['pub_date'] or '',
            'tagline': item['rights'] or ''
        },
        'path': plugin.url_for(
            endpoint='watch_item',
            content_type=content_type,
            podcast_id=podcast_id,
            item_url=item['item_url'].encode('utf-8')
        ),
        'is_playable': True
    } for i, item in enumerate(podcast_items)]
    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'TITLE', 'DATE', 'SIZE')
    }
    if plugin.get_setting('force_viewmode_items', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


def __get_country():
    if not plugin.get_setting('country_already_set'):
        lang_country_mapping = (
            ('chin', 'CN'),
            ('denm', 'DK'),
            ('fin', 'FI'),
            ('fre', 'FR'),
            ('germa', 'DE'),
            ('greec', 'GR'),
            ('ital', 'IT'),
            ('japa', 'JP'),
            ('kor', 'KR'),
            ('dutch', 'NL'),
            ('norw', 'NO'),
            ('pol', 'PL'),
            ('port', 'PT'),
            ('roma', 'RO'),
            ('russ', 'RU'),
            ('span', 'ES'),
            ('swed', 'SE'),
            ('turk', 'TR'),
            ('engl', 'US')
        )
        country = None
        xbmc_language = xbmc.getLanguage().lower()
        for lang, country_code in lang_country_mapping:
            if xbmc_language.startswith(lang):
                country = country_code
                plugin.set_setting('country', country)
                break
        if not country:
            plugin.open_settings()
    country = plugin.get_setting('country') or 'US'
    plugin.set_setting('country_already_set', '1')
    return country


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


if __name__ == '__main__':
    country = __get_country()
    api.set_country(country=country)
    try:
        plugin.run()
    except NetworkError:
        plugin.notify(msg=_('network_error'))
