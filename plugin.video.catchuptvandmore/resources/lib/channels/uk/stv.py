# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
# noinspection PyUnresolvedReferences
from kodi_six import xbmcplugin
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

PATTERN_PLAYER = re.compile(r"PLAYER_ID:\"(.*?)\"")
PATTERN_ACCOUNT = re.compile(r"ACCOUNT_ID:\"(.*?)\"")
PATTERN_KEY = re.compile(r"POLICY_KEY:\"(.*?)\"")
# Live
URL_LIVE_JSON = "https://player.api.stv.tv/v1/streams/%s/"
# channel name

URL_CATEGORIES_JSON = "https://player.api.stv.tv/v1/categories"

URL_PROGRAMS_JSON = "https://player.api.stv.tv/v1/programmes"

URL_VIDEOS_JSON = "https://player.api.stv.tv/v1/episodes"
# guidProgramm

URL_BRIGHTCOVE_DATAS = "https://player.stv.tv/player-web/players/vod/bundle.js"


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """List categroies from https://player.stv.tv/categories/."""
    resp = urlquick.get(URL_CATEGORIES_JSON)
    json_parser = json.loads(resp.text)

    # Most popular category
    item = Listitem()
    item.label = Script.localize(30727)
    item.set_callback(list_videos, item_id=item_id, order_by="-views")
    item_post_treatment(item)
    yield item

    # Recently added category
    item = Listitem()
    item.label = Script.localize(30728)
    item.set_callback(list_videos, item_id=item_id, order_by="-availability.from")
    item_post_treatment(item)
    yield item

    # Other categories
    for category_datas in json_parser["results"]:
        item = Listitem()
        item.label = category_datas["name"]
        item.art["thumb"] = item.art["landscape"] = category_datas["images"][
            "_filepath"
        ]
        item.set_callback(
            list_programs, item_id=item_id, category_guid=category_datas["guid"]
        )
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_guid, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    params = {"category": category_guid}
    resp = urlquick.get(URL_PROGRAMS_JSON, params=params)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser["results"]:
        program_title = program_datas["name"]
        program_image = program_datas["images"][0]["_filepath"]
        program_plot = program_datas["longDescription"]
        program_guid = program_datas["guid"]

        item = Listitem()
        item.label = program_title
        item.art["thumb"] = item.art["landscape"] = program_image
        item.info["plot"] = program_plot
        item.set_callback(list_videos, item_id=item_id, program_guid=program_guid)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_guid=None, order_by=None, **kwargs):
    plugin.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED)
    payload = {"limit": "300"}
    if program_guid:
        payload["programme_guid"] = program_guid
    if order_by:
        payload["orderBy"] = order_by
    resp = urlquick.get(URL_VIDEOS_JSON, params=payload)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["results"]:
        video_title = video_datas["programme"]["name"] + " - " + video_datas["title"]
        video_image = video_datas["images"][0]["_filepath"]
        video_plot = video_datas["summary"]
        video_duration_datas = video_datas["video"]["_duration"].split(" ")
        if len(video_duration_datas) > 2:
            video_duration = 3600 * int(video_duration_datas[0]) + 60 * int(
                video_duration_datas[2]
            )
        else:
            video_duration = 60 * int(video_duration_datas[0])
        video_id = video_datas["video"]["id"]

        try:
            subtitle = video_datas["_subtitles"]["webvtt"]
        except Exception:
            subtitle = None

        item = Listitem()
        item.label = video_title
        item.art["thumb"] = item.art["landscape"] = video_image
        item.info["plot"] = video_plot
        item.info["duration"] = video_duration

        if video_datas["schedule"] is not None:
            date_value = video_datas["schedule"]["startTime"].split("T")[0]
            item.info.date(date_value, "%Y-%m-%d")

        item.set_callback(get_video_url, item_id=item_id, video_id=video_id, subtitle=subtitle)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin, item_id, video_id, subtitle, download_mode=False, **kwargs):
    resp = urlquick.get(URL_BRIGHTCOVE_DATAS)

    data_account = PATTERN_ACCOUNT.findall(resp.text)[0]
    data_player = PATTERN_PLAYER.findall(resp.text)[0]
    key = PATTERN_KEY.findall(resp.text)[0]
    data_video_id = video_id

    return resolver_proxy.get_brightcove_video_json(plugin, data_account, data_player, data_video_id, key, download_mode, subtitle)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    if item_id == "stv_plusone":
        item_id = "stv-plus-1"

    resp = urlquick.get(URL_LIVE_JSON % item_id)
    json_parser = json.loads(resp.text)
    url = json_parser["results"]["streamUrl"]
    return resolver_proxy.get_stream_with_quality(plugin, url, manifest_type="hls")
