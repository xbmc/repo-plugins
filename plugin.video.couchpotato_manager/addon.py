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

from xbmcswift2 import Plugin, xbmc, xbmcgui
from resources.lib.api import \
    CouchPotatoApi, AuthenticationError, ConnectionError

STRINGS = {
    # Root menu
    'all_movies': 30000,
    'add_new_wanted': 30001,
    'wanted_movies': 30002,
    'done_movies': 30003,
    'status_list': 30004,
    # Context menu
    'addon_settings': 30100,
    'refresh_releases': 30101,
    'delete_movie': 30102,
    'delete_release': 30103,
    'download_release': 30104,
    'ignore_release': 30105,
    'youtube_trailer': 30106,
    'full_refresh': 30107,
    # Dialogs
    'enter_movie_title': 30110,
    'select_movie': 30111,
    'select_profile': 30112,
    'delete_movie_head': 30113,
    'delete_movie_l1': 30114,
    'select_default_profile': 30115,
    # Error dialogs
    'connection_error': 30120,
    'wrong_credentials': 30121,
    'wrong_network': 30122,
    'want_set_now': 30123,
    # Noticications
    'wanted_added': 30130,
    'no_movie_found': 30131,
    'success': 30132,
    # Help Dialog
    'release_help_head': 30140,
    'release_help_l1': 30141,
    'release_help_l2': 30142,
    'release_help_l3': 30143,
    # Labels in Plot:
    'type': 30150,
    'provider': 30151,
    'provider_extra': 30152,
    'age': 30153,
    'seed_leech': 30154,
    'size_mb': 30155,
    'description': 30156,
}

YT_TRAILER_URL = (
    'plugin://plugin.video.youtube/'
    '?path=/root/search&feed=search&search=%s+Trailer'
)


plugin = Plugin()


@plugin.cached()
def get_status_list():
    return api.get_status_list()


@plugin.route('/')
def show_root_menu():
    def context_menu():
        return [
            (
                _('addon_settings'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='open_settings'
                )
            ),
        ]

    def context_menu_wanted():
        return [
            (
                _('full_refresh'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='do_full_refresh'
                )
            ),
        ]

    items = [
        {'label': _('add_new_wanted'),
         'replace_context_menu': True,
         'context_menu': context_menu(),
         'path': plugin.url_for(endpoint='add_new_wanted')},
        {'label': _('all_movies'),
         'replace_context_menu': True,
         'context_menu': context_menu(),
         'path': plugin.url_for(endpoint='show_all_movies')},
        {'label': _('wanted_movies'),
         'replace_context_menu': True,
         'context_menu': context_menu_wanted(),
         'path': plugin.url_for(endpoint='show_movies', status='active')},
        {'label': _('done_movies'),
         'replace_context_menu': True,
         'context_menu': context_menu(),
         'path': plugin.url_for(endpoint='show_movies', status='done')},
        # {'label': _('status_list'),
        #  'replace_context_menu': True,
        #  'context_menu': context_menu(),
        #  'path': plugin.url_for(endpoint='show_status_list')},
    ]
    return plugin.finish(items)


@plugin.route('/status_list/')
def show_status_list():
    def context_menu():
        return [
            (
                _('addon_settings'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='open_settings'
                )
            ),
        ]
    items = []
    for status in get_status_list():
        items.append({
            'label': status['label'],
            'replace_context_menu': True,
            'context_menu': context_menu(),
            'path': plugin.url_for(
                endpoint='show_movies',
                status=status['identifier']
            )
        })
    return plugin.finish(items)


@plugin.route('/movies/', name='show_all_movies', options={'status': None})
@plugin.route('/movies/status/<status>/')
def show_movies(status):
    def context_menu(movie_id, movie_title):
        return [
            (
                _('refresh_releases'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='refresh_releases',
                    library_id=movie_id
                )
            ),
            (
                _('delete_movie'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='delete_movie',
                    library_id=movie_id
                )
            ),
            (
                _('youtube_trailer'),
                'XBMC.Container.Update(%s)' % YT_TRAILER_URL % movie_title
            ),
            (
                _('addon_settings'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='open_settings'
                )
            ),
        ]

    def get_status(status_id):
        return [s for s in status_list if s['id'] == status_id]

    releases = plugin.get_storage('releases')
    releases.clear()
    status_list = get_status_list()
    items = []
    plugin.set_content('movies')
    if not status:
        movies = api.get_movies()
    else:
        movies = api.get_movies(status=status)
    i = 0
    for i, movie in enumerate(movies):
        info = movie['library']['info']
        movie_id = str(movie['library_id'])
        label = info['titles'][0]
        status_label = get_status(movie['status_id'])[0]['label']
        label = u'[%s] %s' % (status_label, label)
        releases[movie_id] = movie['releases']
        items.append({
            'label': label,
            'thumbnail': (info['images']['poster'] or [''])[0],
            'info': {
                'count': i,
                'originaltitle': info.get('original_title', ''),
                'writer': ', '.join(info.get('writers', [])),
                'director': ', '.join(info.get('directors', [])),
                'code': info.get('imdb', ''),
                'year': info.get('year', 0),
                'plot': info.get('plot', ''),
                'genre': ', '.join(info.get('genres', [])),
                'tagline': info.get('tagline', ''),
                'actors': info.get('actors', []),  # broken in XBMC Frodo
                'rating': info.get('rating', {}).get('imdb', [0, 0])[0],
                'votes': info.get('rating', {}).get('imdb', [0, 0])[1]
            },
            'replace_context_menu': True,
            'context_menu': context_menu(movie_id, info['titles'][0]),
            'properties': {
                'fanart_image': (info['images'].get('backdrop') or [''])[0],
            },
            'path': plugin.url_for(
                endpoint='show_releases',
                library_id=movie_id
            ),
        })
    releases.sync()
    sort_methods = ['playlist_order', 'video_rating', 'video_year']
    return plugin.finish(items, sort_methods=sort_methods)


@plugin.route('/movies/add/')
def add_new_wanted():
    if 'imdb_id' in plugin.request.args:
        imdb_id = plugin.request.args['imdb_id'][0]
        if imdb_id:
            return add_new_wanted_by_id(imdb_id)
    if 'title' in plugin.request.args:
        search_title = plugin.request.args['title'][0]
    else:
        search_title = plugin.keyboard(heading=_('enter_movie_title'))
    if search_title:
        movies = api.search_wanted(search_title)
        if not movies:
            plugin.notify(msg=_('no_movie_found'))
            return
        items = [
            '%s %s' % (movie['titles'][0], 
            	('(%s)' % movie['year']) if movie.get('year', False) else '')
            for movie in movies
        ]
        selected = xbmcgui.Dialog().select(
            _('select_movie'), items
        )
        if selected >= 0:
            selected_movie = movies[selected]
            profile_id = ask_profile()
            if profile_id:
                success = api.add_wanted(
                    profile_id=profile_id,
                    movie_identifier=selected_movie['imdb']
                )
                if success:
                    plugin.notify(msg=_('wanted_added'))


@plugin.route('/movies/add-by-id/<imdb_id>')
def add_new_wanted_by_id(imdb_id):
    profile_id = ask_profile()
    if profile_id:
        success = api.add_wanted(
            profile_id=profile_id,
            movie_identifier=imdb_id
        )
        if success:
            plugin.notify(msg=_('wanted_added'))


def ask_profile():
    if not plugin.get_setting('default_profile', str):
        profiles = api.get_profiles()
        items = [profile['label'] for profile in profiles]
        selected = xbmcgui.Dialog().select(
            _('select_profile'), items
        )
        if selected == -1:
            return
        selected_profile = profiles[selected]
        profile_id = selected_profile['id']
    else:
        profile_id = plugin.get_setting('default_profile', int)
    return profile_id


@plugin.route('/movies/<library_id>/releases/')
def show_releases(library_id):

    def context_menu(release_id):
        return [
            (
                _('delete_release'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='delete_release',
                    release_id=release_id
                )
            ),
            (
                _('download_release'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='download_release',
                    release_id=release_id
                )
            ),
            (
                _('ignore_release'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='ignore_release',
                    release_id=release_id
                )
            ),
            (
                _('addon_settings'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='open_settings'
                )
            ),
        ]

    def labelize(string_id, content):
        return u'[B]%s[/B]: %s' % (_(string_id), content)

    releases = plugin.get_storage('releases')
    items = []
    for release in releases[library_id]:
        info = release['info']
        t = info['type'][0].upper()
        items.append({
            'label': '[%s %d] %s' % (t, info['score'], info['name']),
            'info': {
                'size': info['provider'] * 1024,
                'plot': '[CR]'.join((
                    labelize('type', info['type']),
                    labelize('provider', info['provider']),
                    labelize('provider_extra', info['provider_extra']),
                    labelize('age', info['age']),
                    labelize('seed_leech', '%s/%s' % (
                        info.get('seeders', '0'), info.get('leechers', '0'))
                    ),
                    labelize('size_mb', info['size']),
                    labelize('description', info['description'])
                )),
            },
            'replace_context_menu': True,
            'context_menu': context_menu(release['id']),
            'path': plugin.url_for(
                endpoint='show_release_help',
                foo=release['id']  # to have items with different URLs
            ),
        })
    return plugin.finish(items)


@plugin.route('/movies/all/refresh')
def do_full_refresh():
    success = api.do_full_refresh()
    if success:
        plugin.notify(msg=_('success'))


@plugin.route('/movies/<library_id>/refresh')
def refresh_releases(library_id):
    success = api.refresh_releases(library_id)
    if success:
        plugin.notify(msg=_('success'))


@plugin.route('/movies/<library_id>/delete')
def delete_movie(library_id):
    confirmed = xbmcgui.Dialog().yesno(
        _('delete_movie_head'),
        _('delete_movie_l1')
    )
    if confirmed:
        success = api.delete_movie(library_id)
        if success:
            plugin.notify(msg=_('success'))


@plugin.route('/release/<release_id>/delete')
def delete_release(release_id):
    success = api.delete_release(release_id)
    if success:
        plugin.notify(msg=_('success'))


@plugin.route('/release/<release_id>/download')
def download_release(release_id):
    success = api.download_release(release_id)
    if success:
        plugin.notify(msg=_('success'))


@plugin.route('/release/<release_id>/ignore')
def ignore_release(release_id):
    success = api.ignore_release(release_id)
    if success:
        plugin.notify(msg=_('success'))


@plugin.route('/release/help')
def show_release_help():
    xbmcgui.Dialog().ok(
        _('release_help_head'),
        _('release_help_l1'),
        _('release_help_l2'),
        _('release_help_l3'),
    )


@plugin.route('/settings/default_profile')
def set_default_profile():
    profiles = api.get_profiles()
    items = [profile['label'] for profile in profiles]
    selected = xbmcgui.Dialog().select(
        _('select_default_profile'), items
    )
    if selected >= 0:
        selected_profile = profiles[selected]
        plugin.set_setting('default_profile', str(selected_profile['id']))
    elif selected == -1:
        plugin.set_setting('default_profile', '')


@plugin.route('/settings')
def open_settings():
    plugin.open_settings()


def get_api():
    logged_in = False
    while not logged_in:
        cp_api = CouchPotatoApi()
        try:
            new_api_key = cp_api.connect(
                hostname=plugin.get_setting('hostname', unicode),
                port=plugin.get_setting('port', int),
                use_https=plugin.get_setting('use_https', bool),
                username=plugin.get_setting('username', unicode),
                password=plugin.get_setting('password', unicode),
                api_key=plugin.get_setting('api_key', str),
                url_base=plugin.get_setting('url_base', str),
                ba_username=plugin.get_setting('ba_username', unicode),
                ba_password=plugin.get_setting('ba_password', unicode),
            )
        except AuthenticationError:
            try_again = xbmcgui.Dialog().yesno(
                _('connection_error'),
                _('wrong_credentials'),
                _('want_set_now')
            )
            if not try_again:
                return
            plugin.open_settings()
            continue
        except ConnectionError:
            try_again = xbmcgui.Dialog().yesno(
                _('connection_error'),
                _('wrong_network'),
                _('want_set_now')
            )
            if not try_again:
                return
            plugin.open_settings()
            continue
        else:
            logged_in = True
            if plugin.get_setting('api_key', str) != new_api_key:
                plugin.set_setting('api_key', new_api_key)
    return cp_api


def log(text):
    plugin.log.info(text)


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id]).encode('utf-8')
    else:
        log('String is missing: %s' % string_id)
        return string_id

if __name__ == '__main__':
    api = get_api()
    if api:
        plugin.run()
