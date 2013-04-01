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
import resources.lib.scraper as scraper

plugin = Plugin()


@plugin.route('/')
def show_categories():
    categories = scraper.get_categories()
    items = [{
        'label': category['title'],
        'path': plugin.url_for(
            endpoint='show_videos',
            category=category['link'],
            page='1',
        ),
    } for category in categories]
    return plugin.finish(items)


@plugin.route('/category/<category>/<page>/')
def show_videos(category, page):
    videos, has_next_page = scraper.get_videos(category, page)
    items = [{
        'label': video['title'],
        'thumbnail': video['image'],
        'info': {
            'originaltitle': video['title']
        },
        'path': plugin.url_for(
            endpoint='watch_video',
            url=video['link']
        ),
        'is_playable': True,
    } for video in videos]
    if has_next_page:
        next_page = str(int(page) + 1)
        items.append({
            'label': '>> %s %s >>' % (
                plugin.get_string(30001),
                next_page
            ),
            'path': plugin.url_for(
                endpoint='show_videos',
                category=category,
                page=next_page
            ),
        })
    if int(page) > 1:
        prev_page = str(int(page) - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (
                plugin.get_string(30001),
                prev_page
            ),
            'path': plugin.url_for(
                endpoint='show_videos',
                category=category,
                page=prev_page
            ),
        })
    return plugin.finish(items)


@plugin.route('/watch/<url>/')
def watch_video(url):
    video_url = scraper.get_video_file(url)
    return plugin.set_resolved_url(video_url)


if __name__ == '__main__':
    plugin.run()
