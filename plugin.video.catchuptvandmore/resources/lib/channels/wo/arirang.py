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

from resources.lib.codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import re
from resources.lib import urlquick

# TO DO
# Find a way to get M3U8 (live)
# Get Info Replay And Live (date, duration, etc ...)

URL_ROOT = 'http://www.arirang.com/mobile/'

URL_EMISSION = URL_ROOT + 'tv_main.asp'
# URL STREAM below present in this URL in mobile phone

URL_STREAM = 'http://amdlive.ctnd.com.edgesuite.net/' \
             'arirang_1ch/smil:arirang_1ch.smil/playlist.m3u8'


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
    resp = urlquick.get(URL_EMISSION)
    root = resp.parse("ul",
                      attrs={"class": "amenu_tab amenu_tab_3 amenu_tab_sub"})

    for category_datas in root.iterfind(".//li"):
        category_title = category_datas.find('.//a').text
        category_url = URL_ROOT + category_datas.find(".//a").get("href")

        item = Listitem()
        item.label = category_title
        item.set_callback(list_programs,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_url, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(category_url)
    root = resp.parse()

    for program_datas in root.iterfind(".//dl[@class='alist amain_tv']"):
        program_title = program_datas.find('.//img').get('alt')
        program_image = program_datas.find('.//img').get('src')
        program_url = URL_ROOT + program_datas.find(".//a").get("href")

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()

    for video_datas in root.iterfind(".//dl[@class='alist']"):
        video_title = video_datas.find('.//img').get('alt')
        video_image = video_datas.find('.//img').get('src')
        video_url = video_datas.find('.//a').get('href')
        video_url = re.compile(r'\(\'(.*?)\'\)').findall(video_url)[0]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)
    list_streams_datas = re.compile(r'mediaurl: \'(.*?)\'').findall(resp.text)
    for stream_datas in list_streams_datas:
        if 'm3u8' in stream_datas:
            stream_url = stream_datas

    if download_mode:
        return download.download_video(stream_url)
    return stream_url


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):
    return URL_STREAM
