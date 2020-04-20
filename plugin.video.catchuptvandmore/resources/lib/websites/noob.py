# -*- coding: utf-8 -*-
'''
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto
    This file is part of Catch-up TV & More.
    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''
# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem

from resources.lib.labels import LABELS
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import re
import urlquick

URL_ROOT = 'http://noob-tv.com'


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


CATEGORIES = {
    'Noob': URL_ROOT + '/videos.php?id=1',
    'WarpZone Project': URL_ROOT + '/videos.php?id=4',
    'Blog de Gaea': URL_ROOT + '/videos.php?id=2',
    'Funglisoft': URL_ROOT + '/videos.php?id=6',
    'Flander'
    's Company': URL_ROOT + '/videos.php?id=7',
    'Emissions': URL_ROOT + '/videos.php?id=5'
}


def root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    for category_name, category_url in list(CATEGORIES.items()):
        item = Listitem()
        item.label = category_name
        item.set_callback(list_shows,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_shows(plugin, item_id, category_url, **kwargs):
    """Build categories listing"""
    resp = urlquick.get(category_url)
    root = resp.parse("p", attrs={"class": "mod-articles-category-introtext"})

    for show in root.iterfind(".//a"):
        item = Listitem()
        item.label = show.text
        show_url = URL_ROOT + '/' + show.get('href')

        item.set_callback(list_videos, item_id=item_id, show_url=show_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, show_url, **kwargs):
    """Build videos listing"""
    resp = urlquick.get(show_url)
    root = resp.parse()

    for episode in root.iterfind(".//div[@class='showcategory']"):
        item = Listitem()
        item.label = episode.find('.//h5').find('a').text.strip()
        video_url = URL_ROOT + '/' + episode.find('.//a').get('href')
        item.art['thumb'] = item.art['landscape'] = URL_ROOT + '/' + episode.find('.//img').get('src')
        item.info['plot'] = ''
        if episode.find(".//span[@class='mod-articles-category-date']"
                        ).text is not None:
            item.info['plot'] = episode.find(
                ".//span[@class='mod-articles-category-date']").text.strip()

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""
    video_html = urlquick.get(video_url).text
    video_id = re.compile(r'www.youtube.com/embed/(.*?)\?').findall(
        video_html)[0]

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)
