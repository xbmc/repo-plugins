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

from xbmcswift2 import Plugin
from resources.lib.scraper import Scraper


STRINGS = {
    'page': 30001
}

plugin = Plugin()
scraper = Scraper()


@plugin.route('/')
def show_topics():
    topics = scraper.get_video_topics()
    items = [{
        'label': topic['title'],
        'path': plugin.url_for(
            endpoint='show_videos',
            topic_id=topic['id'],
            page='1'
        )
    } for topic in topics]
    return plugin.finish(items)


@plugin.route('/videos/<topic_id>/<page>/')
def show_videos(topic_id, page):
    page = int(page)
    videos = scraper.get_videos(topic_id, page)
    items = __format_videos(videos)
    if True:  # FIXME: find a way to detect...
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='show_videos',
                topic_id=topic_id,
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='show_videos',
                topic_id=topic_id,
                page=previous_page,
                update='true')
        })
    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    if plugin.get_setting('force_viewmode') == 'true':
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/video/<video_id>')
def play_video(video_id):
    video_url = scraper.get_video_url(video_id)
    return plugin.set_resolved_url(video_url)


def __format_videos(videos):
    items = [{
        'label': video['title'],
        'icon': video['thumbnail'],
        'thumbnail': video['thumbnail'],
        'info': {
            'count': i,
        },
        'stream_info': {
            'video': {'duration': video['duration']}
        },
        'is_playable': True,
        'path': plugin.url_for(
            endpoint='play_video',
            video_id=video['id']
        ),
    } for i, video in enumerate(videos)]
    return items


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id


def log(text):
    plugin.log.info(text)

if __name__ == '__main__':
    plugin.run()
