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

from datetime import date
from string import ascii_lowercase, digits
from xbmcswift2 import Plugin, xbmc
from resources.lib.api import DokuMonsterApi, NetworkError

PER_PAGE = 50

plugin = Plugin()
api = DokuMonsterApi(default_count=PER_PAGE)

STRINGS = {
    'popular_docus': 30001,
    'new_docus': 30002,
    'tags': 30003,
    'all': 30004,
    'top_docus': 30005,
    'search': 30006,
    'network_error': 30200
}


@plugin.route('/')
def show_root():
    items = (
        # FIXME: Reihe
        {'label': _('popular_docus'), 'path': plugin.url_for(
            endpoint='show_popular_docus'
        )},
        {'label': _('new_docus'), 'path': plugin.url_for(
            endpoint='show_new_docus'
        )},
        {'label': _('tags'), 'path': plugin.url_for(
            endpoint='show_tags'
        )},
        {'label': _('all'), 'path': plugin.url_for(
            endpoint='show_initials'
        )},
        {'label': _('top_docus'), 'path': plugin.url_for(
            endpoint='show_top_docus'
        )},
        {'label': _('search'), 'path': plugin.url_for(
            endpoint='search'
        )},
    )
    return plugin.finish(items)


@plugin.route('/tags/')
def show_tags():
    tags = api.get_tags()
    items = [{
        'label': '%s [%s]' % (tag.get('name'), tag.get('count')),
        'path': plugin.url_for(
            endpoint='show_docus_by_tag',
            tag=tag['id']
        )
    } for tag in tags]
    return plugin.finish(items)


@plugin.route('/tags/<tag>/')
def show_docus_by_tag(tag):
    return __finish_paginate(
        'show_docus_by_tag', api.get_docus_by_tag, tag=tag
    )


@plugin.route('/initals/')
def show_initials():
    items = []
    for char in list(ascii_lowercase + digits):
        items.append({
            'label': char.upper(),
            'path': plugin.url_for(
                endpoint='show_docus_by_initial',
                initial=char
            )
        })
    return plugin.finish(items)


@plugin.route('/initals/<initial>/')
def show_docus_by_initial(initial):
    return __finish_paginate(
        'show_docus_by_initial', api.get_docus_by_initial, initial=initial
    )


@plugin.route('/popular_docus/')
def show_popular_docus():
    return __finish_paginate('show_popular_docus', api.get_popular_docus)


@plugin.route('/top_docus/')
def show_top_docus():
    return __finish_paginate('show_top_docus', api.get_top_docus)


@plugin.route('/new_docus/')
def show_new_docus():
    return __finish_paginate('show_new_docus', api.get_newest_docus)


@plugin.route('/search/')
def search():
    query = __keyboard(_('search'))
    if query:
        url = plugin.url_for('search_result', query=query)
        plugin.redirect(url)


@plugin.route('/search/<query>/')
def search_result(query):
    return __finish_paginate(
        'search_result', api.get_docus_by_query, query=query
    )


@plugin.route('/play/<docu_id>')
def play(docu_id):
    docu = api.get_docu(docu_id)
    plugin.log.info(repr(docu))
    media = docu.get('media', {})
    source, media_type = media.get('source'), media.get('type')
    playback_url = None
    if source == 'youtube.com':
        if media_type == 'video':
            playback_url = (
                'plugin://plugin.video.youtube/'
                '?action=play_video&videoid=%s' % media.get('id')
            )
        elif media_type == 'playlist':
            playback_url = (
                'plugin://plugin.video.youtube/'
                '?action=play_all&playlist=%s' % media.get('id')
            )
    elif source == 'vimeo.com':
        if media_type == 'video':
            playback_url = (
                'plugin://plugin.video.vimeo/'
                '?action=play_video&videoid=%s' % media.get('id')
            )
    if playback_url:
        plugin.log.info('Using playback url: %s' % playback_url)
        return plugin.set_resolved_url(playback_url)
    else:
        plugin.log.error(repr(media))
        plugin.notify(msg=_('Not Implemented yet'))


def __finish_paginate(endpoint, api_func, *args, **kwargs):
    is_update = 'page' in plugin.request.args
    page = plugin.request.args.get('page', ['1'])[0]
    docus, total_count = api_func(*args, page=page, **kwargs)
    items = __format_docus(docus)
    if int(page) > 1:
        p = str(int(page) - 1)
        items.insert(0, {
            'label': '<< Page %s <<' % p,
            'info': {'count': 0},
            'path': plugin.url_for(
                endpoint,
                page=p,
                **kwargs
            )
        })
    if int(page) * PER_PAGE > int(total_count):
        p = str(int(page) + 1)
        items.append({
            'label': '>> Page %s >>' % p,
            'info': {'count': len(docus) + 2},
            'path': plugin.url_for(
                endpoint,
                page=p,
                **kwargs
            )
        })
    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE'),
        'update_listing': is_update
    }
    if plugin.get_setting('force_viewmode') == 'true':
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


def __format_docus(docus, skip_playlists=True):
    items = []
    for i, docu in enumerate(docus):
        if skip_playlists and docu['media']['type'] == 'playlist':
            continue
        tagline = 'language: %s | views: %s | comments: %s' % (
            docu['lang'], docu['views'], docu['comments']
        )
        d = date.fromtimestamp(float(docu['online']))
        pub_date = '%02d.%02d.%04d' % (d.day, d.month, d.year)
        title = u'[COLOR red][%s°][/COLOR] %s' % (docu['fire'], docu['title'])
        item = {
            'label': title,
            'icon': docu['thumb'],
            'info': {
                'count': i + 1,
                'studio': docu['username'] or '',
                'genre': docu['tags'] or '',
                'tagline': tagline,
                'plot': docu['description'].replace('\n\r', '[CR]') or '',
                'date': pub_date
            },
            'path': plugin.url_for(
                endpoint='play',
                docu_id=docu['id']
            ),
            'is_playable': True
        }
        items.append(item)
    return items


def __keyboard(title, text=''):
    keyboard = xbmc.Keyboard(text, title)
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        return keyboard.getText()


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


if __name__ == '__main__':
    try:
        plugin.run()
    except NetworkError:
        plugin.notify(msg=_('network_error'))
