# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations
import json

from xbmcgui import ListItem

from resources.lib import route
from resources.lib import parse
from resources.lib import fetch
from resources.lib.log import log
from resources.lib.favourites import favourites

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from resources.lib.plugin import Plugin
    from resources.lib.typedef import ListItemGenerator


def get_page_data(url: str,
                  params: dict | None = None):
    """Return the JSON data embedded in the HTML of a page."""
    resp = fetch.get(url, params=params)
    data = parse.scrape_json_data(resp.text)
    return data


@route.content
def main_menu(plugin: Plugin) -> ListItemGenerator:
    addon = plugin.addon
    addon_path = addon.getAddonInfo('path')
    main_menu_icon_path = addon_path + '/resources/media/mainmenuicons/'
    list_item = ListItem(label='Home')
    list_item.setArt({"thumb": main_menu_icon_path + 'home.png'})
    yield (route.build_callback('menu/list_page', page_url='https://www.bbc.co.uk/sounds', slug='Home'),
           list_item,
           True)
    list_item = ListItem(label='Music')
    list_item.setArt({"thumb": main_menu_icon_path + 'music.png'})
    yield (route.build_callback('menu/list_page', page_url='https://www.bbc.co.uk/sounds/music', slug='Music'),
           list_item,
           True)
    list_item = ListItem(label='Podcasts')
    list_item.setArt({"thumb": main_menu_icon_path + 'podcast.png'})
    yield (route.build_callback('menu/list_page', page_url='https://www.bbc.co.uk/sounds/podcasts', slug='Podcasts'),
           list_item,
           True)
    list_item = ListItem(label='My Sounds')
    list_item.setArt({"thumb": main_menu_icon_path + 'mysounds.png'})
    yield (route.build_callback('menu/list_page', page_url='https://www.bbc.co.uk/sounds/my', slug='MySounds'),
           list_item,
           True)
    list_item = ListItem(label='Radio')
    list_item.setArt({"thumb": main_menu_icon_path + 'radio.png'})
    yield (route.build_callback('menu/list_page', page_url='https://www.bbc.co.uk/sounds/stations', slug='Radio'),
           list_item,
           True)
    list_item = ListItem(label='Search')
    list_item.setArt({"thumb": main_menu_icon_path + 'search.png'})
    yield (route.build_callback('search/list_search_terms', slug='search'),
           list_item,
           True)


@route.content
def list_page(plugin: Plugin,
              page_url: str,
              slug: str = '') -> ListItemGenerator:
    data = get_page_data(page_url)

    signed_in = data['props']['isSignedIn']
    if plugin.settings.getBool('is-signed-in') != signed_in:
        log("WARNING: Correcting the signed-in status to '%s'.", signed_in)
        plugin.settings.setBool('is-signed-in', signed_in)

    rails = data['props']['pageProps']['dehydratedState']['queries'][-1]['state']['data']['data']
    if page_url.endswith('sounds/my'):
        # Just as well to update the cached subscriptions and bookmarks now we have the data.
        favourites.scrape_urns(rails)

    parser = parse.Parser(plugin, parent_url=page_url, slug=slug)
    yield from parser.parse_items_list(rails)
    plugin.set_sort_methods(parser.sort_methods)


@route.content
def list_rail(plugin: Plugin,
              page_url: str,
              rail_id: str,
              slug: str = '') -> ListItemGenerator:
    """List the contents of a particular rail on a page."""
    if page_url.startswith('https://www.bbc'):
        # Get data from an HTML page
        data = get_page_data(page_url)
        rails = data['props']['pageProps']['dehydratedState']['queries'][-1]['state']['data']['data']
    else:
        # Get json data from an API end point
        resp = fetch.get(page_url)
        rails = json.loads(resp.content)['data']
    parser = parse.Parser(plugin, container_type=rail_id, parent_url=page_url, slug=slug)
    for rail in rails:
        if rail['id'] == rail_id:
            yield from parser.parse_items_list(rail['data'])
            # A possible 'view more' item or something similar.
            yield parser.parse_controls(rail.get('controls'))
            break
    plugin.set_sort_methods(parser.sort_methods)


@route.content
def list_rail_by_url(plugin: Plugin,
                     rail_url: str,
                     slug: str = '',
                     page: str = '1') -> ListItemGenerator:
    """List the contents of a particular rail that has its own url, as opposed to all
     items being embedded in its parent page.

    The main advantage of a separate url is that the response can contain user-related data,
    like whether items are subscribed or on the user's favourite list.

    """
    if 'recommendations' in rail_url:
        max_page_len = 30
    else:
        max_page_len = 100

    resp = fetch.get(rail_url,
                     params={'offset': (int(page) - 1) * max_page_len,
                             'limit': max_page_len})
    resp_data = json.loads(resp.content)
    parser = parse.Parser(plugin, parent_url=rail_url, slug=slug)
    yield from parser.parse_items_list(resp_data['data'])

    if resp_data['total'] > int(page) * max_page_len:
        yield plugin.next_page()


@route.content
def list_container_content(plugin: Plugin,
                           urn: str,
                           slug: str = '',
                           list_clips: str = '',
                           page: str = '1') -> ListItemGenerator:
    parser = parse.Parser(plugin, slug=slug)
    url, container_type = parser.urn2url(urn)
    parser.container_type = container_type
    parser.parent_url = url
    max_page_len = {'category': 100,
                    'tag': 100}.get(container_type, 1000)
    if container_type == 'category':
        params = {'experience': 'domestic',
                  'sort': 'sequential',  # '-release_date',
                  'offset': (int(page) - 1) * max_page_len,
                  'limit': max_page_len}
    else:
        # Try to get everything in one go. Kodi's sorting from its side menu makes very little
        # sense if the items are paginated with a different sort method on the backend.
        # page_size = plugin.settings.getInt('page_len')
        params = {'experience': 'domestic',
                  'sort': 'sequential',
                  'offset': (int(page) - 1) * max_page_len,
                  'limit': max_page_len}
    resp = fetch.get(url, params=params)
    resp_data = json.loads(resp.content)
    items_list = resp_data['data']
    # Separate regular_items from clips:
    regular_items = [dta for dta in items_list if 'clip' not in dta['urn']]
    clips = [dta for dta in items_list if 'clip' in dta['urn']]

    if clips and list_clips == 'true':
        yield from parser.parse_items_list(clips)
        return

    yield from parser.parse_items_list(regular_items)

    if clips:
        li = ListItem('Short Clips')
        li.setProperty('SpecialSort', 'bottom')
        url = route.build_callback('menu/list_container_content',
                                   urn=urn,
                                   list_clips='true',
                                   page=page)
        yield url, li, True

    total_items = resp_data.get('total')
    if total_items and total_items > int(page) * max_page_len:
        yield plugin.next_page()

    plugin.set_sort_methods(parser.sort_methods)
