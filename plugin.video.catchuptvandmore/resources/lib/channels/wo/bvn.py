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
import time
import urlquick


# TO DO
# Info DATE

URL_ROOT = 'https://www.bvn.tv'

# LIVE :
URL_LIVE_DATAS = URL_ROOT + '/wp-content/themes/bvn/assets/js/app.js'
# Get Id
JSON_LIVE = 'https://json.dacast.com/b/%s/%s/%s'
# Id in 3 part
JSON_LIVE_TOKEN = 'https://services.dacast.com/token/i/b/%s/%s/%s'
# Id in 3 part

# REPLAY :
URL_TOKEN = 'https://ida.omroep.nl/app.php/auth'
URL_DAYS = URL_ROOT + '/uitzendinggemist/'
URL_INFO_REPLAY = 'https://e.omroep.nl/metadata/%s'
# Id Video, time
URL_VIDEO_REPLAY = 'https://ida.omroep.nl/app.php/%s?adaptive=yes&token=%s'
# Id Video, Token


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_days(plugin, item_id)


@Route.register
def list_days(plugin, item_id):
    """
    Build categories listing
    - day 1
    - day 2
    - ...
    """
    resp = urlquick.get(URL_DAYS)
    root_soup = bs(resp.text, 'html.parser')
    list_days_datas = root_soup.find_all(
        "h3", class_=re.compile("m-section__title"))
    day_id = 0

    for day_datas in list_days_datas:
        day_title = day_datas.text
        day_id = day_id + 1

        item = Listitem()
        item.label = day_title
        item.set_callback(
            list_videos,
            item_id=item_id,
            day_id=day_id)
        yield item


@Route.register
def list_videos(plugin, item_id, day_id):

    resp = urlquick.get(URL_DAYS)
    root_soup = bs(resp.text, 'html.parser')
    slick_missed_day_id = 'slick-missed-day-%s' % (day_id)
    list_videos_datas = root_soup.find_all(
        id=slick_missed_day_id)[0].find_all('li')

    for video_datas in list_videos_datas:
        list_video_id = video_datas.find('a').get('href').rsplit('/')
        video_id = list_video_id[len(list_video_id)-1]
        video_title = ''
        video_time = video_datas.find('time', class_="m-section__scroll__item__bottom__time").text.replace('.', ':')
        if video_datas.find('span', class_="m-section__scroll__item__bottom__title--sub").string is not None:
            video_title = video_time + ' - ' + video_datas.find('span', class_="m-section__scroll__item__bottom__title").text + \
                ': ' + video_datas.find('span', class_="m-section__scroll__item__bottom__title--sub").text
        else:
            video_title = video_time + ' - ' + video_datas.find('span', class_="m-section__scroll__item__bottom__title").text
        video_image = URL_ROOT + video_datas.find('img').get('data-src')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

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


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):

    # get token
    resp = urlquick.get(URL_TOKEN)
    token_json_parser = json.loads(resp.text)
    token = token_json_parser["token"]

    # get stream url
    resp2 = urlquick.get(URL_VIDEO_REPLAY % (video_id, token))
    json_parser = json.loads(resp2.text)
    stream_url = ''
    if 'items' in json_parser:
        for stream_url_datas in json_parser["items"][0]:
            stream_url_json = stream_url_datas["url"]
            break
        resp3 = urlquick.get(stream_url_json + \
            'jsonpCallback%s5910' % (str(time.time()).replace('.', '')))
        json_value = re.compile(r'\((.*?)\)').findall(resp3.text)[0]
        json_parser2 = json.loads(json_value)

        if 'url' in json_parser2:
            stream_url = json_parser2["url"]

    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(URL_LIVE_DATAS)
    list_id_values = re.compile(
        r'dacast\(\'(.*?)\'\,').findall(resp.text)[0].split('_')

    resp2 = urlquick.get(JSON_LIVE % (list_id_values[0], list_id_values[1], list_id_values[2]))
    live_json_parser = json.loads(resp2.text)

    # json with token
    resp3 = urlquick.get(JSON_LIVE_TOKEN % (list_id_values[0], list_id_values[1], list_id_values[2]))
    token_json_parser = json.loads(resp3.text)

    return live_json_parser["hls"] + \
        token_json_parser["token"]
