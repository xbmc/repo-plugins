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

import re
from xbmcswift2 import Plugin, xbmc, xbmcgui
from resources.lib import scraper

STRINGS = {
    'page': 30000,
    'search': 30001,
    'show_my_favs': 30002,
    'no_scraper_found': 30003,
    'add_to_my_favs': 30004,
    'del_from_my_favs': 30005,
    'no_my_favs': 30006,
    'use_context_menu': 30007,
    'to_add': 30008,
}

plugin = Plugin()


@plugin.route('/')
def show_categories():
    items = [{
        'label': category['title'],
        'path': plugin.url_for(
            endpoint='show_path',
            path=category['path']
        )
    } for category in scraper.get_categories()]
    items.append({
        'label': _('search'),
        'path': plugin.url_for('video_search')
    })
    items.append({
        'label': _('show_my_favs'),
        'path': plugin.url_for('show_my_favs')
    })
    return plugin.finish(items)


@plugin.route('/search/')
def video_search():
    search_string = __keyboard(_('search'))
    if search_string:
        __log('search gots a string: "%s"' % search_string)
        url = plugin.url_for(
            endpoint='video_search_result',
            search_string=search_string
        )
        plugin.redirect(url)


@plugin.route('/search/<search_string>/')
def video_search_result(search_string):
    path = scraper.get_search_path(search_string)
    return show_path(path)


@plugin.route('/my_favs/')
def show_my_favs():

    def context_menu(item_path):
        context_menu = [(
            _('del_from_my_favs'),
            'XBMC.RunPlugin(%s)' % plugin.url_for('del_from_my_favs',
                                                  item_path=item_path),
        )]
        return context_menu

    my_fav_items = plugin.get_storage('my_fav_items')
    items = my_fav_items.values()
    for item in items:
        item['context_menu'] = context_menu(item['path'])
    if not items:
        dialog = xbmcgui.Dialog()
        dialog.ok(_('no_my_favs'), _('use_context_menu'), _('to_add'))
        return
    return plugin.finish(items)


@plugin.route('/path/<path>/')
def show_path(path):
    try:
        items, next_page, prev_page = scraper.get_path(path)
    except NotImplementedError:
        plugin.notify(msg=_('no_scraper_found'), title='Path: %s' % path)
    else:
        return __add_items(items, next_page, prev_page)


def __add_items(entries, next_page=None, prev_page=None):
    my_fav_items = plugin.get_storage('my_fav_items')

    def context_menu(item_path, video_id):
        if not item_path in my_fav_items:
            context_menu = [(
                _('add_to_my_favs'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='add_to_my_favs',
                    item_path=item_path
                ),
            )]
        else:
            context_menu = [(
                _('del_from_my_favs'),
                'XBMC.RunPlugin(%s)' % plugin.url_for(
                    endpoint='del_from_my_favs',
                    item_path=item_path
                ),
            )]
        return context_menu

    def format_episode_title(title):
        if fix_show_title and '-' in title and ('Folge' in title or 'Staffel' in title):
            title, show = title.rsplit('-', 1)
            title = title.replace('Staffel ', 'S').replace(' Folge ', 'E')
            title = title.replace('Folge ', 'E').replace('Ganze Folge', '')
            return u'%s %s' % (show.strip(), title.strip())
        return title

    def better_thumbnail(thumb_url):
        if 'web/' in thumb_url and not thumb_url.startswith('http://is'):
            thumb_url = thumb_url.replace('http://i', 'http://is')
            thumb_url = re.sub('mv/web/[0-9]+', 'de', thumb_url)
            thumb_url = thumb_url.replace('.jpg', '.jpg_hq.jpg')
        return thumb_url

    fix_show_title = plugin.get_setting('fix_show_title', bool)
    temp_items = plugin.get_storage('temp_items')
    temp_items.clear()
    items = []
    has_icons = False
    i = 0
    for i, entry in enumerate(entries):
        if not has_icons and entry.get('thumb'):
            has_icons = True
        if entry['is_folder']:
            items.append({
                'label': entry['title'],
                'thumbnail': entry.get('thumb', 'DefaultFolder.png'),
                'info': {'count': i + 1},
                'path': plugin.url_for(
                    endpoint='show_path',
                    path=entry['path']
                )
            })
        else:
            items.append({
                'label': format_episode_title(entry['title']),
                'thumbnail': better_thumbnail(
                    entry.get('thumb', 'DefaultVideo.png')
                ),
                'icon': entry.get('thumb', 'DefaultVideo.png'),
                'info': {
                    'video_id': entry['video_id'],
                    'count': i + 1,
                    'plot': entry.get('description', ''),
                    'studio': entry.get('author', {}).get('name', ''),
                    'date': entry.get('date', ''),
                    'year': int(entry.get('year', 0)),
                    'rating': float(entry.get('rating', 0)),
                    'votes': unicode(entry.get('votes')),
                    'views': unicode(entry.get('views', 0))
                },
                'stream_info': {
                    'video': {'duration': entry.get('duration', 0)}
                },
                'is_playable': True,
                'path': plugin.url_for(
                    endpoint='watch_video',
                    video_id=entry['video_id']
                )
            })
    if prev_page:
        items.append({
            'label': '<< %s %s <<' % (_('page'), prev_page['number']),
            'info': {'count': 0},
            'thumbnail': 'DefaultFolder.png',
            'path': plugin.url_for(
                endpoint='show_path',
                path=prev_page['path'],
                update='true',
            )
        })
    if next_page:
        items.append({
            'label': '>> %s %s >>' % (_('page'), next_page['number']),
            'thumbnail': 'DefaultFolder.png',
            'info': {'count': i + 2},
            'path': plugin.url_for(
                endpoint='show_path',
                path=next_page['path'],
                update='true',
            )
        })

    for item in items:
        temp_items[item['path']] = item
        item['context_menu'] = context_menu(
            item['path'], item['info'].get('video_id')
        )
    temp_items.sync()

    update_on_pageswitch = plugin.get_setting('update_on_pageswitch', bool)
    is_update = update_on_pageswitch and 'update' in plugin.request.args
    finish_kwargs = {
        'sort_methods': ('playlist_order', 'label'),
        'update_listing': is_update
    }
    if has_icons and plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/video/<video_id>/play')
def watch_video(video_id):
    video = scraper.get_video(video_id)
    if 'hls_playlist' in video:
        __log('watch_video using HLS')
        video_url = video['hls_playlist']
    elif not video['rtmpurl']:
        __log('watch_video using FLV')
        video_url = video['filepath'] + video['file']
    else:
        __log('watch_video using RTMPE or RTMPT')
        video_url = (
            '%(rtmpurl)s '
            'tcUrl=%(rtmpurl)s '
            'swfVfy=%(swfobj)s '
            'pageUrl=%(pageurl)s '
            'playpath=%(playpath)s'
        ) % video
    __log('watch_video finished with url: %s' % video_url)
    return plugin.set_resolved_url(video_url)


@plugin.route('/my_favs/add/<item_path>')
def add_to_my_favs(item_path):
    my_fav_items = plugin.get_storage('my_fav_items')
    temp_items = plugin.get_storage('temp_items')
    my_fav_items[item_path] = temp_items[item_path]
    my_fav_items.sync()


@plugin.route('/my_favs/del/<item_path>')
def del_from_my_favs(item_path):
    my_fav_items = plugin.get_storage('my_fav_items')
    if item_path in my_fav_items:
        del my_fav_items[item_path]
        my_fav_items.sync()


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


def __log(text):
    plugin.log.info(text)


if __name__ == '__main__':
    try:
        plugin.run()
    except scraper.NetworkError:
        plugin.notify(msg=_('network_error'))
