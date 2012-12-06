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

import resources.lib.videos_scraper as videos_scraper
import resources.lib.streams_scraper as streams_scraper
import resources.lib.vodcasts_scraper as vodcast_scraper

STRINGS = {
    'page': 30001,
    'streams': 30100,
    'videos': 30101,
    'vodcasts': 30103,
    'search': 30200,
    'title': 30201
}

plugin = Plugin()


@plugin.route('/')
def show_root_menu():
    items = [
        {'label': _('streams'),
         'path': plugin.url_for('show_streams')},
        {'label': _('videos'),
         'path': plugin.url_for('show_video_topics')},
        {'label': _('vodcasts'),
         'path': plugin.url_for('show_vodcasts')}
    ]
    return plugin.finish(items)


@plugin.route('/streams/')
def show_streams():
    items = [{
        'label': stream['title'],
        'path': plugin.url_for(
            endpoint='play_stream',
            id=stream['id']
        ),
        'icon': stream['thumbnail'],
        'info': {
            'originaltitle': stream['title'],
            'plot': stream['description']
        },
        'is_playable': True,
    } for stream in streams_scraper.get_streams()]
    return plugin.finish(items)


@plugin.route('/videos/')
def show_video_topics():
    scraper = videos_scraper.Scraper()
    items = [{
        'label': topic['name'],
        'path': plugin.url_for(
            endpoint='show_videos_by_topic',
            topic_id=topic['id'],
            page='1'
        ),
    } for topic in scraper.get_video_topics()]
    items.append({
        'label': _('search'),
        'path': plugin.url_for(
            endpoint='search'
        )
    })
    return plugin.finish(items)


@plugin.route('/vodcasts/')
def show_vodcasts():
    items = [{
        'label': vodcast['title'],
        'path': plugin.url_for(
            endpoint='show_vodcast_videos',
            rss_file=vodcast['rss_file']
        ),
    } for vodcast in vodcast_scraper.get_vodcasts()]
    return plugin.finish(items)


@plugin.route('/vodcasts/<rss_file>/')
def show_vodcast_videos(rss_file):
    videos = vodcast_scraper.show_vodcast_videos(rss_file)
    items = [{
        'label': video['title'],
        'info': {
            'plot': video['description']
        },
        'path': video['url'],
        'thumbnail': video['thumbnail'],
        'is_playable': True,
    } for video in videos]
    return plugin.finish(items)


@plugin.route('/videos/<topic_id>/<page>/')
def show_videos_by_topic(topic_id, page):
    scraper = videos_scraper.Scraper()
    limit = 30
    page = int(page)
    start = (page - 1) * limit
    videos, count = scraper.get_videos_by_topic_id(topic_id, start, limit)
    items = __format_videos(videos)
    if count > page * limit:
        next_page = str(page + 1)
        items.insert(0, {
            'label': '>> %s %s >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='show_videos_by_topic',
                topic_id=topic_id,
                page=next_page,
                update='true')
        })
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='show_videos_by_topic',
                topic_id=topic_id,
                page=previous_page,
                update='true')
        })
    finish_kwargs = {
        'sort_methods': ('PLAYLIST_ORDER', 'DATE', 'SIZE', 'DURATION'),
        'update_listing': 'update' in plugin.request.args
    }
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/video/<id>')
def play_video(id):
    video = videos_scraper.Scraper().get_video(id)
    return plugin.set_resolved_url(video['url'])


@plugin.route('/stream/<id>')
def play_stream(id):
    stream_url = streams_scraper.get_stream(id)
    return plugin.set_resolved_url(stream_url)


@plugin.route('/search/')
def search():
    query = plugin.keyboard(heading=_('title'))
    if query and len(query) > 3:
        log('search gots a string: "%s"' % query)
        videos, count = videos_scraper.Scraper().search_videos(query)
        items = __format_videos(videos)
        return plugin.finish(items)


def __format_videos(videos):
    items = [{
        'label': video['title'],
        'thumbnail': video['thumbnail'],
        'info': {
            'originaltitle': video['title'],
            'duration': video['duration'],
            'plot': video['description'],
            'date': video['date'],
            'size': video['filesize'],
            'credits': video['author'],
            'genre': ' | '.join(video['genres'])
        },
        'is_playable': True,
        'path': plugin.url_for(
            endpoint='play_video',
            id=video['id']
        ),
    } for video in videos]
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
