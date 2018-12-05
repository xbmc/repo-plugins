# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

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


import json
import re
import urlquick


# TO DO
# Replay protected by SAMPLE-AES (keep code - desactivate channel for the moment)


URL_ROOT = 'https://uktvplay.uktv.co.uk'

URL_SHOWS = URL_ROOT + '/shows/'
# channel_name

URL_BRIGHTCOVE_DATAS = 'https://s3-eu-west-1.amazonaws.com/uktv-static/prod/play/app.f9f9840edb0a29f05ebf.js'


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_SHOWS)
    json_value = re.compile(
        r'window\.\_\_NUXT\_\_\=(.*?)\;\<\/script\>').findall(resp.text)[0]
    json_parser = json.loads(json_value)

    for serie_id in json_parser["state"]["content"]["series"]:
        for program_datas in json_parser["state"]["content"]["series"][serie_id]:
            if item_id == program_datas["channel"]:
                program_title = program_datas["brand_name"]
                item = Listitem()
                item.label = program_title
                item.set_callback(
                    list_videos,
                    item_id=item_id,
                    serie_id=serie_id)
                yield item
                break


@Route.register
def list_videos(plugin, item_id, serie_id):

    resp = urlquick.get(URL_SHOWS)
    json_value = re.compile(
        r'window\.\_\_NUXT\_\_\=(.*?)\;\<\/script\>').findall(resp.text)[0]
    json_parser = json.loads(json_value)

    # Get data_account / data_player
    resp2 = urlquick.get(URL_BRIGHTCOVE_DATAS)
    data_account = re.compile(
        r'VUE_APP_BRIGHTCOVE_ACCOUNT\:\"(.*?)\"').findall(resp2.text)[0]
    data_player = re.compile(
        r'VUE_APP_BRIGHTCOVE_PLAYER\:\"(.*?)\"').findall(resp2.text)[0]

    for video_datas in json_parser["state"]["content"]["series"][serie_id]:

        video_title = video_datas["brand_name"] + ' - ' + video_datas["name"] + ' S%sE%s' % (video_datas["series_number"], str(video_datas["episode_number"]))
        video_image = video_datas["image"]
        video_plot = video_datas["synopsis"]
        video_duration = video_datas["duration"] * 60
        video_id = video_datas["video_id"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            data_account=data_account,
            data_player=data_player,
            data_video_id=video_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            data_account=data_account,
            data_player=data_player,
            data_video_id=video_id)
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, data_account, data_player, data_video_id,
        download_mode=False, video_label=None):

    return resolver_proxy.get_brightcove_video_json(
        plugin,
        data_account,
        data_player,
        data_video_id,
        download_mode,
        video_label)
