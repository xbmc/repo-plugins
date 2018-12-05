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

import json
import re
import urlquick

# TO DO

URL_ROOT = 'http://www.la7.it'

URL_DAYS = URL_ROOT + '/rivedila7/0/%s'
# Channels (upper)

# Live
URL_LIVE = URL_ROOT + '/dirette-tv'


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_days(plugin, item_id)


@Route.register
def list_days(plugin, item_id):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_DAYS % item_id.upper())
    root_soup = bs(resp.text, 'html.parser')
    list_days_datas = root_soup.find_all(
        'div', class_='giorno')

    for day_datas in list_days_datas:
        day_title = day_datas.find(
            'div', class_='dateRowWeek').text + ' - ' + \
                day_datas.find('div', class_='dateDay').text + ' - ' + \
                    day_datas.find('div', class_='dateMonth').text
        day_url = URL_ROOT + day_datas.find('a').get('href')

        item = Listitem()
        item.label = day_title
        item.set_callback(
            list_videos,
            item_id=item_id,
            day_url=day_url)
        yield item


@Route.register
def list_videos(plugin, item_id, day_url):

    resp = urlquick.get(day_url)
    print 'response : ' + repr(resp.text)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_='palinsesto_row disponibile clearfix')

    for video_datas in list_videos_datas:
        video_title = video_datas.find('img').get('title')
        video_image = video_datas.find('img').get('src')
        video_plot = video_datas.find('div', class_='descrizione').find('p').text
        video_url = video_datas.find('a', class_="thumbVideo").get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot

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
    json_value = re.compile(
        r'src\: \{(.*?)\}\,').findall(resp.text)[0]
    json_parser = json.loads('{' + json_value + '}')
    if download_mode:
        return download.download_video(json_parser["m3u8"], video_label)
    return json_parser["m3u8"]


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    return re.compile(
        r'var vS \= \'(.*?)\'').findall(resp.text)[0]
