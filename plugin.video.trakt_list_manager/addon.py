#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
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

import os
from xbmcswift2 import Plugin, xbmc, xbmcgui
from resources.lib.api import TraktListApi, AuthenticationError, \
    LIST_PRIVACY_IDS, NONE

API_KEY = '0e22ca9987e7f45b475bbde1ab2ce2d86396164ba8d57ba1a8c1cb644102b27e'
WATCHLIST_SLUG = 'WATCHLIST'  # hacky but reduces code amount...

CP_ADD_URL = 'plugin://plugin.video.couchpotato_manager/movies/add?imdb_id=%s'

STRINGS = {
    # Root menu entries
    'new_customlist': 30000,
    'add_movie': 30001,
    'show_watchlist': 30002,
    'show_customlists': 30003,
    # Context menu
    'addon_settings': 30100,
    'delete_customlist': 30101,
    'delete_movie': 30102,
    'movie_info': 30103,
    'add_to_cp': 30104,
    # Dialogs
    'enter_movie_title': 30110,
    'select_movie': 30111,
    'select_list': 30112,
    'delete_movie_head': 30113,
    'delete_movie_l1': 30114,
    'delete_customlist_head': 30115,
    'delete_customlist_l1': 30116,
    'watchlist': 30117,
    # Error dialogs
    'connection_error': 30120,
    'wrong_credentials': 30121,
    'want_set_now': 30122,
    # Noticications
    'no_movie_found': 30130,
    'success': 30131,
    # Help Dialog
    'help_head': 30140,
    'help_l1': 30141,
    'help_l2': 30142,
    'help_l3': 30143,
}

plugin = Plugin()

@plugin.route('/')
def show_root():
    items = [
        {'label': _('show_watchlist'),
         'path': plugin.url_for(endpoint='show_watchlist')},
        {'label': _('show_customlists'),
         'path': plugin.url_for(endpoint='show_customlists')},
    ]
    return plugin.finish(items)

@plugin.route('/customlists/')
def show_customlists():
    def context_menu(list_slug):
        return [
            (
                _('delete_customlist'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='delete_customlist',
                    list_slug=list_slug,
                    refresh='true',
                )
            ),
            (
                _('addon_settings'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='open_settings'
                )
            ),
        ]

    items = [{
        'label': '%s (%s)' % (trakt_list['name'], trakt_list['privacy']),
        'replace_context_menu': True,
        'context_menu': context_menu(
            list_slug=trakt_list['ids']['slug']
        ),
        'path': plugin.url_for(
            endpoint='show_customlist',
            list_slug=trakt_list['ids']['slug']
        )
    } for trakt_list in api.get_lists()]
    items.append({
        'label': _('new_customlist'),
        'path': plugin.url_for(
            endpoint='new_customlist',
            refresh='true',
        )
    })
    return plugin.finish(items)

@plugin.route('/customlists/<list_slug>/movies/')
def show_customlist(list_slug):
    def context_menu(list_slug, imdb_id, tmdb_id):
        return [
            (
                _('movie_info'),
                'XBMC.Action(Info)'
            ),
            (
                _('delete_movie'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='delete_movie_from_customlist',
                    list_slug=list_slug,
                    imdb_id=imdb_id,
                    tmdb_id=tmdb_id,
                    refresh='true',
                )
            ),
            (
                _('add_to_cp'),
                'XBMC.RunPlugin(%s)' % CP_ADD_URL % imdb_id
            ),
            (
                _('addon_settings'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='open_settings'
                )
            ),
        ]

    raw_movies = [item for item in api.get_list(list_slug) if item['type']=='movie']
    items = format_movies(raw_movies)
    for item in items:
        item['context_menu'] = context_menu(
            list_slug=list_slug,
            imdb_id=item['info'].get('code', NONE),
            tmdb_id=item.get('tmdb_id', NONE)
        )
    plugin.set_content('movies')
    items.append({
        'label': _('add_movie'),
        'info': {'count': len(items) + 1},
        'path': plugin.url_for(
            endpoint='add_movie_to_customlist',
            list_slug=list_slug,
            refresh=True,
        )
    })
    sort_methods = ['playlist_order', 'video_rating', 'video_year']
    return plugin.finish(items, sort_methods=sort_methods)

@plugin.route('/watchlist/movies/')
def show_watchlist():
    def context_menu(imdb_id, tmdb_id):
        return [
            (
                _('movie_info'),
                'XBMC.Action(Info)'
            ),
            (
                _('delete_movie'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='delete_movie_from_watchlist',
                    imdb_id=imdb_id,
                    tmdb_id=tmdb_id,
                    refresh='true',
                )
            ),
            (
                _('add_to_cp'),
                'XBMC.RunPlugin(%s)' % CP_ADD_URL % imdb_id
            ),
            (
                _('addon_settings'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='open_settings'
                )
            ),
        ]

    items = format_movies(api.get_watchlist())
    for item in items:
        item['context_menu'] = context_menu(
            imdb_id=item['info'].get('code', NONE),
            tmdb_id=item.get('tmdb_id', NONE)
        )
    items.append({
        'label': _('add_movie'),
        'info': {'count': len(items) + 1},
        'path': plugin.url_for(
            endpoint='add_movie_to_watchlist',
            refresh=True,
        )
    })
    return items

@plugin.route('/watchlist/movies/add')
def add_movie_to_watchlist():
    movie = get_movie()
    if movie:
        api.add_movie_to_watchlist(
            imdb_id=movie['ids']['imdb'],
            tmdb_id=movie['ids']['tmdb'])
        show_result()

@plugin.route('/watchlist/movies/delete/<imdb_id>/<tmdb_id>')
def delete_movie_from_watchlist(imdb_id, tmdb_id):
    confirmed = xbmcgui.Dialog().yesno(
        _('delete_movie_head'),
        _('delete_movie_l1')
    )
    if confirmed:
        api.del_movie_from_watchlist(
            imdb_id=imdb_id,
            tmdb_id=tmdb_id)
        show_result()

@plugin.route('/customlists/new')
def new_customlist():
    if 'title' in plugin.request.args:
        title = plugin.request.args['title'][0]
    else:
        title = plugin.keyboard(heading=_('enter_list_title'))
    if title:
        privacy_id = plugin.get_setting(
            'default_privacy',
            choices=LIST_PRIVACY_IDS
        )
        api.add_list(name=title,privacy_id=privacy_id)
        show_result()

@plugin.route('/customlists/<list_slug>/delete')
def delete_customlist(list_slug):
    confirmed = xbmcgui.Dialog().yesno(
        _('delete_customlist_head'),
        _('delete_customlist_l1')
    )
    if confirmed:
        api.del_list(list_slug)
        show_result()

@plugin.route('/movies/add')
def add_movie_to_list():
    movie = get_movie()
    if movie:
        default_list_slug = plugin.get_setting('default_list_slug', str)
        if default_list_slug:
            list_slug = default_list_slug
        else:
            list_to_add = ask_list()
            if not list_to_add:
                return
            list_slug = list_to_add['ids']['slug']
        if list_slug == WATCHLIST_SLUG:
            api.add_movie_to_watchlist(
                imdb_id=movie['ids']['imdb'],
                tmdb_id=movie['ids']['tmdb']
            )
            show_result()
        elif list_slug:
            api.add_movie_to_list(
                list_slug=list_slug,
                imdb_id=movie['ids']['imdb'],
                tmdb_id=movie['ids']['tmdb']
            )
            show_result()

@plugin.route('/customlists/<list_slug>/movies/add')
def add_movie_to_customlist(list_slug):
    movie = get_movie()
    if movie:
        api.add_movie_to_list(
            list_slug=list_slug,
            imdb_id=movie['ids']['imdb'],
            tmdb_id=movie['ids']['tmdb']
        )
        show_result()

@plugin.route('/customlists/<list_slug>/movies/delete/<imdb_id>/<tmdb_id>')
def delete_movie_from_customlist(list_slug, imdb_id, tmdb_id):
    confirmed = xbmcgui.Dialog().yesno(
        _('delete_movie_head'),
        _('delete_movie_l1')
    )
    if confirmed:
        api.del_movie_from_list(
            list_slug=list_slug,
            imdb_id=imdb_id,
            tmdb_id=tmdb_id
        )
        show_result()

def get_movie():
    movie = {
        'imdb_id': plugin.request.args.get('imdb_id', [''])[0],
        'tmdb_id': plugin.request.args.get('tmdb_id', [''])[0],
        'title': plugin.request.args.get('title', [''])[0],
    }
    if movie.get('imdb_id') or movie.get('tmdb_id'):
        return movie
    if not movie.get('title'):
        movie['title'] = plugin.keyboard(heading=_('enter_movie_title'))
    if not movie.get('title'):
        return
    movies = api.search_movie(movie['title'])
    if not movies:
        plugin.notify(msg=_('no_movie_found'))
        return
    items = [
        '%s (%s)' % (movie['movie']['title'], movie['movie']['year'])
        for movie in movies
    ]
    selected = xbmcgui.Dialog().select(
        _('select_movie'), items
    )
    if selected >= 0:
        return movies[selected]['movie']

def ask_list():
    customlists = api.get_lists()
    lists = [{'name': ('watchlist'), 'ids': {'slug': WATCHLIST_SLUG}}] + customlists
    selected = xbmcgui.Dialog().select(
        _('select_list'), [l['name'] for l in lists]
    )
    if selected >= 0:
        return lists[selected]

def show_result():
    #TODO: Consider how to catch & display results 
    icon_path = os.path.join(plugin.addon.getAddonInfo('path'), 'icon.png')
    plugin.notify(msg=_('success'), image=icon_path)
    if 'refresh' in plugin.request.args:
        xbmc.executebuiltin('Container.Refresh')
    
@plugin.route('/help')
def show_help():
    xbmcgui.Dialog().ok(
        _('help_head'),
        _('help_l1'),
        _('help_l2'),
        _('help_l3'),
    )

@plugin.route('/settings/default_list')
def set_default_list():
    default_list = ask_list()
    if default_list:
        plugin.set_setting('default_list', default_list['name'])
        plugin.set_setting('default_list_slug', default_list['ids']['slug'])
    else:
        plugin.set_setting('default_list', '')
        plugin.set_setting('default_list_slug', '')

@plugin.route('/settings')
def open_settings():
    plugin.open_settings()

@plugin.cached()
def get_xbmc_movies():
    import json
    query = {
        'jsonrpc': '2.0',
        'id': 0,
        'method': 'VideoLibrary.GetMovies',
        'params': {
            'properties': ['imdbnumber', 'file']
        }
    }
    response = json.loads(xbmc.executeJSONRPC(json.dumps(query)))
    movie_dict = dict(
        (movie['imdbnumber'], movie['file'])
        for movie in response.get('result', {}).get('movies', [])
    )
    return movie_dict

@plugin.route('/movie/<imdb_id>/play')
def play_movie(imdb_id):
    xbmc_movies = get_xbmc_movies()
    movie_file = xbmc_movies[imdb_id]
    return plugin.set_resolved_url(movie_file)

def format_movies(raw_movies):
    xbmc_movies = get_xbmc_movies()
    items = []
    for i, item in enumerate(raw_movies):
        movie = item['movie']
        ids=movie['ids']
        if ids.get('imdb', '') in xbmc_movies:
            label = u'[B]%s[/B]' % movie['title']
            path = plugin.url_for(
                endpoint='play_movie',
                imdb_id=ids['imdb']
            )
        else:
            label = movie['title']
            path = plugin.url_for(
                endpoint='show_help'
            )
        items.append({
            'label': label,
            'thumbnail': movie['images']['poster']['full'],
            'info': {
                'count': i,
                'code': ids.get('imdb', ''),
                'tmdb_id': ids.get('tmdb', ''),
                'year': movie.get('year', 0),
                'plot': movie.get('overview', ''),
                'mpaa': movie.get('certification', ''),
                #'genre': ', '.join(movie.get('genres', [])),
                'tagline': movie.get('tagline', ''),
                'playcount': movie.get('plays', 0),
                'rating': movie.get('ratings', {}).get('percentage', 0) / 10.0,
                'votes': movie.get('ratings', {}).get('votes', 0)
            },
            'stream_info': {
                'video': {'duration': movie.get('runtime', 0) * 60}
            },
            'replace_context_menu': True,
            'properties': {
                'fanart_image': movie['images']['fanart']['full'],
            },
            'is_playable': True,
            'path': path,
        })
    return items


def get_api():
    logged_in = False
    api = TraktListApi()
    while not logged_in:
        try:
            token = api.connect(
                username=plugin.get_setting('username', unicode),
                password=plugin.get_setting('password', unicode),
                token=plugin.get_setting('trakt_token', unicode),
                api_key=API_KEY,
                use_https=plugin.get_setting('use_https', bool),
            )
            plugin.set_setting('trakt_token', token)
            logged_in = True
        except AuthenticationError:
            token = ''
        
        if not token:
            try_again = xbmcgui.Dialog().yesno(
                _('connection_error'),
                _('wrong_credentials'),
                _('want_set_now')
            )
            if not try_again:
                return
            plugin.open_settings()
    return api

def log(text):
    plugin.log.info(text)

def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        log('String is missing: %s' % string_id)
        return string_id

if __name__ == '__main__':
    api = get_api()
    if api:
        plugin.run()
