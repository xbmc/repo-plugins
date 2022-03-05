# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json

import urlquick
from codequick import Listitem, Resolver, Route
from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

# TO DO
# Add More Pages

URL_API = 'https://api.canalplus.pro'
# ChannelName

URL_VIDEOS = URL_API + '/creativemedia/video'


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    headers = {
        'x-minisite-domain':
        'jack.canalplus.com',
        'User-Agent':
        web_utils.get_random_ua()
    }
    resp = urlquick.get(URL_VIDEOS, headers=headers)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser["blocks"]:
        if program_datas["container"] != 'content':
            continue

        if 'template' not in program_datas["content"]:
            continue

        program_title = program_datas["content"]["title"]

        item = Listitem()
        item.label = program_title
        item.set_callback(list_videos, item_id=item_id, program_title=program_title)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_title, **kwargs):

    headers = {
        'X-MINISITE-DOMAIN':
        'jack.canalplus.com',
        'User-Agent':
        web_utils.get_random_ua()
    }
    resp = urlquick.get(URL_VIDEOS, headers=headers)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser["blocks"]:
        if program_datas["container"] != 'content':
            continue

        if 'template' not in program_datas["content"]:
            continue

        if program_title != program_datas["content"]["title"]:
            continue

        for video_datas in program_datas["content"]["articles"]:
            if 'video' not in video_datas:
                continue

            video_title = video_datas["title"]
            video_image = ''
            if 'links' in video_datas["mainMedia"]["default"]:
                video_image = video_datas["mainMedia"]["default"]["links"][0]["href"]
                video_image = video_image.replace('{width}', '800').replace('{height}', '450')
            video_plot = video_datas["abstract"]
            video_id = video_datas["video"]["id"]
            video_source = video_datas["video"]["source"]
            date_value = video_datas["publishedAt"].split('T')[0]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['plot'] = video_plot
            item.info.date(date_value, '%Y-%m-%d')

            item.set_callback(
                get_video_url,
                item_id=item_id,
                video_id=video_id,
                video_source=video_source)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  video_source,
                  download_mode=False,
                  **kwargs):

    if 'youtube' in video_source:
        return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)

    if 'dailymotion' in video_source:
        return resolver_proxy.get_stream_dailymotion(plugin, video_id, download_mode)
