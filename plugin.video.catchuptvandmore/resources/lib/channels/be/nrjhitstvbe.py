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
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import json
import re
import urlquick

# TO DO

URL_ROOT = 'https://www.nrj.be'

URL_LIVE = URL_ROOT + '/tv'

URL_STREAM = 'https://services.brid.tv/services/get/video/%s/%s.json'

URL_VIDEOS = URL_ROOT + '/replay/videos'


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_videos(plugin, item_id)


@Route.register
def list_videos(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_VIDEOS)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='col-nrj-card']"):
        if video_datas.find(".//a") is not None:
            video_title = video_datas.find(".//div[@class='nrj-card__text']").text
            video_image_datas = video_datas.find(".//div[@class='nrj-card__pict']").get('style')
            video_image = re.compile(
                r'url\((.*?)\)').findall(video_image_datas)[0]
            video_url = URL_ROOT + video_datas.find(".//a").get('href')

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

    resp = urlquick.get(video_url, max_age=-1)
    data_player = re.compile(r'data-video-player-id\=\"(.*?)\"').findall(
        resp.text)[0]
    data_video_id = re.compile(r'data-video-id\=\"(.*?)\"').findall(
        resp.text)[0]

    resp2 = urlquick.get(
        URL_STREAM % (data_player, data_video_id), max_age=-1)
    json_parser2 = json.loads(resp2.text)
    return 'https:' + json_parser2["Video"][0]["source"]["hd"]


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    data_player = re.compile(r'data-video-player-id\=\"(.*?)\"').findall(
        resp.text)[0]
    data_video_id = re.compile(r'data-video-id\=\"(.*?)\"').findall(
        resp.text)[0]

    resp2 = urlquick.get(
        URL_STREAM % (data_player, data_video_id), max_age=-1)
    json_parser2 = json.loads(resp2.text)
    return json_parser2["Video"][0]["source"]["sd"]
