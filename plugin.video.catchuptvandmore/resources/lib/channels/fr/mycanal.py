# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017 SylvainCecchetto

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
from resources.lib import download


import re
import json
import urlquick

# TO DO
# Wait Kodi 18 to use live with DRM

# URL :
URL_ROOT_SITE = 'https://www.mycanal.fr'
# Channel

# Replay channel :
URL_REPLAY = URL_ROOT_SITE + '/chaines/%s'
# Channel name


# Dailymotion Id get from these pages below
# - http://www.dailymotion.com/cstar
# - http://www.dailymotion.com/canalplus
# - http://www.dailymotion.com/C8TV
LIVE_DAILYMOTION_ID = {
    'c8': 'x5gv5rr',
    'cstar': 'x5gv5v0',
    'canalplus': 'x5gv6be'
}


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_REPLAY % item_id)
    json_replay = re.compile(
        'window.__data=(.*?)};').findall(resp.text)[0]
    json_parser = json.loads(json_replay + ('}'))

    for category in json_parser["landing"]["strates"]:
        if category["type"] == "contentRow" or \
                category["type"] == "contentGrid":
            if 'title' in category:
                title = category['title']
            else:
                title = json_parser["page"]["displayName"]

            item = Listitem()
            item.label = title
            item.set_callback(
                list_contents,
                item_id=item_id,
                title_value=title)
            yield item


@Route.register
def list_contents(plugin, item_id, title_value):

    resp = urlquick.get(URL_REPLAY % item_id)
    json_replay = re.compile(
        'window.__data=(.*?)};').findall(resp.text)[0]
    json_parser = json.loads(json_replay + ('}'))

    for category in json_parser["landing"]["strates"]:
        if category["type"] == "contentRow" or \
                category["type"] == "contentGrid":
            if 'title' in category:
                title = category['title']
            else:
                title = json_parser["page"]["displayName"]

            if title_value == title:
                for content in category["contents"]:
                    if content["type"] == 'quicktime' or content["type"] == 'pfv' or content["type"] == 'detailPage':
                        video_title = content["onClick"]["displayName"]
                        video_image = content['URLImage']
                        if content["type"] == 'quicktime':
                            video_url = content["onClick"]["URLMedias"]
                        else:
                            resp2 = urlquick.get(content["onClick"]["URLPage"])
                            json_parser2 = json.loads(resp2.text)
                            video_url = json_parser2['detail']['informations']['URLMedias']

                        item = Listitem()
                        item.label = video_title
                        item.art['thumb'] = video_image
                        item.set_callback(
                            get_video_url,
                            item_id=item_id,
                            next_url=video_url)
                        yield item
                    elif content["type"] == 'article':
                        continue
                    else:
                        program_title = content["onClick"]["displayName"]
                        program_image = content['URLImage']
                        program_url = content["onClick"]["URLPage"]

                        item = Listitem()
                        item.label = program_title
                        item.art['thumb'] = program_image
                        item.set_callback(
                            list_sub_programs,
                            item_id=item_id,
                            next_url=program_url)
                        yield item


@Route.register
def list_sub_programs(plugin, item_id, next_url):

    resp = urlquick.get(next_url)
    json_parser = json.loads(resp.text)

    if 'strates' in json_parser:
        for sub_program_datas in json_parser["strates"]:

            if sub_program_datas['type'] == 'plainTextHTML':
                continue
            
            if sub_program_datas['type'] == 'carrousel':
                continue

            if 'title' in sub_program_datas:
                sub_program_title = sub_program_datas["title"]

                item = Listitem()
                item.label = sub_program_title
                item.set_callback(
                    list_videos,
                    item_id=item_id,
                    next_url=next_url,
                    sub_program_title=sub_program_title)
                yield item
            else:
                sub_program_title = json_parser["currentPage"]["displayName"]

                item = Listitem()
                item.label = sub_program_title
                item.set_callback(
                    list_videos,
                    item_id=item_id,
                    next_url=next_url,
                    sub_program_title=sub_program_title)
                yield item

    elif 'seasons' in json_parser['detail']:
        for seasons_datas in json_parser['detail']['seasons']:
            season_title = seasons_datas['onClick']['displayName']
            season_url = seasons_datas['onClick']['URLPage']

            item = Listitem()
            item.label = season_title
            item.set_callback(
                list_videos_seasons,
                item_id=item_id,
                next_url=season_url)
            yield item


@Route.register
def list_videos_seasons(plugin, item_id, next_url):

    resp = urlquick.get(next_url)
    json_parser = json.loads(resp.text)

    program_title = json_parser['currentPage']['displayName']

    for video_datas in json_parser['episodes']['contents']:
        video_title = program_title + ' ' + video_datas['title'] + ' ' + video_datas['subtitle']
        video_image = video_datas['URLImage']
        video_plot = video_datas['summary']
        video_url = video_datas['URLMedias']

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            next_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            next_url=video_url)
        yield item


@Route.register
def list_videos(plugin, item_id, next_url, sub_program_title):

    resp = urlquick.get(next_url)
    json_parser = json.loads(resp.text)

    for sub_program_datas in json_parser["strates"]:
        if 'title' in sub_program_datas:
            if sub_program_title == sub_program_datas["title"]:
                if 'contents' in sub_program_datas:
                    for video_datas in sub_program_datas["contents"]:
                        if video_datas["type"] == 'quicktime' or video_datas["type"] == 'pfv' or video_datas["type"] == 'VoD' or video_datas["type"] == 'detailPage':
                            if 'title' in video_datas:
                                if 'subtitle' in video_datas:
                                    video_title = video_datas['subtitle'] + ' - ' + video_datas['title']
                                else:
                                    video_title = video_datas['title']
                            else:
                                video_title = video_datas["onClick"]["displayName"]
                            video_image = video_datas['URLImage']
                            video_url = ''
                            if video_datas["type"] == 'quicktime':
                                video_url = video_datas["onClick"]["URLMedias"]
                            else:
                                resp2 = urlquick.get(video_datas["onClick"]["URLPage"])
                                json_parser2 = json.loads(resp2.text)
                                video_url = json_parser2['detail']['informations']['URLMedias']

                            item = Listitem()
                            item.label = video_title
                            item.art['thumb'] = video_image

                            item.context.script(
                                get_video_url,
                                plugin.localize(LABELS['Download']),
                                item_id=item_id,
                                next_url=video_url,
                                video_label=LABELS[item_id] + ' - ' + item.label,
                                download_mode=True)

                            item.set_callback(
                                get_video_url,
                                item_id=item_id,
                                next_url=video_url)
                            yield item
        else:
            if sub_program_title == json_parser["currentPage"]["displayName"]:
                if 'contents' in sub_program_datas:
                    for video_datas in sub_program_datas["contents"]:
                        if video_datas["type"] == 'quicktime' or video_datas["type"] == 'pfv' or video_datas["type"] == 'VoD' or video_datas["type"] == 'detailPage':
                            if 'title' in video_datas:
                                if 'subtitle' in video_datas:
                                    video_title = video_datas['subtitle'] + ' - ' + video_datas['title']
                                else:
                                    video_title = video_datas['title']
                            else:
                                video_title = video_datas["onClick"]["displayName"]
                            video_image = video_datas['URLImage']
                            video_url = ''
                            if video_datas["type"] == 'quicktime':
                                video_url = video_datas["onClick"]["URLMedias"]
                            else:
                                resp2 = urlquick.get(video_datas["onClick"]["URLPage"])
                                json_parser2 = json.loads(resp2.text)
                                video_url = json_parser2['detail']['informations']['URLMedias']

                            item = Listitem()
                            item.label = video_title
                            item.art['thumb'] = video_image

                            item.context.script(
                                get_video_url,
                                plugin.localize(LABELS['Download']),
                                item_id=item_id,
                                next_url=video_url,
                                video_label=LABELS[item_id] + ' - ' + item.label,
                                download_mode=True)

                            item.set_callback(
                                get_video_url,
                                item_id=item_id,
                                next_url=video_url)
                            yield item


@Resolver.register
def get_video_url(
        plugin, item_id, next_url, download_mode=False, video_label=None):

    resp = urlquick.get(
        next_url,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    json_parser = json.loads(resp.text)

    if json_parser["detail"]["informations"]['consumptionPlatform'] == 'HAPI':
        Script.notify(
            "INFO",
            plugin.localize(LABELS['drm_notification']),
            Script.NOTIFY_INFO)
        return False

    stream_url = ''
    for stream_datas in json_parser["detail"]["informations"]["videoURLs"]:
        if stream_datas["encryption"] == 'clear':
            stream_url = stream_datas["videoURL"]

    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    return resolver_proxy.get_stream_dailymotion(
        plugin, LIVE_DAILYMOTION_ID[item_id], False)
