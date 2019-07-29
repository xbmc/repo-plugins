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

import re
import json

from codequick import Route, Resolver, Listitem
import urlquick

from resources.lib.labels import LABELS
from resources.lib import resolver_proxy
from resources.lib.listitem_utils import item_post_treatment, item2dict

URL_ROOT = 'https://national.fff.fr'

URL_REPLAY = URL_ROOT + '/#replay'

# TODO Add Live


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    resp = urlquick.get(URL_REPLAY)
    list_categories_title = re.compile(
        r'title                 : \'(.*?)\'').findall(resp.text)

    category_id = 0
    for category_title in list_categories_title:
        item = Listitem()
        item.label = category_title
        category_id += 1

        item.set_callback(list_videos,
                          item_id=item_id,
                          category_id=category_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_id, **kwargs):
    """Build videos listing"""

    resp = urlquick.get(URL_REPLAY)
    list_videos_datas = re.compile(r'videos            : \[(.*?)\]').findall(
        resp.text)

    json_parser = json.loads('[' + list_videos_datas[category_id - 1] + ']')

    for video_datas in json_parser:
        video_title = video_datas['overlayTitle']
        video_image = ''
        if 'backgroundImage' in video_datas:
            video_image = video_datas['backgroundImage']
        video_id = video_datas['dailymotionId']

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        if 'overlayDescription' in video_datas:
            date_value = video_datas['overlayDescription'].split('|')[0]
            item.info.date(date_value, '%d/%m/%Y')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  video_label=None,
                  **kwargs):
    """Get video URL and start video player"""

    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode, video_label)
