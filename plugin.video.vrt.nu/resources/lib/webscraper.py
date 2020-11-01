# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements static functions for scraping the VRT NU website(https://www.vrt.be/vrtnu/)"""

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.error import HTTPError
except ImportError:  # Python 2
    from urllib2 import HTTPError

from kodiutils import get_cache, log_error, open_url, ttl, update_cache
from utils import assetpath_to_id


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
    try:
        response = open_url(vrtnu_url, raise_errors='all')
    except HTTPError as exc:
        log_error('Web scraping video attributes failed: {error}', error=exc)
        return None
    if response is None:
        return None
    html_page = response.read()
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
