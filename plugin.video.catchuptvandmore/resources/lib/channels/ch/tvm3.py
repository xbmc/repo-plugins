# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Get Image

URL_ROOT = 'http://www.tvm3.tv'

# Replay
URL_REPLAY = URL_ROOT + '/replay'

URL_STREAM = 'https://livevideo.infomaniak.com/iframe.php?stream=tvm3&name=html5&player=%s'
# player_id


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_REPLAY)
    root = resp.parse()

    for program_datas in root.iterfind(
            ".//div[@class='uk-panel uk-panel-hover']"):
        program_title = program_datas.find('.//img').get('alt')
        program_image = URL_ROOT + program_datas.find('.//img').get('src')
        program_url = URL_ROOT + program_datas.find('.//a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()
    list_videos_datas = root.findall(
        ".//div[@class='uk-panel uk-panel-hover uk-invisible']")
    list_videos_datas += root.findall(
        ".//div[@class='uk-panel uk-panel-space uk-invisible']")

    is_youtube = False

    for video_datas in list_videos_datas:
        video_title = video_datas.find('.//h3').find('.//a').text
        if video_datas.find(".//div[@class='youtube-player']") is not None:
            video_id = video_datas.find(".//div[@class='youtube-player']").get(
                'data-id')
            is_youtube = True
        elif video_datas.find('.//iframe'):
            video_id = re.compile(
                r'player.vimeo.com/video/(.*?)[\?\"]').findall(
                    video_datas.find('.//iframe').get('src'))[0]
        else:
            video_id = None

        if video_id is not None:
            item = Listitem()
            item.label = video_title

            item.set_callback(
                get_video_url,
                item_id=item_id,
                video_id=video_id,
                is_youtube=is_youtube)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  is_youtube,
                  download_mode=False,
                  **kwargs):

    if is_youtube:
        return resolver_proxy.get_stream_youtube(plugin, video_id,
                                                 download_mode)
    return resolver_proxy.get_stream_vimeo(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    player_id = re.compile(r'\;player\=(.*?)\'').findall(resp.text)[0]
    session_urlquick = urlquick.Session(allow_redirects=False)
    resp2 = session_urlquick.get(
        URL_STREAM % player_id,
        headers={'User-Agent': web_utils.get_random_ua()},
        max_age=-1)
    location_url = resp2.headers['Location']
    resp3 = urlquick.get(location_url.replace(
        'infomaniak.com/', 'infomaniak.com/playerConfig.php'),
        max_age=-1)
    json_parser = json.loads(resp3.text)
    stream_url = ''
    for stram_datas in json_parser['data']['integrations']:
        if 'hls' in stram_datas['type']:
            stream_url = stram_datas['url']
    return stream_url
