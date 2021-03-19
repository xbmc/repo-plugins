# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

import inputstreamhelper
from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import web_utils
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Add FUJITV Replay in Kodi 18 is out (DRM protected) 'cx' channel

URL_ROOT = 'https://tver.jp'

URL_REPLAY_BY_TV = URL_ROOT + '/%s'
# channel

URL_BRIGHTCOVE_POLICY_KEY = 'http://players.brightcove.net/%s/%s_default/index.min.js'
# AccountId, PlayerId

URL_BRIGHTCOVE_VIDEO_JSON = 'https://edge.api.brightcove.com/'\
                            'playback/v1/accounts/%s/videos/%s'
# AccountId, VideoId


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    category_title = plugin.localize(30701)
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
    list_videos_datas = root.find(".//div[@class='listinner']").findall(
        './/li')

    for video_data in list_videos_datas:
        video_title = video_data.find('.//h3').text
        video_image = ''
        if video_data.find(".//div[@class='picinner lazyload']") is not None:
            video_image = video_data.find(".//div[@class='picinner lazyload']").get('data-bg')
        video_plot = ''
        if video_data.find(".//p[@class='summary']") is not None:
            video_plot = video_data.find(".//p[@class='summary']").text
        video_url = URL_ROOT + video_data.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item


# BRIGHTCOVE Part
def get_brightcove_policy_key(data_account, data_player):
    """Get policy key"""
    file_js = urlquick.get(URL_BRIGHTCOVE_POLICY_KEY %
                           (data_account, data_player))
    return re.compile('policyKey:"(.+?)"').findall(file_js.text)[0]


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

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

    # Method to get JSON from 'edge.api.brightcove.com'
    resp = urlquick.get(
        URL_BRIGHTCOVE_VIDEO_JSON % (data_account, data_video_id),
        headers={
            'User-Agent':
            web_utils.get_random_ua(),
            'Accept':
            'application/json;pk=%s' %
            (get_brightcove_policy_key(data_account, data_player)),
            'X-Forwarded-For':
            plugin.setting.get_string('header_x-forwarded-for')
        })
    json_parser = json.loads(resp.text)

    video_url = ''
    if 'sources' in json_parser:
        for url in json_parser["sources"]:
            if 'src' in url:
                if 'manifest.mpd' in url["src"]:
                    video_url = url["src"]
    else:
        if json_parser[0]['error_code'] == "ACCESS_DENIED":
            plugin.notify('ERROR', plugin.localize(30713))
            return False

    if video_url == '':
        return False

    item = Listitem()
    item.path = video_url
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    return item
