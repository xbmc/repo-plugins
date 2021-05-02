# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Fix Replay (DRM)

URL_API = 'https://watch.blaze.tv'
# Live
URL_LIVE = URL_API + '/live/'
URL_LIVE_JSON = 'https://live.blaze.tv/stream-live.php?key=%s&platform=chrome'
# Key

# Replay
URL_REPLAY = URL_API + '/replay/553'
# pageId
URL_INFO_REPLAY = URL_API + '/watch/replay/%s'
URL_REPLAY_TOKEN = URL_API + '/stream/replay/widevine/%s'
# video ID


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(30701)
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
        if video_datas.find('.//img') is not None:
            video_title = video_datas.find('.//img').get('alt')
        if video_datas.find(".//span[@class='pull-left']") is not None:
            video_title = '{} - {}'.format(
                video_title,
                video_datas.find(".//span[@class='pull-left']").text)
        video_image = video_datas.find('.//img').get('data-src')
        video_id = video_datas.find('.//a').get('data-video-id')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(URL_INFO_REPLAY % video_id)
    stream_id = re.compile(
        r'uvid\"\:\"(.*?)\"').findall(resp.text)[2]

    resp2 = urlquick.get(URL_REPLAY_TOKEN % stream_id,
                         headers={'X-Requested-With': 'XMLHttpRequest'})
    json_parser = json.loads(resp2.text)

    video_url = json_parser['tokenizer']['url']
    token_value = json_parser['tokenizer']['token']
    token_expiry_value = json_parser['tokenizer']['expiry']
    uvid_value = json_parser['tokenizer']['uvid']
    resp3 = urlquick.get(video_url,
                         headers={'User-Agent': web_utils.get_random_ua(),
                                  'token': token_value,
                                  'token-expiry': token_expiry_value,
                                  'uvid': uvid_value},
                         max_age=-1)
    json_parser2 = json.loads(resp3.text)
    return json_parser2["Streams"]["Adaptive"]


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

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
