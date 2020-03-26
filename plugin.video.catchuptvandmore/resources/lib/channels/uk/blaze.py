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

import json
import re
import urlquick

# TO DO
# Fix Replay (DRM)

URL_ROOT = 'http://www.blaze.tv'

URL_API = 'https://watch.blaze.tv'
# Live
URL_LIVE = URL_API + '/live/'
URL_LIVE_JSON = 'https://live.blaze.tv/stream-live.php?key=%s&platform=chrome'
# Key

# Replay
URL_REPLAY = URL_ROOT + '/replay/'
# pageId
URL_REPLAY_JSON = 'https://vod.blaze.tv/stream-vod.php?key=%s&platform=chrome'


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(LABELS['All videos'])
    item.set_callback(list_videos, item_id=item_id)
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_REPLAY)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='col-xs-12 col-sm-6 col-md-3']"):

        video_title = ''
        if video_datas.find('.//h3') is not None:
            video_title = video_datas.find('.//h3').text
        if video_datas.find(".//span[@class='pull-left']") is not None:
            video_title = video_title + ' - ' + video_datas.find(".//span[@class='pull-left']").text
        video_image = video_datas.find('.//img').get('data-src')
        video_url = URL_API + video_datas.find('.//a').get('href')

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

    resp = urlquick.get(video_url)

    key_value = re.compile(
        r'data-key\=\"(.*?)\"').findall(resp.text)[0]
    token_value = re.compile(
        r'data-token\=\"(.*?)\"').findall(resp.text)[0]
    token_expiry_value = re.compile(
        r'data-expiry\=\"(.*?)\"').findall(resp.text)[0]
    uvid_value = re.compile(
        r'data-uvid\=\"(.*?)\"').findall(resp.text)[0]
    resp2 = urlquick.get(
        URL_REPLAY_JSON % key_value,
        headers={
            'User-Agent': web_utils.get_random_ua(),
            'token': token_value,
            'token-expiry': token_expiry_value,
            'uvid': uvid_value
        },
        max_age=-1)
    json_parser2 = json.loads(resp2.text)
    return json_parser2["Streams"]["Adaptive"]


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    live_id = re.compile(
        r'data-player-key\=\"(.*?)\"').findall(resp.text)[0]
    token_value = re.compile(
        r'data-player-token\=\"(.*?)\"').findall(resp.text)[0]
    token_expiry_value = re.compile(
        r'data-player-expiry\=\"(.*?)\"').findall(resp.text)[0]
    uvid_value = re.compile(
        r'data-player-uvid\=\"(.*?)\"').findall(resp.text)[0]
    resp2 = urlquick.get(
        URL_LIVE_JSON % live_id,
        headers={
            'User-Agent': web_utils.get_random_ua(),
            'token': token_value,
            'token-expiry': token_expiry_value,
            'uvid': uvid_value
        },
        max_age=-1)
    json_parser2 = json.loads(resp2.text)
    return json_parser2["Streams"]["Adaptive"]
