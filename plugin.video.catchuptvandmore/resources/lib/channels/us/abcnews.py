# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment


# TODO
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
        if not script_data.text or "__abcnews__" not in script_data.text:
            continue

        script = script_data.text
        page_data = script[script.find('{'):script.rfind('}') + 1]
        json_parser = json.loads(page_data)
        for element in json_parser['page']['content']['section']['bands']:
            try:
                block = element['blocks'][0]
                if block['componentKey'] != 'fullEpisodesBlock':
                    continue

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
