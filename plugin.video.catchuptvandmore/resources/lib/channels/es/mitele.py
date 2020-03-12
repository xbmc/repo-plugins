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

from builtins import range
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib.menu_utils import item_post_treatment

import json
import re
import requests
import urlquick
from kodi_six import xbmcgui

# TO DO
# Add Replay

DESIRED_QUALITY = Script.setting['quality']

URL_LIVE_DATAS = 'http://indalo.mediaset.es/mmc-player/api/mmc/v1/%s/live/flash.json'
# channel name

URL_LIVE_STREAM = 'https://pubads.g.doubleclick.net/ssai/event/%s/streams'
# Live Id

URL_LIVE_HASH = 'https://gatekeeper.mediaset.es/'


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    session_requests = requests.session()
    resp = session_requests.get(URL_LIVE_DATAS % item_id)
    json_parser = json.loads(resp.text)

    root = ''

    if json_parser["locations"][0]["ask"] is not None:
        lives_stream_json = session_requests.post(
            URL_LIVE_STREAM % json_parser["locations"][0]["ask"])
        lives_stream_jsonparser = json.loads(lives_stream_json.text)

        url_stream_without_hash = lives_stream_jsonparser["stream_manifest"]

        lives_hash_json = session_requests.post(
            URL_LIVE_HASH,
            data='{"gcp": "%s"}' % (json_parser["locations"][0]["gcp"]),
            headers={
                'Connection': 'keep-alive',
                'Content-type': 'application/json'
            })
        lives_hash_jsonparser = json.loads(lives_hash_json.text)

        if 'message' in lives_hash_jsonparser:
            if 'geoblocked' in lives_hash_jsonparser['message']:
                plugin.notify('ERROR', plugin.localize(30713))
            return False

        m3u8_video_auto = session_requests.get(url_stream_without_hash + '&' +
                                               lives_hash_jsonparser["suffix"])
    else:
        lives_stream_json = session_requests.post(
            URL_LIVE_HASH,
            data='{"gcp": "%s"}' % (json_parser["locations"][0]["gcp"]),
            headers={
                'Connection': 'keep-alive',
                'Content-type': 'application/json'
            })
        lives_stream_jsonparser = json.loads(lives_stream_json.text)

        if 'message' in lives_stream_jsonparser:
            if 'geoblocked' in lives_stream_jsonparser['message']:
                plugin.notify('ERROR', plugin.localize(30713))
            return False

        m3u8_video_auto = session_requests.get(
            lives_stream_jsonparser["stream"])
        root = lives_stream_jsonparser["stream"].split('master.m3u8')[0]

    lines = m3u8_video_auto.text.splitlines()
    if DESIRED_QUALITY == "DIALOG":
        all_datas_videos_quality = []
        all_datas_videos_path = []
        for k in range(0, len(lines) - 1):
            if 'RESOLUTION=' in lines[k]:
                all_datas_videos_quality.append(
                    lines[k].split('RESOLUTION=')[1])
                if 'http' in lines[k + 1]:
                    all_datas_videos_path.append(lines[k + 1])
                else:
                    all_datas_videos_path.append(root + '/' + lines[k + 1])
        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(LABELS['choose_video_quality']),
            all_datas_videos_quality)
        if seleted_item > -1:
            return all_datas_videos_path[seleted_item]
        else:
            return False
    elif DESIRED_QUALITY == 'BEST':
        # Last video in the Best
        for k in range(0, len(lines) - 1):
            if 'RESOLUTION=' in lines[k]:
                if 'http' in lines[k + 1]:
                    url = lines[k + 1]
                else:
                    url = root + '/' + lines[k + 1]
        return url
    else:
        for k in range(0, len(lines) - 1):
            if 'RESOLUTION=' in lines[k]:
                if 'http' in lines[k + 1]:
                    url = lines[k + 1]
                else:
                    url = root + '/' + lines[k + 1]
            break
        return url
