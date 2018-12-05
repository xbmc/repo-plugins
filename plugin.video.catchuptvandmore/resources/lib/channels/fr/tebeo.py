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
from resources.lib import download

from bs4 import BeautifulSoup as bs

import re
import urlquick

# TODO

URL_ROOT = 'http://www.tebeo.bzh'

URL_LIVE = URL_ROOT + '/player_live.php'

URL_REPLAY = URL_ROOT + '/le-replay'

URL_STREAM = URL_ROOT + '/player.php?idprogramme=%s'


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
    resp = urlquick.get(URL_REPLAY)
    root_soup = bs(resp.text, 'html.parser')
    list_categories_datas = root_soup.find(
        'div', class_='grid_12').find_all('li')

    for category_datas in list_categories_datas:
        category_name = category_datas.find('a').text
        category_url = category_datas.find('a').get('href')

        item = Listitem()
        item.label = category_name
        item.set_callback(
            list_videos,
            item_id=item_id,
            category_url=category_url)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url):

    resp = urlquick.get(category_url)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_='grid_8 replay')
    list_videos_datas += root_soup.find_all(
        'div', class_='grid_4 replay')

    for video_datas in list_videos_datas:
        video_title = video_datas.find('h3').text
        video_image = video_datas.find('img').get('src')
        video_url = video_datas.find('a').get('href')
        date_value = video_datas.find('p').text.split(' ')[0]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info.date(date_value, '%Y-%m-%d')

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
    video_id = re.compile(
        r'idprogramme\=(.*?)\&autoplay').findall(resp.text)[0]
    resp2 = urlquick.get(URL_STREAM % video_id)

    final_url = re.compile(
        r'source\: \"(.*?)\"').findall(resp2.text)[0]
    
    if download_mode:
        return download.download_video(final_url, video_label)
    return final_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(
        URL_LIVE, max_age=-1)
    return re.compile(
        r'source\: \"(.*?)\"').findall(
            resp.text)[0]
