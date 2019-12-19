# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2018  SylvainCecchetto

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
from resources.lib import resolver_proxy
from resources.lib.listitem_utils import item_post_treatment, item2dict

import re
import urlquick

# TO DO
# Add more button
# test videos to see if there is other video hoster

URL_ROOT = 'https://becurious.ch'

URL_VIDEOS = URL_ROOT + '/?infinity=scrolling'


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
    resp = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse("ul", attrs={"class": "sub-menu"})

    for category_datas in root.iterfind(".//li"):
        category_title = category_datas.find('.//a').text
        category_url = category_datas.find('.//a').get('href')

        item = Listitem()
        item.label = category_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, **kwargs):

    resp = urlquick.get(category_url)
    root = resp.parse()

    for video_datas in root.iterfind(".//article"):
        video_title = video_datas.find('.//a').get('title')
        video_url = video_datas.find('.//a').get('href')
        video_image = video_datas.find('.//img').get('src')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(video_url)
    root = resp.parse()
    stream_datas = root.find('.//iframe').get('src')

    # Case Youtube
    if 'youtube' in stream_datas:
        video_id = re.compile('www.youtube.com/embed/(.*?)[\?\"\&]').findall(
            stream_datas)[0]
        return resolver_proxy.get_stream_youtube(plugin, video_id,
                                                 download_mode, video_label)
    # Case Vimeo
    elif 'vimeo' in stream_datas:
        video_id = re.compile('player.vimeo.com/video/(.*?)[\?\"]').findall(
            stream_datas)[0]
        return resolver_proxy.get_stream_vimeo(plugin, video_id, download_mode,
                                               video_label)
    else:
        # Add Notification
        return False
