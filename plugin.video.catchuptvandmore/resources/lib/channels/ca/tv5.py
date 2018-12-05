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
from resources.lib import download

from bs4 import BeautifulSoup as bs

import json
import re
import urlquick
import xbmc

# TO DO
# Info Videos (date, plot, etc ...)


URL_ROOT = 'https://%s.ca'
# Channel Name

URL_VIDEOS = 'https://%s.ca/videos?params[%s]=%s'\
             '&options[sort]=publish_start&options[page]=%s'
# Channel Name, theme|serie, Value, page

URL_STREAM = 'https://production-ps.lvp.llnw.net/r/PlaylistService' \
             '/media/%s/getMobilePlaylistByMediaId'
# StreamId


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(LABELS['All programs'])
    item.set_callback(
        list_programs,
        item_id=item_id)
    yield item

    resp = urlquick.get(URL_ROOT % item_id + '/videos')
    root_soup = bs(resp.text, 'html.parser')
    list_categories_datas = root_soup.find(
        'select',
        class_="js-form-data js-select_filter_video js-select_filter_video-theme"
    ).find_all('option')

    for category_datas in list_categories_datas:
        category_title = category_datas.text
        category_id = category_datas.get('value')

        if 'theme_' in category_id:
            item = Listitem()
            item.label = category_title
            item.set_callback(
                list_videos,
                item_id=item_id,
                next_id=category_id,
                page='1')
            yield item


@Route.register
def list_programs(plugin, item_id):

    resp = urlquick.get(URL_ROOT % item_id + '/videos')
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find(
        'select',
        class_="js-form-data js-select_filter_video js-select_filter_video-serie"
    ).find_all('option')

    for program_datas in list_programs_datas:
        program_title = program_datas.text
        program_id = program_datas.get('value')

        if program_id is not None:
            item = Listitem()
            item.label = program_title
            item.set_callback(
                list_videos,
                item_id=item_id,
                next_id=program_id,
                page='1')
            yield item


@Route.register
def list_videos(plugin, item_id, next_id, page):

    if 'theme' in next_id:
        param_id = 'theme'
    else:
        param_id = 'serie'

    resp = urlquick.get(
        URL_VIDEOS % (item_id, param_id, next_id, page))
    part_page = re.split(
        '<div class="listing-carousel-container">', resp.text)
    part_page = re.split(
        '<div class="pagination-block js-pagination-block">', part_page[1])
    root_soup = bs(part_page[0], 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_='media-thumb ')

    for video_datas in list_videos_datas:
        if video_datas.find('a'):
            video_title = video_datas.find('img').get('alt')
            video_image = video_datas.find('img').get('data-src')
            video_url = URL_ROOT % item_id +  video_datas.find('a').get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image

            item.context.script(
                get_video_url,
                plugin.localize(LABELS['Download']),
                item_id=item_id,
                video_url=video_url,
                video_label=LABELS[item_id] + ' - ' + item.label,
                download_mode=True)

            item.set_callback(
                get_video_url,
                item_id=item_id,
                video_url=video_url)
            yield item

    yield Listitem.next_page(
        item_id=item_id,
        next_id=next_id,
        page=str(int(page) + 1))


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(video_url)
    media_id = re.compile(
        '\'media_id\' : "(.*?)"').findall(resp.text)[0]
    resp2 = urlquick.get(URL_STREAM % media_id)
    json_parser = json.loads(resp2.text)

    stream_url = ''
    if 'mediaList' in json_parser:
        xbmc_version = int(xbmc.getInfoLabel("System.BuildVersion").split('-')[0].split('.')[0])
        if xbmc_version < 17:
            for stream_datas in json_parser["mediaList"][0]["mobileUrls"]:
                if 'MobileH264' in stream_datas["targetMediaPlatform"]:
                    stream_url = stream_datas["mobileUrl"]
        else:
            for stream_datas in json_parser["mediaList"][0]["mobileUrls"]:
                if 'HttpLiveStreaming' in stream_datas["targetMediaPlatform"]:
                    stream_url = stream_datas["mobileUrl"]

    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url
