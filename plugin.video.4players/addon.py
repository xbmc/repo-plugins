#!/usr/bin/python
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

from xbmcswift2 import Plugin
from resources.lib.api import XBMC4PlayersApi, NetworkError, SYSTEMS

STRINGS = {
    'latest_videos': 30000,
    'next': 30001,
    'popular_videos': 30002,
    'network_error': 30200,
    'videos_by_game': 30003,
    'search_by_game': 30004,
    'enter_game_title': 30005,
    'reviews': 30006,
}

plugin = Plugin()
api = XBMC4PlayersApi()


@plugin.route('/')
def show_root_menu():
    items = [
        {'label': _('latest_videos'),
         'path': plugin.url_for('latest_videos')},
        {'label': _('reviews'),
         'path': plugin.url_for('reviews')},
        {'label': _('popular_videos'),
         'path': plugin.url_for('popular_videos')},
        {'label': _('search_by_game'),
         'path': plugin.url_for('search_by_game')},
    ]
    return plugin.finish(items)


@plugin.route('/latest_reviews/', name='reviews', options={'reviews': True})
@plugin.route('/latest_videos/', name='latest_videos')
@plugin.route('/latest_videos/<game_id>/', name='videos_by_game')
def latest_videos(game_id=None, reviews=False):
    older_than = int(plugin.request.args.get('older_than', [0])[0])
    if game_id:
        videos = api.get_videos_by_game(older_than=older_than, game_id=game_id)
    elif reviews:
        videos = api.get_latest_reviews(older_than=older_than)
    else:
        videos = api.get_latest_videos(older_than=older_than)
    most_recent_ts = min((v['ts'] for v in videos))
    items = __format_videos(videos)
    if len(items) == api.LIMIT:
        items.append({
            'label': '>> %s >>' % _('next'),
            'path': plugin.url_for(
                endpoint='latest_videos',
                game_id=game_id,
                older_than=most_recent_ts
            )
        })
    finish_kwargs = {
        'update_listing': 'older_than' in plugin.request.args
    }
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/popular_videos/')
def popular_videos():
    page = int(plugin.request.args.get('page', ['1'])[0])
    videos = api.get_popular_videos(page=page)
    items = __format_videos(videos)
    items.append({
        'label': '>> %s >>' % _('next'),
        'path': plugin.url_for(
            endpoint='popular_videos',
            page=(page + 1)
        )
    })

    finish_kwargs = {
        'update_listing': 'page' in plugin.request.args
    }
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/search/')
def search_by_game():
    search_string = plugin.keyboard(heading=_('enter_game_title'))
    if search_string:
        url = plugin.url_for(
            endpoint='show_games',
            search_string=search_string
        )
        plugin.redirect(url)


@plugin.route('/search/<search_string>/')
def show_games(search_string):
    games = api.get_games(search_string)
    items = __format_games(games)
    finish_kwargs = {}
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/play/<url>')
def play_video(url):
    return plugin.set_resolved_url(url)


def __format_videos(videos):
    quality = plugin.get_setting('quality2', choices=('normal', 'hq'))
    videos = [{
        'label': '%s: %s' % (video['game']['title'], video['video_title']),
        'thumbnail': video['thumb'],
        'info': {
            'title': video['game']['title'],
            'tagline': video['video_title'],
            'size': video['streams'][quality]['size'],
            'date': video['date'],
            'genre': video['game']['genre'],
            'studio': video['game']['studio'],
            'rating': float(video['rating']),
            'votes': video['play_count'],
            'count': i,
            'plot': '[CR]'.join((
                'Date: %s' % video['date'],
                'Size: %d MB' % (int(video['streams'][quality]['size']) / 1048576),
                'Length: %s' % video['duration_str'],
            )),
        },
        'is_playable': True,
        'context_menu': [(
            _('videos_by_game'),
            'Container.Update(%s)' % plugin.url_for(
                endpoint='videos_by_game',
                game_id=str(video['game']['id'])
            )
        )],
        'stream_info': {
            'video': {'duration': video['duration']}
        },
        'path': plugin.url_for(
            endpoint='play_video',
            url=video['streams'][quality]['url']
        ),
    } for i, video in enumerate(videos)]
    return videos


def __format_games(games):
    games = [{
        'label': game['title'],
        'thumbnail': game['thumb'],
        'info': {
            'original_title': game['title'],
            'genre': game['genre'],
            'studio': game['studio'],
            'count': i,
        },
        'path': plugin.url_for(
            endpoint='videos_by_game',
            game_id=str(game['id'])
        ),
    } for i, game in enumerate(games)]
    return games


def __get_enabled_systems():
    if plugin.get_setting('system_filter_enabled', bool):
        enabled_systems = []
        for system in SYSTEMS:
            s = 'show_%s' % system.lower()
            if plugin.get_setting(s, bool):
                enabled_systems.append(system)
        return enabled_systems
    return SYSTEMS


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


if __name__ == '__main__':
    try:
        api.set_systems(__get_enabled_systems())
        plugin.run()
    except NetworkError:
        plugin.notify(msg=_('network_error'))
