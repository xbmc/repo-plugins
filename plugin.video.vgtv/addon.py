#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2012-2016 Espen Hovlandsdal
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

# VGTV plugin for Kodi/XBMC
import os, binascii
from resources.lib.api import VgtvApi
from xbmcswift2 import ListItem
from xbmcswift2 import Plugin
from xbmcswift2 import xbmcgui

STRINGS = {
    'plugin_name':         30000,
    'featured':            30001,
    'series':              30002,
    'news':                30003,
    'documentaries':       30004,
    'most_seen':           30005,
    'categories':          30006,
    'live':                30007,
    'search':              30008,
    'previous_page':       30009,
    'next_page':           30010,
    'remove_from_history': 30011
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
        'label': _('featured'),
        'thumbnail': os.path.join(RES_PATH, 'icon-featured.png'),
        'path': plugin.url_for('show_featured', page='1')
    }, {
        'label': _('series'),
        'thumbnail': os.path.join(RES_PATH, 'icon-series.png'),
        'path': plugin.url_for('show_series')
    }, {
        'label': _('news'),
        'thumbnail': os.path.join(RES_PATH, 'icon-news.png'),
        'path': plugin.url_for('show_category', id='1', mode='videos')
    }, {
        'label': _('documentaries'),
        'thumbnail': os.path.join(RES_PATH, 'icon-documentaries.png'),
        'path': plugin.url_for('show_category', id='121', mode='videos')
    }, {
        'label': _('most_seen'),
        'thumbnail': os.path.join(RES_PATH, 'icon-mostseen.png'),
        'path': plugin.url_for('show_most_seen', page='1')
    }, {
        'label': 'Level Up',
        'thumbnail': os.path.join(RES_PATH, 'icon-level-up.png'),
        'path': plugin.url_for('show_category', id='147', mode='videos')
    }, {
        'label': _('categories'),
        'path': plugin.url_for('show_category', id='0', mode='categories')
    }, {
        'label': _('search'),
        'thumbnail': os.path.join(RES_PATH, 'icon-search.png'),
        'path': plugin.url_for('show_search_history')
    }]

    plugin.add_items(items)
    return plugin.finish()


@plugin.route('/featured/<page>/')
def show_featured(page):
    items, last_page = vgtv.get_default_video_list(
        url='/editorial/frontpage/assets',
        page=page
    )
    return show_video_list('show_latest', items, page, last_page)


@plugin.route('/mostseen/<page>/')
def show_most_seen(page):
    items, last_page = vgtv.get_default_video_list(
        url='/assets/most-seen',
        page=page,
        params={'interval': 'week', 'page': page}
    )
    return show_video_list('show_most_seen', items, page, last_page)


@plugin.route('/searchhistory/')
def show_search_history(skip_input=False):
    history = plugin.get_storage('search_history')
    searches = history.get('items', [])

    # If we have no items in the search history, open input
    if (skip_input is False and len(searches) == 0):
        return input_search()

    # Always start with the "new search"-option
    items = [{
        'label': _('search') + '...',
        'path': plugin.url_for('input_search'),
        'thumbnail': os.path.join(RES_PATH, 'icon-search.png'),
    }]

    # Loop and add queries from history
    for search in searches:
        items.append({
            'label': search,
            'path': plugin.url_for('show_search', page='1', query=search),
            'thumbnail': os.path.join(RES_PATH, 'icon-search.png'),
            'context_menu': [
                make_remove_from_history_context_item(search)
            ]
        })

    plugin.add_items(items)
    return plugin.finish(
        view_mode='thumbnail',
        update_listing=False
    )

@plugin.route('/search/')
def input_search():
    query = plugin.keyboard(heading=_('search'))

    if query is None or len(str(query)) == 0:
        return

    # Lowercase the search to normalize history
    query = query.lower()

    # Load the search history
    history = plugin.get_storage('search_history')
    searches = history.get('items', [])

    # Remove any previous occurency of the item in history
    if query in searches:
        searches.remove(query)

    # Insert the query to history
    searches.insert(0, query)

    # Have we reached or history limit?
    if len(searches) == 40:
        searches.pop()

    # Store the search history
    history['items'] = searches

    return show_search(1, query)


@plugin.route('/search/<page>/<query>')
def show_search(page='', query=''):
    items, last_page = vgtv.get_default_video_list(
        url='/search',
        page=page,
        params={'query': query}
    )
    return show_video_list('show_search', items, page, last_page, query)

@plugin.route('/series/<page>', options={'page': '1'})
def show_series(page=1):
    categories = vgtv.get_series()
    items = []

    for category in categories:
        items.append(ListItem(
            label=category.get('label'),
            path=category.get('path')
        ))

    return items

@plugin.route('/category/<id>/<page>/<mode>/', options={'page': '1'})
def show_category(id, page=1, mode='all'):
    categories = list()
    videos = list()
    
    if mode == 'categories' or mode == 'all':
        categories = build_category_list(id)

    if mode == 'videos' or mode == 'all':
        videos, last_page = vgtv.get_default_video_list(
            url='/categories/' + id + '/assets',
            page=page
        )

    return plugin.finish(categories + videos)

@plugin.route('/showurl/<url>/<category>/<id>/<title>/<duration>/')
def play_url(url, category=None, id=None, title=None, duration=None):
    track_video_play(id, category, title, duration)
    return plugin.set_resolved_url(url)

@plugin.route('/searchhistory/remove/<query>')
def remove_from_history(query):
    history = plugin.get_storage('search_history')
    searches = history.get('items', [])
    searches.remove(query)
    history['items'] = searches

    return show_search_history(skip_input=True)


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

def make_remove_from_history_context_item(query):
    label = _('remove_from_history')
    new_url = plugin.url_for('remove_from_history', query=query)
    return (label, 'XBMC.Container.Refresh(%s)' % new_url)

# Call tracking
def track_video_play(id, category, title, duration):
    vgtv.track_play(
        id=id,
        category_id=category,
        title=title,
        resolution=get_resolution(),
        duration=duration,
        uid=get_uid()
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

# Get some random user ID
def get_uid():
    user = plugin.get_storage('user')
    uid = user.get('uid')

    if uid is None:
        uid = binascii.b2a_hex(os.urandom(10))
        user.update({ 'uid': uid })

    return uid

if __name__ == '__main__':
    plugin.run()
