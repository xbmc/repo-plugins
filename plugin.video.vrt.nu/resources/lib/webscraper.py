# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements static functions for scraping the VRT NU website(https://www.vrt.be/vrtnu/)"""

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.error import HTTPError
    from urllib.parse import unquote
    from urllib.request import build_opener, install_opener, urlopen, ProxyHandler
except ImportError:  # Python 2
    from urllib2 import build_opener, HTTPError, install_opener, ProxyHandler, unquote, urlopen

from kodiutils import get_cache, get_setting_bool, get_proxies, log, log_error, ttl, update_cache
from utils import assetpath_to_id, add_https_proto, strip_newlines

install_opener(build_opener(ProxyHandler(get_proxies())))


def valid_categories(categories):
    """Check if categories contain all necessary keys and values"""
    return bool(categories) and all(item.get('id') and item.get('name') for item in categories)


def get_categories():
    """Return a list of categories by scraping the VRT NU website"""

    cache_file = 'categories.json'
    categories = []

    # Try the cache if it is fresh
    categories = get_cache(cache_file, ttl=7 * 24 * 60 * 60)

    # Try to scrape from the web
    if not valid_categories(categories):
        from bs4 import BeautifulSoup, SoupStrainer
        log(2, 'URL get: https://www.vrt.be/vrtnu/categorieen/')
        response = urlopen('https://www.vrt.be/vrtnu/categorieen/')
        tiles = SoupStrainer('nui-list--content')
        soup = BeautifulSoup(response.read(), 'html.parser', parse_only=tiles)

        categories = []
        for tile in soup.find_all('nui-tile'):
            categories.append(dict(
                id=tile.get('href').split('/')[-2],
                thumbnail=get_category_thumbnail(tile),
                name=get_category_title(tile),
            ))
        if categories:
            from json import dumps
            update_cache('categories.json', dumps(categories))

    # Use the cache anyway (better than hard-coded)
    if not valid_categories(categories):
        categories = get_cache(cache_file, ttl=None)

    # Fall back to internal hard-coded categories if all else fails
    if not valid_categories(categories):
        from data import CATEGORIES
        categories = CATEGORIES
    return categories


def get_category_thumbnail(element):
    """Return a category thumbnail, if available"""
    if get_setting_bool('showfanart', default=True):
        raw_thumbnail = element.find(class_='media').get('data-responsive-image', 'DefaultGenre.png')
        return add_https_proto(raw_thumbnail)
    return 'DefaultGenre.png'


def get_category_title(element):
    """Return a category title, if available"""
    found_element = element.find('h3')
    if found_element:
        return strip_newlines(found_element.contents[0])
    # FIXME: We should probably fall back to something sensible here, or raise an exception instead
    return ''


def get_video_attributes(vrtnu_url):
    """Return a dictionary with video attributes by scraping the VRT NU website"""

    # Get cache
    cache_file = 'web_video_attrs_multi.json'
    video_attrs_multi = get_cache(cache_file, ttl=ttl('indirect'))
    if not video_attrs_multi:
        video_attrs_multi = dict()
    if vrtnu_url in video_attrs_multi:
        return video_attrs_multi[vrtnu_url]

    # Scrape video attributes
    from bs4 import BeautifulSoup, SoupStrainer
    log(2, 'URL get: {url}', url=unquote(vrtnu_url))
    try:
        html_page = urlopen(vrtnu_url).read()
    except HTTPError as exc:
        log_error('Web scraping video attributes failed: {error}', error=exc)
        return None
    strainer = SoupStrainer(['section', 'div'], {'class': ['video-player', 'livestream__inner']})
    soup = BeautifulSoup(html_page, 'html.parser', parse_only=strainer)
    item = None
    epg_channel = None
    if '#epgchannel=' in vrtnu_url:
        epg_channel = vrtnu_url.split('#epgchannel=')[1]
    for item in soup:
        if epg_channel and epg_channel == item.get('data-epgchannel'):
            break
    if not epg_channel and len(soup) > 1:
        return None
    try:
        video_attrs = item.find(name='nui-media').attrs
    except AttributeError as exc:
        log_error('Web scraping video attributes failed: {error}', error=exc)
        return None

    # Update cache
    if vrtnu_url in video_attrs_multi:
        # Update existing
        video_attrs_multi[vrtnu_url] = video_attrs
    else:
        # Create new
        video_attrs_multi.update({vrtnu_url: video_attrs})
    from json import dumps
    update_cache(cache_file, dumps(video_attrs_multi))

    return video_attrs


def get_asset_path(vrtnu_url):
    """Return an asset_path by scraping the VRT NU website"""
    video_attrs = get_video_attributes(vrtnu_url)
    asset_path = video_attrs.get('assetpath')
    return asset_path


def get_asset_id(vrtnu_url):
    """Return an asset_id by scraping the VRT NU website"""
    asset_id = assetpath_to_id(get_asset_path(vrtnu_url))
    return asset_id
