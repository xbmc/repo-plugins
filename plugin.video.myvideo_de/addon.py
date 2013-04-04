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

import string
from xbmcswift2 import Plugin, xbmc, xbmcgui
import SimpleDownloader
from resources.lib import scraper

STRINGS = {
    'page': 30000,
    'search': 30001,
    'download': 30020,
    'no_download_path': 30030,
    'set_now?': 30031,
    'hls_error': 30032,
}

plugin = Plugin()


@plugin.route('/')
def show_categories():
    items = [{
        'label': category['title'],
        'path': plugin.url_for(
            endpoint='show_subcategories',
            path=category['path']
        )
    } for category in scraper.get_categories()]
    items.append({
        'label': _('search'),
        'path': plugin.url_for('video_search')}
    )
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
    items = scraper.get_search_result(search_string)
    return __add_items(items)


@plugin.route('/category/<path>/')
def show_subcategories(path):
    categories = scraper.get_sub_categories(path)
    items = [{
        'label': category['title'],
        'path': plugin.url_for(
            endpoint='show_path',
            path=category['path']
        )
    } for category in categories]
    return plugin.finish(items)


@plugin.route('/<path>/')
def show_path(path):
    items = scraper.get_path(path)
    return __add_items(items)


def __add_items(entries):
    items = []
    update_on_pageswitch = plugin.get_setting('update_on_pageswitch') == 'true'
    has_icons = False
    is_update = False
    for entry in entries:
        if not has_icons and entry.get('thumb'):
            has_icons = True
        if entry.get('pagenination'):
            if entry['pagenination'] == 'PREV':
                if update_on_pageswitch:
                    is_update = True
                title = '<< %s %s <<' % (_('page'), entry['title'])
            elif entry['pagenination'] == 'NEXT':
                title = '>> %s %s >>' % (_('page'), entry['title'])
            items.append({
                'label': title,
                'icon': 'DefaultFolder.png',
                'path': plugin.url_for(
                    endpoint='show_path',
                    path=entry['path']
                )
            })
        elif entry['is_folder']:
            items.append({
                'label': entry['title'],
                'icon': entry.get('thumb', 'DefaultFolder.png'),
                'path': plugin.url_for(
                    endpoint='show_path',
                    path=entry['path']
                )
            })
        else:
            download_url = plugin.url_for(
                endpoint='download_video',
                video_id=entry['video_id']
            )
            items.append({
                'label': entry['title'],
                'icon': entry.get('thumb', 'DefaultVideo.png'),
                'info': {
                    'plot': entry.get('description', ''),
                    'studio': entry.get('username', ''),
                    'date': entry.get('date', ''),
                    'year': int(entry.get('year', 0)),
                    'rating': float(entry.get('rating', 0)),
                    'votes': unicode(entry.get('votes')),
                    'views': unicode(entry.get('views', 0))
                },
                'context_menu': [
                    (_('download'), 'XBMC.RunPlugin(%s)' % download_url),
                ],
                'stream_info': {
                    'video': {'duration': entry.get('length', 0)}
                },
                'is_playable': True,
                'path': plugin.url_for(
                    endpoint='watch_video',
                    video_id=entry['video_id']
                )
            })
    finish_kwargs = {
        #'sort_methods': ('UNSORTED', 'RATING', 'RUNTIME'),
        'update_listing': is_update
    }
    if has_icons and plugin.get_setting('force_viewmode') == 'true':
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/video/<video_id>/download')
def download_video(video_id):
    download_path = plugin.get_setting('download_path')
    while not download_path:
        dialog = xbmcgui.Dialog()
        set_now = dialog.yesno(_('no_download_path'), _('set_now?'))
        if set_now:
            plugin.open_settings()
            download_path = plugin.get_setting('download_path')
        else:
            return
    sd = SimpleDownloader.SimpleDownloader()
    video = scraper.get_video(video_id)
    filename = __get_legal_filename(video['title'])
    if not video['rtmpurl']:
        params = {
            'url': video['filepath'] + video['file'],
        }
    else:
        params = {
            'use_rtmpdump': True,
            'url': video['rtmpurl'],
            'tcUrl': video['rtmpurl'],
            'swfUrl': video['swfobj'],
            'pageUrl': video['pageurl'],
            'playpath': video['playpath']
        }
    params['download_path'] = download_path
    __log('params: %s' % repr(params))
    __log('start downloading: %s to path: %s' % (filename, download_path))
    sd.download(filename, params)


@plugin.route('/video/<video_id>/play')
def watch_video(video_id):
    video = scraper.get_video(video_id)
    if not video['rtmpurl']:
        __log('watch_video using FLV')
        video_url = video['filepath'] + video['file']
        __log('wget %s' % video_url)
    else:
        __log('watch_video using RTMPE or RTMPT')
        __log((
            'rtmpdump '
            '--rtmp "%(rtmpurl)s" '
            '--flv "test.flv" '
            '--tcUrl "%(rtmpurl)s" '
            '--swfVfy "%(swfobj)s" '
            '--pageUrl "%(pageurl)s" '
            '--playpath "%(playpath)s"'
        ) % video)
        video_url = (
            '%(rtmpurl)s '
            'tcUrl=%(rtmpurl)s '
            'swfVfy=%(swfobj)s '
            'pageUrl=%(pageurl)s '
            'playpath=%(playpath)s'
        ) % video
    __log('watch_video finished with url: %s' % video_url)
    return plugin.set_resolved_url(video_url)


def __keyboard(title, text=''):
    keyboard = xbmc.Keyboard(text, title)
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        return keyboard.getText()


def __get_legal_filename(title):
    chars = ' ._-%s%s' % (string.ascii_letters, string.digits)
    return '%s.flv' % ''.join((c for c in title if c in chars))


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
    except NotImplementedError:
        plugin.notify(msg=_('hls_error'))
