# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Listitem, Route, Resolver, Script
import urlquick

from resources.lib import download, resolver_proxy, web_utils
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
    root = resp.parse()
    for script_data in root.iterfind(".//script[@type='text/javascript']"):
        if not script_data.text or "__abcnews__" not in script_data.text:
            continue

        script = script_data.text
        page_data = script[script.find('{'):script.rfind('}') + 1]
        json_parser = json.loads(page_data)
        for element in json_parser['page']['content']['shell']['navConfigData']['nav_links']['items']:
            program_title = element['title']
            program_url = element['href']

            item = Listitem()
            item.label = program_title

            if program_title == "Live":
                item.set_callback(get_live_url,
                                  item_id=item_id)
            elif program_title == "Sections" or program_title == "Shows":
                item.set_callback(list_sections,
                                  item_id="Sections" if 'Sections' in program_title else "Shows",
                                  program_url=URL_ROOT)
            elif program_title == "Search":
                item = Listitem.search(search)
                item_post_treatment(item)
            else:
                item.set_callback(list_videos,
                                  item_id=item_id,
                                  program_url=URL_ROOT + program_url)
            item_post_treatment(item)
            yield item


@Route.register
def search(plugin, search_query, **kwargs):
    r = urlquick.get(f"{URL_ROOT}/meta/api/search?q={search_query}&type=Video")
    j = json.loads(r.text)
    for collection in j['item']:
        item = Listitem()
        item.label = collection['title']
        item.art['thumb'] = collection['image']
        item.art['landscape'] = item.art['thumb']
        item.set_callback(get_video_url,
                          item_id="",
                          video_id=collection['link'])
        item_post_treatment(item)
        yield item


@Route.register
def list_sections(plugin, item_id, program_url, **kwargs):
    if item_id == "Shows":
        # Paid content
        Script.notify("INFO", "Not implemented", Script.NOTIFY_INFO)
        return None

    resp = urlquick.get(program_url)
    root = resp.parse()
    for script_data in root.iterfind(".//script[@type='text/javascript']"):
        if not script_data.text or "__abcnews__" not in script_data.text:
            continue

        script = script_data.text
        page_data = script[script.find('{'):script.rfind('}') + 1]
        json_parser = json.loads(page_data)
        # Paid content
        # if item_id == "Shows":
        #    jsonData = json_parser['page']['content']['shell']['navConfigData']['show_links']
        # else:
        jsonData = json_parser['page']['content']['shell']['navConfigData']['section_links']

        for (key, value) in jsonData.items():
            if type(value) is dict:
                value = value['href']
            program_title = key
            program_url = URL_ROOT + value

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
                for block in element['blocks']:
                    if block["componentKey"] != 'ad':
                        list_videos_datas = block['items']
                        if 'latestVideos' in list_videos_datas:
                            list_videos_datas = list_videos_datas['latestVideos']

                        for video_datas in list_videos_datas:
                            try:
                                video_title = video_datas['title']
                            except TypeError:
                                video_title = video_datas['headline']
                            video_id = video_datas['location']
                            video_image = video_datas['image']
                            video_thumb = video_datas['image']
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

            except (KeyError, IndexError):
                continue


@Resolver.register
def get_video_url(plugin, item_id, video_id, download_mode=False, **kwargs):
    if URL_ROOT in video_id:
        if "id=" in video_id:
            video_id = video_id.split('id=')[1]
        else:
            video_id = video_id.split("-")[-1]

    resp = urlquick.get(URL_REPLAY_STREAM % video_id)
    json_parser = json.loads(resp.text)
    video_url = ''
    for stream_datas in json_parser["channel"]["item"]["media-group"][
            "media-content"]:
        if stream_datas["@attributes"]["type"] == 'application/x-mpegURL':
            video_url = stream_datas["@attributes"]["url"]

    if download_mode:
        return download.download_video(video_url)
    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE_STREAM)
    json_parser = json.loads(resp.text)
    video_url = ''
    for live_datas in json_parser["channel"]["item"]["media-group"][
            "media-content"]:
        if 'application/x-mpegURL' in live_datas["@attributes"]["type"]:
            if 'preview' not in live_datas["@attributes"]["url"]:
                video_url = live_datas["@attributes"]["url"]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
