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
from resources.lib.videobash_scraper import Scraper, NetworkError

plugin = Plugin()
scraper = Scraper('video')

STRINGS = {
    'page': 30000,
}


@plugin.route('/')
def show_categories():
    categories = scraper.get_categories()
    items = [{
        'label': category['title'],
        'path': plugin.url_for(
            'show_videos',
            category_id=category['id'],
            page='1',
        ),
    } for category in categories]
    return plugin.finish(items)


@plugin.route('/videos/<category_id>/<page>/')
def show_videos(category_id, page):
    videos, has_next_page = scraper.get_items(
        category=category_id,
        page=page,
    )
    items = []
    if int(page) > 1:
        previous_page = int(page) - 1
        items.append({
            'label': '<< %s %d <<' % (_('page'), previous_page),
            'path': plugin.url_for(
                endpoint='show_videos',
                category_id=category_id,
                page=str(previous_page),
                update='true'
            )
        })
    items.extend([{
        'label': video['title'],
        'thumbnail': video['thumb'],
        'is_playable': True,
        'path': plugin.url_for(
            endpoint='show_video',
            video_id=video['id'],
        )
    } for video in videos])
    if has_next_page:
        next_page = int(page) + 1
        items.append({
            'label': '>> %s %d >>' % (_('page'), next_page),
            'path': plugin.url_for(
                endpoint='show_videos',
                category_id=category_id,
                page=str(next_page),
                update='true'
            )
        })
    finish_kwargs = {}
    if plugin.get_setting('force_viewmode') == 'true':
        finish_kwargs['view_mode'] = 'thumbnail'
    if 'update' in plugin.request.args:
        finish_kwargs['update_listing'] = True
    return plugin.finish(items, **finish_kwargs)


@plugin.route('/video/<video_id>')
def show_video(video_id):
    video_url = scraper.get_item_url(video_id)
    return plugin.set_resolved_url(video_url)


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
