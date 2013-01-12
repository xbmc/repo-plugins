#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012-2013 Espen Hovlandsdal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# VGTV plugin for XBMC
import os
from xbmcswift2 import ListItem
from xbmcswift2 import Plugin
from resources.lib.api import VgtvApi
from xbmcswift2 import xbmcgui

STRINGS = {
    'plugin_name':   30000,
    'most_recent':   30001,
    'most_viewed':   30002,
    'search':        30003,
    'previous_page': 30004,
    'next_page':     30005,
}

plugin = Plugin()
vgtv = VgtvApi(plugin)

RES_PATH = os.path.join(
    plugin.addon.getAddonInfo('path'),
    'resources',
    'images',
)


@plugin.route('/')
def index():

    items = [{
        'label': _('most_recent'),
        'thumbnail': os.path.join(RES_PATH, 'latest.png'),
        'path': plugin.url_for('show_latest', page='1')
    }, {
        'label': _('most_viewed'),
        'thumbnail': os.path.join(RES_PATH, 'mostseen.png'),
        'path': plugin.url_for('show_most_seen', page='1')
    }, {
        'label': _('search'),
        'thumbnail': os.path.join(RES_PATH, 'search.png'),
        'path': plugin.url_for('input_search')
    }]

    plugin.add_items(items)
    plugin.add_items(build_category_list())
    return plugin.finish()


@plugin.route('/latest/<page>/')
def show_latest(page):
    items, last_page = vgtv.get_default_video_list(
        url='/videos/published/',
        page=page
    )
    return show_video_list('show_latest', items, page, last_page)


@plugin.route('/mostseen/<page>/')
def show_most_seen(page):
    items, last_page = vgtv.get_default_video_list(
        url='/videos/mostseen/',
        page=page,
        params={'interval': 'week'}
    )
    return show_video_list('show_most_seen', items, page, last_page)


@plugin.route('/search/')
def input_search():
    query = plugin.keyboard(heading=_('search'))

    if query is None or len(str(query)) == 0:
        return

    return show_search(1, query)


@plugin.route('/search/<page>/<query>')
def show_search(page='', query=''):
    items, last_page = vgtv.get_default_video_list(
        url='/videos/search/',
        page=page,
        params={'query': query}
    )
    return show_video_list('show_search', items, page, last_page, query)


@plugin.route('/category/<id>/<page>/', options={'page': '1'})
def show_category(id, page=1):
    categories = build_category_list(id)
    items, last_page = vgtv.get_default_video_list(
        url='/videos/published/',
        page=page,
        params={'category': str(id)}
    )
    return plugin.finish(categories + items)


@plugin.route('/show/<id>/<title>/')
def play_id(id, title=None):
    resolved_url, thumb_url, category_id, duration = vgtv.resolve_video_url(id)
    track_video_play(id, category_id, title, duration)
    return plugin.set_resolved_url(resolved_url)


@plugin.route('/showurl/<url>/<category>/<id>/<title>/<duration>/')
def play_url(url, category=None, id=None, title=None, duration=None):
    track_video_play(id, category, title, duration)
    return plugin.set_resolved_url(url)


def show_video_list(fn, items, page, last_page, query=''):
    page = int(page)
    update_listing = False

    if page > 1:
        update_listing = True

        items.insert(0, {
            'label': _('previous_page'),
            'path':  plugin.url_for(fn, page=str(page - 1), query=query)
        })

    if (last_page is False):
        items.append({
            'label': _('next_page'),
            'path':  plugin.url_for(fn, page=str(page + 1), query=query)
        })

    plugin.add_items(items)
    return plugin.finish(
        view_mode='thumbnail',
        update_listing=update_listing
    )


def build_category_list(root_id=0):
    categories = vgtv.get_categories(root_id)
    items = []

    for category in categories:
        items.append(ListItem(
            label=category.get('label'),
            path=category.get('path')
        ))

    return items


# Call tracking
def track_video_play(id, category, title, duration):
    vgtv.track_play(
        id=id,
        category_id=category,
        title=title,
        resolution=get_resolution(),
        duration=duration
    )


# Translation macro
def _(string):
    if string in STRINGS:
        return plugin.get_string(STRINGS[string])
    else:
        return string


# Resolution getter
def get_resolution():
    try:
        win = xbmcgui.Window()
        return win.getWidth() + 'x' + win.getHeight()
    except TypeError:
        return '1920x1080'

if __name__ == '__main__':
    plugin.run()
