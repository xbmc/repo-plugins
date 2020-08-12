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
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import json
import re
import urlquick
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

# TO DO
# Add info LIVE TV
# Get geoblocked video info

URL_ROOT = 'https://videos.tva.ca'

URL_LIVE = URL_ROOT + '/page/direct'

URL_EMISSIONS = URL_ROOT + '/page/touslescontenus'

URL_VIDEOS = URL_ROOT + '/page/rattrapage'

URL_SEARCH = URL_ROOT + '/search'


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
    item.label = plugin.localize(30701)
    item.set_callback(list_videos, item_id=item_id, next_url=URL_VIDEOS)
    item_post_treatment(item)
    yield item

    item = Listitem()
    item.label = plugin.localize(30717)
    item.set_callback(list_programs, item_id=item_id)
    item_post_treatment(item)
    yield item

    item = Listitem.search(list_videos_search, item_id=item_id)
    item_post_treatment(item)
    yield item


@Route.register
def list_videos_search(plugin, item_id, search_query, page=1, **kwargs):
    resp = urlquick.get(URL_SEARCH + '/' + quote(search_query) + '/' + str(page))
    json_parser = json.loads(
        re.compile(r'__INITIAL_STATE__ = (.*?)\}\;').findall(resp.text)[0] +
        '}')

    data_account = json_parser["configurations"]["accountId"]
    data_player = json_parser["configurations"]["playerId"]
    at_least_one = False
    for video_datas in json_parser['items']:

        if '_' in video_datas:
            at_least_one = True
            video_title = json_parser['items'][str(
                video_datas)]["content"]["attributes"]["title"]
            video_plot = ''
            if 'description' in json_parser['items'][str(
                    video_datas)]["content"]["attributes"]:
                video_plot = json_parser['items'][str(
                    video_datas)]["content"]["attributes"]["description"]
            video_image = ''
            if 'image-background' in json_parser['items'][str(
                    video_datas)]["content"]["attributes"]:
                video_image = json_parser['items'][str(video_datas)][
                    "content"]["attributes"]["image-background"]
            video_id = json_parser['items'][str(
                video_datas)]["content"]["attributes"]["assetId"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              data_account=data_account,
                              data_player=data_player,
                              data_video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item
    if at_least_one:
        yield Listitem.next_page(
            item_id=item_id, search_query=search_query, page=page + 1)


@Route.register
def list_programs(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_EMISSIONS)
    json_parser = json.loads(
        re.compile(r'__INITIAL_STATE__ = (.*?)\}\;').findall(resp.text)[0] +
        '}')

    for program_datas in json_parser['items']:
        program_title = json_parser['items'][str(program_datas)]["content"][
            "attributes"]["name"].replace(' - Navigation', '')
        attributes = json_parser['items'][str(program_datas)]["content"][
            "attributes"]
        program_image = ''
        if "image-landscape-medium" in attributes:
            program_image = attributes["image-landscape-medium"]
        elif "image-background-medium" in attributes:
            program_image = attributes["image-background-medium"]
        program_url = None
        if 'pageId' in json_parser['items'][str(program_datas)]["content"][
                "attributes"]:
            program_url = URL_ROOT + '/page/' + json_parser['items'][str(
                program_datas)]["content"]["attributes"]["pageId"]

        if program_url is not None:
            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            item.set_callback(
                list_videos, item_id=item_id, next_url=program_url)
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, next_url, **kwargs):

    resp = urlquick.get(next_url)
    json_parser = json.loads(
        re.compile(r'__INITIAL_STATE__ = (.*?)\}\;').findall(resp.text)[0] +
        '}')

    data_account = json_parser["configurations"]["accountId"]
    data_player = json_parser["configurations"]["playerId"]

    for video_datas in json_parser['items']:

        if '_' in video_datas:
            video_title = json_parser['items'][str(
                video_datas)]["content"]["attributes"]["title"]
            video_plot = ''
            if 'description' in json_parser['items'][str(
                    video_datas)]["content"]["attributes"]:
                video_plot = json_parser['items'][str(
                    video_datas)]["content"]["attributes"]["description"]
            video_image = ''
            if 'image-background' in json_parser['items'][str(
                    video_datas)]["content"]["attributes"]:
                video_image = json_parser['items'][str(video_datas)][
                    "content"]["attributes"]["image-background"]
            video_id = json_parser['items'][str(
                video_datas)]["content"]["attributes"]["assetId"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              data_account=data_account,
                              data_player=data_player,
                              data_video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  data_account,
                  data_player,
                  data_video_id,
                  download_mode=False,
                  **kwargs):

    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id,
                                                    download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    json_parser = json.loads(
        re.compile(r'__INITIAL_STATE__ = (.*?)\}\;').findall(resp.text)[0] +
        '}')

    asset_id_value = ''
    for id_stream_datas in list(json_parser["items"].keys()):
        if item_id.upper() in json_parser["items"][id_stream_datas]["content"]["attributes"]["title"]:
            asset_id_value = json_parser["items"][id_stream_datas]["content"]["attributes"]["assetId"]

    data_account = re.compile(r'accountId":"(.*?)"').findall(resp.text)[0]
    data_player = re.compile(r'playerId":"(.*?)"').findall(resp.text)[0]
    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, asset_id_value)
