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

import base64
import json
import time
import re
import urlquick
import xml.etree.ElementTree as ET


URL_ROOT = 'http://www3.nhk.or.jp/'

URL_LIVE_NHK = 'http://www3.nhk.or.jp/%s/app/tv/hlslive_tv.xml'
# Channel_Name...

URL_COMMONJS_NHK = 'http://www3.nhk.or.jp/%s/common/js/common.js'
# Channel_Name...


URL_CATEGORIES_NHK = 'https://api.nhk.or.jp/%s/vodcatlist/v2/notzero/list.json?apikey=%s'
# Channel_Name, apikey

URL_ALL_VOD_NHK = 'https://api.nhk.or.jp/%s/vodesdlist/v1/all/all/all.json?apikey=%s'
# Channel_Name, apikey

URL_VIDEO_VOD = 'https://player.ooyala.com/sas/player_api/v2/authorization/' \
                'embed_code/%s/%s?device=html5&domain=www3.nhk.or.jp'
# pcode, Videoid

URL_GET_JS_PCODE = 'https://www3.nhk.or.jp/%s/common/player/tv/vod/'
# Channel_Name...


def get_pcode(item_id):
    # Get js file
    resp = urlquick.get(URL_GET_JS_PCODE % item_id)
    list_js_part_url = re.compile('<script src="\/(.+?)"').findall(resp.text)

    # Get last JS script
    get_pcode_url = URL_ROOT + list_js_part_url[len(list_js_part_url) - 1]

    # Get apikey
    resp2 = urlquick.get(get_pcode_url)
    list_pcode = re.compile('pcode: "(.+?)"').findall(resp2.text)
    return list_pcode[0]


def get_api_key(item_id):
    # Get apikey
    resp = urlquick.get(URL_COMMONJS_NHK % item_id)
    list_apikey = re.compile('nw_api_key\|\|"(.+?)"').findall(resp.text)
    return list_apikey[0]


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(LABELS['All videos'])
    item.set_callback(
        list_videos,
        item_id=item_id,
        category_id=0)
    yield item

    resp = urlquick.get(URL_CATEGORIES_NHK % (item_id, get_api_key(item_id)))
    json_parser = json.loads(resp.text)

    for category_datas in json_parser["vod_categories"]:
        category_title = category_datas["name"]
        category_id = category_datas["category_id"]

        item = Listitem()
        item.label = category_title
        item.set_callback(
            list_videos,
            item_id=item_id,
            category_id=category_id)
        yield item


@Route.register
def list_videos(plugin, item_id, category_id):

    resp = urlquick.get(URL_ALL_VOD_NHK % (item_id, get_api_key(item_id)))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["data"]["episodes"]:

        video_to_add = False
        if str(category_id) == '0':
            video_to_add = True
        else:
            for category_id_value in video_datas["category"]:
                if str(category_id_value) == str(category_id):
                    video_to_add = True
        if video_to_add:
            video_title = video_datas["title_clean"] + ' - ' + \
                video_datas["sub_title_clean"]
            video_image = URL_ROOT + video_datas["image"]
            video_id = video_datas["vod_id"]
            video_plot = video_datas["description_clean"]
            video_duration = video_datas["movie_duration"]
            date_value = time.strftime(
                '%Y-%m-%d',
                time.localtime(int(str(video_datas["onair"])[:-3])))

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image
            item.info['duration'] = video_duration
            item.info['plot'] = video_plot
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


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):

    resp = urlquick.get(URL_VIDEO_VOD % (get_pcode(item_id), video_id))
    json_parser = json.loads(resp.text)

    for stream_datas in json_parser["authorization_data"][video_id]["streams"]:
        stream_url_base64 = stream_datas["url"]["data"]

    final_video_url = base64.standard_b64decode(stream_url_base64)
    if download_mode:
        return download.download_video(final_video_url, video_label)
    return final_video_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    desired_country = Script.setting[item_id + '.country']
    resp = urlquick.get(URL_LIVE_NHK % item_id)
    xmlElements = ET.XML(resp.text)
    stream_url = ''
    if desired_country == 'Outside Japan':
        stream_url = xmlElements.find("tv_url").findtext("wstrm")
    else:
        stream_url = xmlElements.find("tv_url").findtext("jstrm")
    return stream_url
