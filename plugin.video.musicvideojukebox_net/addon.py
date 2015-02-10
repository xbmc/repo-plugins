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

from random import shuffle
from resources.lib import scraper
from xbmcswift2 import Plugin

plugin = Plugin()


@plugin.route('/')
def show_root():
    videos = scraper.get_videos()
    shuffle(videos)
    items = [{
        'label': u'%s - %s' % (video['interpret'], video['title']),
        'thumbnail': video['thumb'],
        'is_playable': True,
        'path': plugin.url_for(
            'play_video',
            video_url=video['video_url']
        )
    } for video in videos]
    finish_kwargs = {}
    if plugin.get_setting('force_viewmode', bool):
        finish_kwargs['view_mode'] = 'thumbnail'
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/play/<video_url>')
def play_video(video_url):
    return plugin.set_resolved_url(video_url)


if __name__ == '__main__':
    try:
        plugin.run()
    except scraper.NetworkError:
        plugin.notify(plugin.get_string(30020))
