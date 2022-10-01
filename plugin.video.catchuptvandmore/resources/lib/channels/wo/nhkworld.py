# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import time
import re

from codequick import Listitem, Route, Script
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

# noinspection PyUnresolvedReferences
from codequick import Resolver

from resources.lib import resolver_proxy, web_utils


URL_ROOT = 'http://www3.nhk.or.jp/'

URL_LIVE_NHK = 'https://www3.nhk.or.jp/nhkworld/app/tv/hlslive_web.json'
# Channel_Name...

URL_COMMONJS_NHK = 'http://www3.nhk.or.jp/%s/common/js/common.js'
# Channel_Name...

URL_CATEGORIES_NHK = 'https://api.nhk.or.jp/%s/vodcatlist/v7a/all/en/ondemand/list.json?apikey=%s'
# Channel_Name, apikey

URL_ALL_VOD_NHK = 'https://api.nhk.or.jp/%s/vodesdlist/v7a/category/%s/en/all/all.json?apikey=%s'
# Channel_Name, apikey

URL_VIDEO_VOD = 'https://movie-s.nhk.or.jp/v/refid/nhkworld/prefid/%s'
# Videoid

URL_VIDEO_STREAM = 'https://movie-s.nhk.or.jp/ws/ws_program/api/%s/apiv/5/mode/json?v=%s'
# data_de_api_key, data_de_program_uuid


def get_api_key(item_id):
    # Get apikey
    resp = urlquick.get(URL_COMMONJS_NHK % item_id)
    list_apikey = re.compile('nw_api_key\|\|"(.+?)"').findall(resp.text)
    return list_apikey[0]


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_CATEGORIES_NHK % (item_id, get_api_key(item_id)))
    json_parser = json.loads(resp.text)

    for category_datas in json_parser["vod_categories"]:
        category_title = category_datas["name"]
        category_id = category_datas["category_id"]

        item = Listitem()
        item.label = category_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_id=category_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_id, **kwargs):

    resp = urlquick.get(URL_ALL_VOD_NHK % (item_id, category_id, get_api_key(item_id)))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["data"]["episodes"]:

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
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['duration'] = video_duration
        item.info['plot'] = video_plot
        item.info.date(date_value, '%Y-%m-%d')

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

    resp = urlquick.get(URL_VIDEO_VOD % video_id)
    data_de_api_key = re.compile(
        r'data-de-api-key\=\"(.*?)\"').findall(resp.text)[0]
    data_de_program_uuid = re.compile(
        r'data-de-program-uuid\=\"(.*?)\"').findall(resp.text)[0]

    resp2 = urlquick.get(URL_VIDEO_STREAM % (data_de_api_key, data_de_program_uuid))
    json_parser2 = json.loads(resp2.text)

    video_url = json_parser2["response"]["WsProgramResponse"]["program"]["asset"]["ipadM3u8Url"]

    if download_mode:
        return download.download_video(video_url)
    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    desired_country = kwargs.get('language', Script.setting[item_id + '.language'])

    resp = urlquick.get(URL_LIVE_NHK)
    json_parser = json.loads(resp.text)
    video_url = ''
    if desired_country == 'Outside Japan':
        video_url = json_parser["main"]["wstrm"]
    else:
        video_url = json_parser["main"]["jstrm"]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
