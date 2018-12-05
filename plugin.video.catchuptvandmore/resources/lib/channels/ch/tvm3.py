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
from resources.lib import resolver_proxy

from bs4 import BeautifulSoup as bs

import re
import urlquick

# TO DO
# Get Image


URL_ROOT = 'http://www.tvm3.tv'

# Replay
URL_REPLAY = URL_ROOT + '/replay'


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_REPLAY)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find_all(
        'div', class_='uk-panel uk-panel-hover')
    for program_datas in list_programs_datas:
        program_title = program_datas.find(
            'img').get('alt')
        program_image = URL_ROOT + program_datas.find(
            'img').get('src')
        program_url = URL_ROOT + program_datas.find(
            'a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(
            list_videos,
            item_id=item_id,
            program_url=program_url)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url):

    resp = urlquick.get(program_url)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_='uk-panel uk-panel-hover uk-invisible')
    list_videos_datas += root_soup.find_all(
        'div', class_='uk-panel uk-panel-space uk-invisible')

    is_youtube = False

    for video_datas in list_videos_datas:
        video_title = video_datas.find(
            'h3').find('a').text
        if video_datas.find('div', class_='youtube-player'):
            video_id = video_datas.find(
                'div', class_='youtube-player').get('data-id')
            is_youtube = True
        elif video_datas.find('iframe'):
            video_id = re.compile(
                r'player.vimeo.com/video/(.*?)[\?\"]').findall(
                video_datas.find(
                    'iframe').get('src'))[0]

        item = Listitem()
        item.label = video_title

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_id=video_id,
            is_youtube=is_youtube,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id,
            is_youtube=is_youtube)
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, is_youtube,
        download_mode=False, video_label=None):

    if is_youtube:
        return resolver_proxy.get_stream_youtube(
            plugin, video_id, download_mode, video_label)
    else:
        return resolver_proxy.get_stream_vimeo(
            plugin, video_id, download_mode, video_label)
