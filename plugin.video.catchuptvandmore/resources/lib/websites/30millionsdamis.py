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


from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import re
import urlquick

URL_ROOT = 'http://www.30millionsdamis.fr'


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT + '/actualites/videos')
    root = resp.parse("select", attrs={"class": "selecttourl"})

    for category in root.iterfind("option"):
        item = Listitem()
        item.label = category.text.strip()
        category_url = category.get('value')

        item.set_callback(list_videos,
                          item_id=item_id,
                          page=0,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, page, category_url, **kwargs):
    """Build videos listing"""
    if int(page) > 0:
        resp = urlquick.get(category_url + 'actu-page/%s/' % page)
    else:
        resp = urlquick.get(category_url)
    root = resp.parse("div", attrs={"class": "tt-news"})

    at_least_one_item = False

    for episode in root.iterfind(".//div[@class='news-latest']"):
        at_least_one_item = True
        item = Listitem()
        item.label = episode.find('.//a').get('title')
        video_url = URL_ROOT + episode.find('.//a').get('href')
        item.art['thumb'] = item.art['landscape'] = URL_ROOT + episode.find('.//img').get('src')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    if at_least_one_item:
        yield Listitem.next_page(item_id=item_id,
                                 category_url=category_url,
                                 page=page + 1)
    else:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  video_url,
                  item_id,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""
    video_html = urlquick.get(video_url).text
    video_id = re.compile(r'videoID\=\"(.*?)\"').findall(
        video_html)[0]

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)
