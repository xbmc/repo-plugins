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
from resources.lib import resolver_proxy
from resources.lib.listitem_utils import item_post_treatment, item2dict

import re
import urlquick

# TO DO
# Add FUJITV Replay in Kodi 18 is out (DRM protected) 'cx' channel

URL_ROOT = 'https://tver.jp'

URL_REPLAY_BY_TV = URL_ROOT + '/%s'
# channel


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
    category_title = plugin.localize(LABELS['All videos'])
    category_url = URL_REPLAY_BY_TV % item_id

    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos, item_id=item_id, category_url=category_url)
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, category_url, **kwargs):

    resp = urlquick.get(category_url)
    root = resp.parse()
    if item_id == 'cx':
        list_videos_datas = root.find(".//div[@class='listinner']").findall(
            './/li')
    else:
        list_videos_datas = root.findall(".//li[@class='resumable']")

    for video_data in list_videos_datas:
        video_title = video_data.find('.//h3').text
        video_image = re.compile(r'url\((.*?)\);').findall(
            video_data.find(".//div[@class='picinner']").get('style'))[0]
        video_plot = video_data.find(".//p[@class='summary']").text
        video_url = URL_ROOT + video_data.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot

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

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    stream_datas = resp.text.split('addPlayer(')[1].split(');')[0].replace(
        "\n", "").replace("\r", "").split(',')
    data_account = stream_datas[0].strip().replace("'", "")
    data_player = stream_datas[1].strip().replace("'", "")
    if item_id == 'tx':
        data_video_id = stream_datas[4].strip().replace("'", "")
    else:
        data_video_id = 'ref:' + stream_datas[4].strip().replace("'", "")
    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id,
                                                    download_mode, video_label)
