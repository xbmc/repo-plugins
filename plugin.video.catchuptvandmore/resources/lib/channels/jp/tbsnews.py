# -*- coding: utf-8 -*-
"""
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
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import urlquick

URL_ROOT = 'http://news.tbs.co.jp'

URL_CONTENT = URL_ROOT + '/digest/%s.html'
# content

URL_STREAM = 'http://flvstream.tbs.co.jp/flvfiles/_definst_/newsi/digest/%s_1m.mp4/playlist.m3u8'
# content

NEWS_CONTENT = ['nb', '23', 'nst', 'jnn']


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
    category_title = 'TBS ニュース'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos_news, item_id=item_id)
    item_post_treatment(item)
    yield item

    category_title = 'TBS ニュース - 気象'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos_weather, item_id=item_id)
    item_post_treatment(item)
    yield item


@Route.register
def list_videos_news(plugin, item_id, **kwargs):

    for content in NEWS_CONTENT:
        resp = urlquick.get(URL_CONTENT % content)
        root = resp.parse()
        video_news_datas = root.find(".//article[@class='md-mainArticle']")

        video_title = video_news_datas.findall(".//img[@class='lazy']")[0].get(
            'alt')
        video_image = URL_ROOT + video_news_datas.findall(
            ".//img[@class='lazy']")[0].get('data-original')
        video_url = URL_STREAM % content

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos_weather(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_CONTENT % 'weather')
    root = resp.parse()
    video_weather_datas = root.find(".//article[@class='md-mainArticle']")

    video_title = video_weather_datas.findall(".//img[@class='lazy']")[0].get(
        'alt')
    video_image = URL_ROOT + video_weather_datas.findall(
        ".//img[@class='lazy']")[0].get('data-original')
    video_url = URL_STREAM % 'weather'

    item = Listitem()
    item.label = video_title
    item.art['thumb'] = item.art['landscape'] = video_image

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
    if download_mode:
        return download.download_video(video_url)
    return video_url
