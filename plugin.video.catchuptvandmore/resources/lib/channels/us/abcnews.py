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


from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import json
import urlquick

# TO DO
# Fix Video 404 / other type stream video (detect and implement)

URL_ROOT = 'https://abcnews.go.com'

# Stream
URL_LIVE_STREAM = URL_ROOT + '/video/itemfeed?id=abc_live11&secure=true'

URL_REPLAY_STREAM = URL_ROOT + '/video/itemfeed?id=%s'
# videoId


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_ROOT)
    root = resp.parse("div", attrs={"class": "shows-dropdown"})

    for program_datas in root.iterfind(".//li"):
        if 'View' in program_datas.find(".//span[@class='link-text']").text:
            program_title = program_datas.find(
                ".//span[@class='link-text']").text
            program_url = program_datas.find('.//a').get('href')

            item = Listitem()
            item.label = program_title
            item.set_callback(list_videos,
                              item_id=item_id,
                              program_url=program_url)
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()
    for script_data in root.iterfind(".//script[@type='text/javascript']"):
        if script_data.text and "__abcnews__" in script_data.text:
            script = script_data.text
            page_data = script[script.find('{'):script.rfind('}') + 1]
            json_parser = json.loads(page_data)
            for element in json_parser['page']['content']['section']['bands']:
                try:
                    block = element['blocks'][0]
                    if block['componentKey'] == 'fullEpisodesBlock':
                        list_videos_datas = block['items']['latestVideos']
                        for video_datas in list_videos_datas:
                            video_title = video_datas['title']
                            video_id = video_datas['id']
                            video_image = video_datas['image']
                            video_thumb = video_datas['videos']['thumbnail']
                            video_duration = video_datas['videos']['duration']

                            item = Listitem()
                            item.label = video_title
                            item.art['thumb'] = video_thumb
                            item.art['landscape'] = video_image
                            item.info['duration'] = video_duration
                            item.set_callback(get_video_url,
                                              item_id=item_id,
                                              video_id=video_id)
                            item_post_treatment(item,
                                                is_playable=True,
                                                is_downloadable=True)
                            yield item
                        break
                except KeyError:
                    continue
            break


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(URL_REPLAY_STREAM % video_id)
    json_parser = json.loads(resp.text)
    stream_url = ''
    for stream_datas in json_parser["channel"]["item"]["media-group"][
            "media-content"]:
        if stream_datas["@attributes"]["type"] == 'application/x-mpegURL':
            stream_url = stream_datas["@attributes"]["url"]

    if download_mode:
        return download.download_video(stream_url)
    return stream_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE_STREAM)
    json_parser = json.loads(resp.text)
    stream_url = ''
    for live_datas in json_parser["channel"]["item"]["media-group"][
            "media-content"]:
        if 'application/x-mpegURL' in live_datas["@attributes"]["type"]:
            if 'preview' not in live_datas["@attributes"]["url"]:
                stream_url = live_datas["@attributes"]["url"]
    return stream_url
