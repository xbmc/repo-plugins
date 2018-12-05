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


URL_ROOT = 'https://www.lachainemeteo.com'

URL_VIDEOS = URL_ROOT + '/videos-meteo/videos-la-chaine-meteo'


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
    resp = urlquick.get(URL_VIDEOS)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find_all(
        'div', class_='viewVideosSeries')

    for program_datas in list_programs_datas:
        program_title = program_datas.find(
            'div', class_='title').text.strip()

        item = Listitem()
        item.label = program_title
        item.set_callback(
            list_videos,
            item_id=item_id,
            program_title_value=program_title)
        yield item


@Route.register
def list_videos(plugin, item_id, program_title_value):

    resp = urlquick.get(URL_VIDEOS)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find_all(
        'div', class_='viewVideosSeries')

    for program_datas in list_programs_datas:
        program_title = program_datas.find(
            'div', class_='title').text.strip()

        if program_title == program_title_value:
            list_videos_datas = program_datas.find_all('a')
            for video_datas in list_videos_datas:
                video_title = video_datas.find('div', class_='txt').text
                video_image = video_datas.find('img').get('data-src')
                video_url = video_datas.get('href')

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


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(video_url)
    data_account = re.compile(
        'players.brightcove.net/(.*?)/').findall(resp.text)[0]
    data_video_id = re.compile(
        'data-video-id=\'(.*?)\'').findall(resp.text)[0]
    data_player = re.compile(
        'data-player=\'(.*?)\'').findall(resp.text)[0]
    return resolver_proxy.get_brightcove_video_json(
        plugin,
        data_account,
        data_player,
        data_video_id,
        download_mode,
        video_label)
