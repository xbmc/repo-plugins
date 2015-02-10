#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer
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
from resources.lib import scraper

plugin = Plugin()

STRINGS = {
    'current': 30000,
    'archive': 30002,
    'search': 30003,
    'network_error': 30020
}


@plugin.route('/')
def show_root():
    items = [
        {'label': _('current'),
         'path': plugin.url_for('show_current')},
        {'label': _('archive'),
         'path': plugin.url_for('show_archive')},
        {'label': _('search'),
         'path': plugin.url_for('search')}
    ]
    return plugin.finish(items)


@plugin.route('/current/')
def show_current():
    videos = scraper.get_current_videos()
    return __add_videos(videos)


@plugin.route('/watch/<video_id>')
def watch_video(video_id):
    video_url = scraper.get_video_url(video_id)
    return plugin.set_resolved_url(video_url)


@plugin.route('/archive/')
def show_archive():
    archive_dates = scraper.get_archive_dates()
    items = [{
        'label': archive_date['title'],
        'path': plugin.url_for(
            'show_archived_videos',
            archive_id=archive_date['archive_id'],
        ),
    } for archive_date in archive_dates]
    items.reverse()
    return plugin.finish(items)


@plugin.route('/archive/<archive_id>/')
def show_archived_videos(archive_id):
    videos = scraper.get_archived_videos(
        archive_id=archive_id
    )
    return __add_videos(videos)


@plugin.route('/search/')
def search():
    search_string = plugin.keyboard(heading=_('search'))
    if search_string:
        url = plugin.url_for(
            'search_result',
            search_string=search_string
        )
        plugin.redirect(url)


@plugin.route('/search/<search_string>/')
def search_result(search_string):
    videos = scraper.get_search_result(search_string)
    return __add_videos(videos)


def __add_videos(videos):
    items = [{
        'label': video['title'],
        'thumbnail': video['thumb'],
        'path': plugin.url_for(
            'watch_video',
            video_id=video['video_id']
        ),
        'info': {
            'date': video['date']
        },
        'is_playable': True,
    } for video in videos]
    finish_kwargs = {
        'sort_methods': ('DATE', )
    }
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


if __name__ == '__main__':
    try:
        plugin.run()
    except scraper.NetworkError:
        plugin.notify(msg=_('network_error'))
