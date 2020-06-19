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

from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import re
import urlquick

# TODO
# Add Replay

URL_ROOT = "http://www.telegrenoble.net"

URL_LIVE = URL_ROOT + '/direct.html'

URL_REPLAY = URL_ROOT + '/replay.html'

URL_VIDEOS = URL_ROOT + '/views/htmlFragments/replayDetail_pages.php?page=%s&elementsPerPage=10&idEmission=%s'
# Page, Category_Id


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
    resp = urlquick.get(URL_REPLAY)
    root = resp.parse()

    for category_datas in root.iterfind(".//div[@class='emission black']"):
        category_name = category_datas.find('.//a').text
        category_image = URL_ROOT + '/' + category_datas.find('.//img').get('src')
        category_plot = category_datas.find(".//div[@class='description']").text
        category_id = re.compile(
            r'fichiers\/emissions\/(.*?)\/').findall(category_datas.find('.//img').get('src'))[0]

        item = Listitem()
        item.label = category_name
        item.art['thumb'] = item.art['landscape'] = category_image
        item.info['plot'] = category_plot
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_id=category_id,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_id, page, **kwargs):

    resp = urlquick.get(URL_VIDEOS % (page, category_id))
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='replay campton-light']"):
        video_title = video_datas.find('.//a').get('title')
        video_image = video_datas.find('.//img').get('src')
        video_plot = video_datas.find(".//div[@class='description']").text
        video_url = URL_ROOT + '/' + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

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

    resp = urlquick.get(video_url)
    video_id = re.compile(
        r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin,
                                                 video_id,
                                                 download_mode)


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(
        URL_LIVE, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    live_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin,
                                                 live_id,
                                                 False)
