# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2019  SylvainCecchetto

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
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import json
import re
import urlquick

# TO DO

URL_ROOT = 'https://www.at5.nl'

URL_LIVE = URL_ROOT + '/tv'

URL_VIDEOS = 'https://at5news.vinsontv.com/api/news?source=web&slug=%s&page=%s'
# slug, page


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_ROOT)
    root = resp.parse("ul", attrs={"class": "nav-bar-mobile-submenu "})

    for category_datas in root.iterfind(".//li"):

        category_title = category_datas.find('a').text
        category_slug = category_datas.find('a').get('href').replace('/', '')

        item = Listitem()
        item.label = category_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_slug=category_slug,
                          page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_slug, page, **kwargs):

    resp = urlquick.get(URL_VIDEOS % (category_slug, page))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["category"]["news"]:
        if video_datas["video"]:
            video_title = video_datas["title"]
            video_image = video_datas["media"][0]["image"]
            video_plot = utils.strip_tags(video_datas["text"])
            video_url = None
            video_id = None
            if 'url' in video_datas["media"][0]:
                video_url = video_datas["media"][0]["url"]
            elif 'youtube.com/embed' in video_datas["text"]:
                video_id = re.compile(r'youtube\.com\/embed\/(.*?)\"').findall(
                    video_datas["text"])[0]

            if video_url is not None:
                item = Listitem()
                item.label = video_title
                item.art['thumb'] = item.art['landscape'] = video_image
                item.info['plot'] = video_plot

                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_url=video_url)
                item_post_treatment(item,
                                    is_playable=True,
                                    is_downloadable=True)
                yield item

            if video_id is not None:
                item = Listitem()
                item.label = video_title
                item.art['thumb'] = item.art['landscape'] = video_image
                item.info['plot'] = video_plot

                item.set_callback(get_video_yt_url,
                                  item_id=item_id,
                                  video_id=video_id)
                item_post_treatment(item,
                                    is_playable=True,
                                    is_downloadable=True)
                yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             category_slug=category_slug,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    if download_mode:
        return download.download_video(video_url)
    return video_url


@Resolver.register
def get_video_yt_url(plugin,
                     item_id,
                     video_id,
                     download_mode=False,
                     **kwargs):

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_LIVE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    return re.compile(r'videoStream\"\:\"(.*?)\"').findall(resp.text)[0]
