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
from resources.lib.menu_utils import item_post_treatment

import re
import urlquick

# TO DO
# Add info LIVE TV, Replay

URL_ROOT = 'http://zonevideo.telequebec.tv'

URL_LIVE = 'https://player.telequebec.tv/Tq_VideoPlayer.js'

URL_EMISSIONS = URL_ROOT + '/a-z/'

URL_STREAM = 'https://mnmedias.api.telequebec.tv/m3u8/%s.m3u8'
# VideoId


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
    resp = urlquick.get(URL_EMISSIONS)
    root = resp.parse("div", attrs={"class": "list"})

    for program_datas in root.iterfind(".//li"):
        program_title = program_datas.find('.//a').text
        program_url = URL_ROOT + program_datas.find('.//a').get('href')

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

    for video_datas in root.iterfind(".//div[@class='item']"):
        video_title = video_datas.find('.//p').text.split(
            ' / ')[0] + ' - ' + video_datas.find('.//h4').find('.//a').text
        video_plot = video_datas.find('.//p').text
        video_image = video_datas.find('.//img').get('src')
        video_id = video_datas.get('data-mediaid')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    final_video_url = URL_STREAM % video_id

    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    return 'https:' + re.compile(r'm3U8Url:"(.*?)"').findall(resp.text)[0]
