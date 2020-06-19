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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import base64
import json
import re
import urlquick

# TO DO
# Add info Video (duration, ...)

URL_ROOT = 'https://www.channelnewsasia.com'

URL_LIVE_ID = URL_ROOT + '/news/livetv'

URL_VIDEO_VOD = 'https://player.ooyala.com/sas/player_api/v2/authorization/' \
                'embed_code/%s/%s?device=html5&domain=www.channelnewsasia.com'
# pcode, liveId

URL_GET_JS_PCODE = URL_ROOT + '/blueprint/cna/js/main.js'

URL_VIDEOS_DATAS = URL_ROOT + '/news/videos'

URL_VIDEOS = URL_ROOT + '/dynamiclist?channelId=%s&contextId=%s&pageIndex=%s'
# showId, contextId, page

URL_SHOWS_DATAS = URL_ROOT + '/news/video-on-demand'

URL_SHOWS = URL_ROOT + '/dynamiclist?contextId=%s&pageIndex=%s'


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    item = Listitem()
    item.label = 'Videos'
    item.set_callback(list_programs_videos, item_id=item_id)
    yield item

    item = Listitem()
    item.label = 'Video On Demand'
    item.set_callback(list_programs_videos_on_demand,
                      item_id=item_id,
                      page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_programs_videos(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_VIDEOS_DATAS)
    context_id = re.compile('contextId\" value=\"(.*?)\"').findall(
        resp.text)[0]
    root = resp.parse(
        "select", attrs={"class": "filter__input i-arrow-select-small-red"})

    for program_datas in root.iterfind(".//option"):
        program_title = program_datas.get('label')
        program_id = program_datas.get('value')

        item = Listitem()
        item.label = program_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          context_id=context_id,
                          program_id=program_id,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_programs_videos_on_demand(plugin, item_id, page, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_SHOWS_DATAS)
    context_id = re.compile('contextId\" value=\"(.*?)\"').findall(
        resp.text)[0]
    resp2 = urlquick.get(URL_SHOWS % (context_id, page))
    json_parser = json.loads(resp2.text)

    for program_datas in json_parser["items"]:
        program_title = program_datas["title"]
        program_image = ''
        for image_datas in program_datas["image"]["items"][0]["srcset"]:
            program_image = URL_ROOT + image_datas["src"]
        program_url = URL_ROOT + program_datas["url"]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos_on_demand,
                          item_id=item_id,
                          program_url=program_url,
                          page='1')
        item_post_treatment(item)
        yield item

    yield Listitem.next_page(item_id=item_id, page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, context_id, program_id, page, **kwargs):

    resp = urlquick.get(URL_VIDEOS % (program_id, context_id, page))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['items']:
        video_title = video_datas["image"]["alt"].replace(' | Video', '')
        video_image = video_datas["image"]["src"]
        video_url = URL_ROOT + video_datas["url"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             context_id=context_id,
                             program_id=program_id,
                             page=str(int(page) + 1))


@Route.register
def list_videos_on_demand(plugin, item_id, program_url, page, **kwargs):

    resp = urlquick.get(program_url)
    context_id = re.compile('contextId\" value=\"(.*?)\"').findall(
        resp.text)[0]
    resp2 = urlquick.get(URL_SHOWS % (context_id, page))
    json_parser = json.loads(resp2.text)

    for video_datas in json_parser['items']:
        video_title = video_datas["title"]
        video_image = ''
        if 'src' in video_datas["image"]:
            video_image = video_datas["image"]["src"]
        else:
            for image_datas in video_datas["image"]["items"][0]["srcset"]:
                video_image = URL_ROOT + image_datas["src"]
        video_url = URL_ROOT + video_datas["url"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             program_url=program_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)
    list_stream_id = re.compile('video-asset-id="(.*?)"').findall(resp.text)

    if len(list_stream_id) > 0:
        pcode_datas = urlquick.get(URL_GET_JS_PCODE)
        pcode = re.compile(r'ooyalaPCode\:"(.*?)"').findall(
            pcode_datas.text)[0]
        reps_stream_datas = urlquick.get(URL_VIDEO_VOD %
                                         (pcode, list_stream_id[0]))
        json_parser = json.loads(reps_stream_datas.text)
        # Get Value url encodebase64
        if 'streams' in json_parser["authorization_data"][list_stream_id[0]]:
            for stream_datas in json_parser["authorization_data"][
                    list_stream_id[0]]["streams"]:
                if stream_datas["delivery_type"] == 'hls':
                    stream_url_base64 = stream_datas["url"]["data"]

            final_video_url = base64.standard_b64decode(stream_url_base64)
            if download_mode:
                return download.download_video(final_video_url)
            return final_video_url
        else:
            plugin.notify('ERROR', plugin.localize(30713))
    return False


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_LIVE_ID)
    list_stream_id = re.compile('video-asset-id="(.*?)"').findall(resp.text)

    if len(list_stream_id) > 0:
        pcode_datas = urlquick.get(URL_GET_JS_PCODE)
        pcode = re.compile(r'ooyalaPCode\:"(.*?)"').findall(
            pcode_datas.text)[0]
        reps_stream_datas = urlquick.get(URL_VIDEO_VOD %
                                         (pcode, list_stream_id[0]))
        json_parser = json.loads(reps_stream_datas.text)
        # Get Value url encodebase64
        if 'streams' in json_parser["authorization_data"][list_stream_id[0]]:
            for stream_datas in json_parser["authorization_data"][
                    list_stream_id[0]]["streams"]:
                if stream_datas["delivery_type"] == 'hls':
                    stream_url_base64 = stream_datas["url"]["data"]
            return base64.standard_b64decode(stream_url_base64)
        else:
            plugin.notify('ERROR', plugin.localize(30713))
    return False
