#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer
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
import resources.lib.cheez_api as cheez_api

__addon_id__ = 'plugin.image.cheezburger_network'
__addon_name__ = 'Cheezburger Network'

STRINGS = {
    'page': 30000,
    'browse_by_site': 30001,
    'random_by_category': 30002,
    'new_random': 30003,
}

plugin = Plugin(__addon_name__, __addon_id__, __file__)

api = cheez_api.CheezburgerApi(
    developer_key='df1b9bff-ce69-46e7-8732-1035272f3ee7',
    default_count=int(plugin.get_setting('per_page'))
)

force_thumbnail = plugin.get_setting('force_viewmode') == 'true'


@plugin.route('/')
def show_menu():
    items = (
        {'label': _('browse_by_site'),
         'path': plugin.url_for('show_sites')},
        {'label': _('random_by_category'),
         'path': plugin.url_for('show_categories')},
    )
    return plugin.finish(items)


@plugin.route('/sites/')
def show_sites():
    items = [{
        'label': site['title'],
        'thumbnail': site['logo'],
        'path': plugin.url_for(
            'show_content',
            site_id=site['id'],
            page='1',
        ),
    } for site in get_cached(api.get_sites)]
    kwargs = {
        'update_listing': 'update' in plugin.request.args,
        'view_mode': 'thumbnail' if force_thumbnail else None
    }
    return plugin.finish(items, **kwargs)


@plugin.route('/categories/')
def show_categories():
    items = [{
        'label': category['title'],
        'path': plugin.url_for(
            'show_random',
            category_id=category['id'],
        ),
    } for category in get_cached(api.get_categories)]
    return plugin.finish(items)


@plugin.route('/sites/<site_id>/<page>/')
def show_content(site_id, page):
    images = api.get_featured_content(int(site_id), int(page))
    items = [{
        'label': image['title'],
        'thumbnail': image['image'],
        'path': image['image'],
        'is_playable': True,
    } for image in [i for i in images if i['type'] == 'Image']]

    if int(page) > 1:
        prev_page = str(int(page) - 1)
        items.insert(0, {
            'label': '<< %s %s <<' % (_('page'), prev_page),
            'path': plugin.url_for(
                'show_content',
                site_id=site_id,
                page=prev_page,
                update=True,
            ),
        })

    next_page = str(int(page) + 1)
    items.append({
        'label': '>> %s %s >>' % (_('page'), next_page),
        'path': plugin.url_for(
            'show_content',
            site_id=site_id,
            page=next_page,
            update=True,
        ),
    })
    kwargs = {
        'update_listing': 'update' in plugin.request.args,
        'view_mode': 'thumbnail' if force_thumbnail else None,
    }
    return plugin.finish(items, **kwargs)


@plugin.route('/category/<category_id>/random/')
def show_random(category_id):
    items = [{
        'label': image['title'],
        'thumbnail': image['image'],
        'path': image['image'],
        'is_playable': True,
    } for image in api.get_random_lols(int(category_id))]

    items.insert(0, {
        'label': '>> %s <<' % _('new_random'),
        'path': plugin.url_for(
            'show_random',
            category_id=category_id,
            update=True,
        ),
    })
    kwargs = {
        'update_listing': 'update' in plugin.request.args,
        'view_mode': 'thumbnail' if force_thumbnail else None,
    }
    return plugin.finish(items, **kwargs)


def get_cached(func, *args, **kwargs):
    '''Return the result of func with the given args and kwargs
    from cache or execute it if needed'''
    @plugin.cached(kwargs.pop('TTL', 1440))
    def wrap(func_name, *args, **kwargs):
        return func(*args, **kwargs)
    return wrap(func.__name__, *args, **kwargs)


def _(string_id):
    if string_id in STRINGS:
        return plugin.get_string(STRINGS[string_id])
    else:
        plugin.log.warning('String is missing: %s' % string_id)
        return string_id

if __name__ == '__main__':
    try:
        plugin.run()
    except cheez_api.NetworkError:
        plugin.notify(title=__addon_name__, msg=_('network_error'))
