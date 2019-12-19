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

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import json
import re
import urlquick
import xml.etree.ElementTree as ET

# TO DO
# Add replay

URL_ROOT = 'https://www.raiplay.it'

# Live
URL_LIVE = URL_ROOT + '/dirette/%s'
# Channel

URL_REPLAYS = URL_ROOT + '/dl/RaiTV/RaiPlayMobile/Prod/Config/programmiAZ-elenco.json'


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_letters(plugin, item_id)


@Route.register
def list_letters(plugin, item_id, **kwargs):
    """
    Build letter
    - A
    - B
    - ....
    """
    resp = urlquick.get(URL_REPLAYS)
    json_parser = json.loads(resp.text)

    for letter_title in list(json_parser.keys()):
        item = Listitem()
        item.label = letter_title
        item.set_callback(list_programs,
                          item_id=item_id,
                          letter_title=letter_title)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, letter_title, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_REPLAYS)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser[letter_title]:
        if "PathID" in program_datas:
            program_title = program_datas["name"]
            program_image = ''
            if "images" in program_datas:
                if 'landscape' in program_datas["images"]:
                    program_image = program_datas["images"][
                        "landscape"].replace('/resizegd/[RESOLUTION]', '')
            program_url = program_datas["PathID"]

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = program_image
            item.set_callback(list_videos,
                              item_id=item_id,
                              program_url=program_url)
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    json_parser = json.loads(resp.text)

    # Get Program Name and Program Plot
    program_name = json_parser["Name"]
    program_plot = json_parser["infoProg"]["description"]

    has_contents = False

    try:
        url_videos = URL_ROOT + json_parser["Blocks"][0]["Sets"][0]["url"]
        has_contents = True
    except Exception:
        pass

    if has_contents:
        resp2 = urlquick.get(url_videos)
        json_parser2 = json.loads(resp2.text)

        for video_datas in json_parser2["items"]:
            video_title = program_name + ' ' + video_datas[
                'name'] + ' ' + video_datas['subtitle']
            video_image = video_datas["images"]["landscape"].replace(
                '/resizegd/[RESOLUTION]', '')
            duration_value = video_datas['duration'].split(':')
            video_duration = 0
            if len(duration_value) > 2:
                video_duration = int(duration_value[0]) * 3600 + int(
                    duration_value[1]) * 60 + int(duration_value[2])
            elif len(duration_value) > 1:
                video_duration = int(duration_value[0]) * 60 + int(
                    duration_value[1])
            video_url = URL_ROOT + video_datas['pathID']

            item = Listitem()
            item.label = video_title
            item.art["thumb"] = video_image
            item.info['duration'] = video_duration
            item.info['plot'] = program_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_label=LABELS[item_id] + ' - ' + item.label,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(video_url)
    json_parser = json.loads(resp.text)

    if download_mode:
        return download.download_video(json_parser["video"]["contentUrl"],
                                       video_label)
    return json_parser["video"]["contentUrl"]


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.get(URL_LIVE % item_id, max_age=-1)
    return re.compile(r'\"content_url\"\:\"(.*?)\"').findall(
        resp.text)[0]
