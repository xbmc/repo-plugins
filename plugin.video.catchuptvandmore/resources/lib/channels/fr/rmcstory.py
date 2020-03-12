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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import json
import urlquick

# TO DO
# Get year from Replay

URL_ROOT = 'https://rmcstory.bfmtv.com'

URL_REPLAY_RMCSTORY = URL_ROOT + '/mediaplayer-replay/nouveautes/'

URL_LIVE_RMCSTORY = URL_ROOT + '/mediaplayer-direct/'


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
    resp = urlquick.get(URL_REPLAY_RMCSTORY)
    root = resp.parse("div", attrs={"class": "list_21XUu"})

    for category_datas in root.iterfind(".//a"):
        category_title = category_datas.text
        category_url = URL_ROOT + category_datas.get('href')

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

    for video_datas in root.iterfind(".//div[@class='root_qT0Me']"):
        if video_datas.find(".//p[@class='subtitle_1hI_I']").text is not None:
            if video_datas.find(".//p[@class='title_1APl2']").text is not None:
                video_title = video_datas.find(
                    ".//p[@class='title_1APl2']").text + ' - ' + video_datas.find(
                        ".//p[@class='subtitle_1hI_I']").text
            else:
                video_title = video_datas.find(".//p[@class='subtitle_1hI_I']").text
        else:
            video_title = video_datas.find(".//p[@class='title_1APl2']").text
        video_image = video_datas.find('.//img').get('src')
        video_url = URL_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

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

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    root = resp.parse()
    video_datas = root.find(".//div[@class='next-player player_2t_e9']")

    data_account = video_datas.get('data-account')
    data_video_id = video_datas.get('data-video-id')
    data_player = video_datas.get('data-player')

    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id,
                                                    download_mode)


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_LIVE_RMCSTORY,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)

    root = resp.parse()
    live_datas = root.find(".//div[@class='next-player player_2t_e9']")

    data_account = live_datas.get('data-account')
    data_video_id = live_datas.get('data-video-id')
    data_player = live_datas.get('data-player')

    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id)
