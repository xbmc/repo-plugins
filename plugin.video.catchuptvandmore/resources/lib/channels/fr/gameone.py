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
from resources.lib.menu_utils import item_post_treatment

import json
import re
import urlquick

# TO DO
# Video Infos (date, duration)

URL_ROOT = 'http://www.gameone.net'
# ChannelName

URL_PROGRAMS = URL_ROOT + '/shows'

# PageId


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_PROGRAMS)
    root = resp.parse()

    for program_datas in root.iterfind(".//li[@class='item poster css-1u1rran-Wrapper e19yuxbf0']"):
        program_title = program_datas.find(".//div[@class='header']/span").text
        program_image = ''
        list_images = program_datas.findall(".//img")
        for image_datas in list_images:
            if 'http' in image_datas.get('srcset'):
                program_image = image_datas.get('srcset')
        program_url = URL_ROOT + program_datas.find('.//a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(
            list_seasons, item_id=item_id, program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_seasons(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    json_value = re.compile(r'window\.__DATA__ \= (.*?)\}\;').findall(
        resp.text)[0]
    json_parser = json.loads(json_value + '}')

    for main_contents_datas in json_parser['children']:
        if 'MainContainer' in main_contents_datas['type']:
            for season_child in main_contents_datas['children']:
                if season_child['type'] is not None:
                    if 'SeasonSelector' in season_child['type']:
                        for season_datas in season_child['props']['items']:
                            season_title = season_datas['label']
                            if season_datas['url'] is not None:
                                season_url = URL_ROOT + season_datas['url']
                            else:
                                season_url = program_url

                            item = Listitem()
                            item.label = season_title
                            item.set_callback(
                                list_videos,
                                item_id=item_id,
                                season_url=season_url)
                            item_post_treatment(item)
                            yield item


@Route.register
def list_videos(plugin, item_id, season_url, **kwargs):

    if 'api/context' in season_url:
        resp = urlquick.get(season_url)
        json_parser = json.loads(resp.text)

        for video_datas in json_parser['items']:
            video_title = video_datas['meta']['header'][
                'title']
            video_image = video_datas['media']['image']['url']
            video_plot = video_datas['meta']['description']
            # TODO add duration / date
            video_url = URL_ROOT + video_datas['url']

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(
                get_video_url,
                item_id=item_id,
                video_url=video_url)
            item_post_treatment(
                item, is_playable=True, is_downloadable=True)
            yield item

        if json_parser['loadMore'] is not None:
            new_season_url = URL_ROOT + json_parser['loadMore']['url']
            yield Listitem.next_page(item_id=item_id, season_url=new_season_url)

    else:
        resp = urlquick.get(season_url)
        json_value = re.compile(r'window\.__DATA__ \= (.*?)\}\;').findall(
            resp.text)[0]
        json_parser = json.loads(json_value + '}')

        for main_contents_datas in json_parser['children']:
            if 'MainContainer' in main_contents_datas['type']:
                for video_child in main_contents_datas['children']:
                    if video_child['type'] is not None:
                        if 'LineList' in video_child['type']:
                            video_props = video_child['props']
                            if 'video-guide' in video_props['type']:
                                for video_datas in video_props['items']:
                                    video_title = video_datas['meta']['header'][
                                        'title']
                                    video_image = video_datas['media']['image']['url']
                                    video_plot = video_datas['meta']['description']
                                    # TODO add duration / date
                                    video_url = URL_ROOT + video_datas['url']

                                    item = Listitem()
                                    item.label = video_title
                                    item.art['thumb'] = item.art['landscape'] = video_image
                                    item.info['plot'] = video_plot

                                    item.set_callback(
                                        get_video_url,
                                        item_id=item_id,
                                        video_url=video_url)
                                    item_post_treatment(
                                        item, is_playable=True, is_downloadable=True)
                                    yield item

                                if 'loadMore' in video_props:
                                    new_season_url = URL_ROOT + video_props['loadMore']['url']
                                    yield Listitem.next_page(
                                        item_id=item_id,
                                        season_url=new_season_url)


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)
    json_value = re.compile(r'window\.__DATA__ \= (.*?)\}\;').findall(
        resp.text)[0]
    json_parser = json.loads(json_value + '}')

    video_uri = ''
    for main_contents_datas in json_parser['children']:
        if 'MainContainer' in main_contents_datas['type']:
            for stream_child in main_contents_datas['children']:
                if stream_child['type'] is not None:
                    if 'VideoPlayer' in stream_child['type']:
                        video_uri = stream_child['props']['media']['video'][
                            'config']['uri']

    return resolver_proxy.get_mtvnservices_stream(plugin, video_uri,
                                                  download_mode)
