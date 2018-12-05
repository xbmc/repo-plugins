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

from bs4 import BeautifulSoup as bs

import json
import urlquick


# TO DO
# Get year from Replay


URL_REPLAY = 'http://www.numero23.fr/replay/'

URL_INFO_LIVE_JSON = 'http://www.numero23.fr/wp-content/cache/n23-direct.json'

CORRECT_MONTH = {
    'janvier': '01',
    'février': '02',
    'mars': '03',
    'avril': '04',
    'mai': '05',
    'juin': '06',
    'juillet': '07',
    'août': '08',
    'septembre': '09',
    'octobre': '10',
    'novembre': '11',
    'décembre': '12'
}


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
    categories_soup = root_soup.find(
        'div',
        class_='nav-programs'
    )
    for category in categories_soup.find_all('a'):
        category_name = category.find(
            'span').get_text().replace(
            '\n', ' ').replace('\r', ' ').rstrip('\r\n')
        category_url = category.get('href')

        item = Listitem()
        item.label = category_name
        item.set_callback(
            list_videos,
            item_id=item_id,
            category_url=category_url,
            page='1')
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, page):

    replay_paged_url = category_url + '&paged=' + page
    resp = urlquick.get(replay_paged_url)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_='program sticky video')

    for video_datas in list_videos_datas:
        info_video = video_datas.find_all('p')

        video_title = utils.ensure_unicode(
            video_datas.find('p', class_="red").text)
        video_img = video_datas.find(
            'img')['src']
        video_id = video_datas.find(
            'div', class_="player")['data-id-video']
        video_duration = 0
        video_duration_list = utils.strip_tags(str(info_video[3])).split(':')
        if len(video_duration_list) > 2:
            video_duration = int(video_duration_list[0]) * 3600 + \
                int(video_duration_list[1]) * 60 + \
                int(video_duration_list[2])
        else:
            video_duration = int(video_duration_list[0]) * 60 + \
                int(video_duration_list[1])

        # get month and day on the page
        try:
            date_list = utils.strip_tags(str(info_video[2])).split(' ')
        except:
            pass
        day = '00'
        month = '00'
        year = '2018'
        if len(date_list) > 3:
            day = date_list[2]
            try:
                month = CORRECT_MONTH[date_list[3]]
            except Exception:
                month = '00'
            # get year ?

        date_value = '-'.join((year, month, day))

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_img
        item.info['duration'] = video_duration
        item.info.date(date_value, '%Y-%m-%d')

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_id=video_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)
        yield item

    yield Listitem.next_page(
        item_id=item_id,
        category_url=category_url,
        page=str(int(page) + 1))


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):
    return resolver_proxy.get_stream_dailymotion(
        plugin, video_id, download_mode, video_label)


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(
        URL_INFO_LIVE_JSON,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    json_parser = json.loads(resp.text)
    video_id = json_parser["video"]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, False)
