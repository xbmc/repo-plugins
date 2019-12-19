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
from resources.lib.listitem_utils import item_post_treatment, item2dict

import json
import re
import requests
import urlquick
from kodi_six import xbmcgui

# TO DO
# Find a way to get APIKey ?

# URL_JSON_LIVES = 'https://services.vrt.be/videoplayer/r/live.json'
# All lives in this JSON

URL_ROOT = 'https://www.vrt.be'

# Replay

URL_CATEGORIES_JSON = 'https://search.vrt.be/suggest?facets[categories]=%s'
# Category Name

URL_LOGIN = 'https://accounts.eu1.gigya.com/accounts.login'

URL_TOKEN = 'https://token.vrt.be'

URL_STREAM_JSON = 'https://mediazone.vrt.be/api/v1/vrtvideo/assets/%s'
# VideoID

# Live

URL_API = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1'

URL_TOKEN_LIVE = URL_API + '/tokens'

URL_LIVE = URL_API + '/videos/vualto_%s_geo?vrtPlayerToken=%s&client=vrtvideo'
# ChannelName

ROOT_VRT = {'/vrtnu/a-z/': 'A-Z', '/vrtnu/categorieen/': 'Categorieën'}


def get_api_key():
    # resp = urlquick.get(
    #     URL_ROOT + '/vrtnu/')
    # return re.compile(
    #     'apiKey=(.*?)\&').findall(api_key_html)[0]
    return '3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG'


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_root(plugin, item_id)


@Route.register
def list_root(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    for root_part_url, root_title in list(ROOT_VRT.items()):
        root_url = URL_ROOT + root_part_url

        if 'categorieen' in root_part_url:
            next_value = 'list_categories'
        else:
            next_value = 'list_programs'

        item = Listitem()
        item.label = root_title
        item.set_callback(eval(next_value), item_id=item_id, root_url=root_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, root_url, **kwargs):

    resp = urlquick.get(root_url)
    root = resp.parse()

    for program_datas in root.iterfind(".//nui-tile"):
        program_title = program_datas.find('.//a').text.strip()
        program_image = 'https:' + program_datas.find('.//img').get(
            'data-responsive-image')
        program_url = URL_ROOT + program_datas.find('.//a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(list_videos, item_id=item_id, next_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_categories(plugin, item_id, root_url, **kwargs):

    resp = urlquick.get(root_url, max_age=-1)
    root = resp.parse()

    for category_datas in root.iterfind(".//nui-tile"):
        category_title = category_datas.find('.//a').text.strip()
        category_image = 'https:' + category_datas.find(
            ".//img").get('data-responsive-image')
        category_url = URL_ROOT + category_datas.find('.//a').get('href')

        item = Listitem()
        item.label = category_title
        item.art['thumb'] = category_image
        item.set_callback(list_category_programs,
                          item_id=item_id,
                          next_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_category_programs(plugin, item_id, next_url, **kwargs):

    category_id = re.compile('categorieen/(.*?)/').findall(next_url)[0]
    resp = urlquick.get(URL_CATEGORIES_JSON % category_id)
    json_parser = json.loads(resp.text)

    for category_program_datas in json_parser:

        category_program_title = category_program_datas['title']
        category_program_image = 'https:' + category_program_datas['thumbnail']
        category_program_url = 'https:' + category_program_datas['targetUrl']

        item = Listitem()
        item.label = category_program_title
        item.art['thumb'] = category_program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          next_url=category_program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, next_url, **kwargs):

    resp = urlquick.get(next_url)
    root = resp.parse()

    if root.find(".//ul[@class='vrtnu-list']") is not None:
        list_videos_datas = root.find(".//ul[@class='vrtnu-list']").findall(
            './/li')
        for video_datas in list_videos_datas:
            video_title = video_datas.find('.//h3').text.strip()
            video_image = 'https:' + video_datas.find('.//img').get(
                'srcset').split('1x')[0].strip()
            video_plot = ''
            if video_datas.find('.//p').text is not None:
                video_plot = video_datas.find('.//p').text.strip()
            video_url = URL_ROOT + video_datas.find('.//a').get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_label=LABELS[item_id] + ' - ' + item.label,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item
    else:
        if root.find(".//div[@class='nui-content-area']") is not None:
            video_datas = root.find(".//div[@class='nui-content-area']")
            video_title = video_datas.find('.//h1').text.strip()
            video_image = 'https:' + video_datas.find('.//img').get(
                'srcset').strip()
            video_plot = video_datas.find(
                ".//div[@class='content__shortdescription']").text.strip()
            video_url = re.compile(r'page_url":"(.*?)"').findall(resp.text)[0]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_label=LABELS[item_id] + ' - ' + item.label,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    session_requests = requests.session()

    if plugin.setting.get_string('vrt.login') == '' or\
            plugin.setting.get_string('vrt.password') == '':
        xbmcgui.Dialog().ok(
            'Info',
            plugin.localize(30604) % ('VRT NU', 'https://www.vrt.be/vrtnu/'))
        return False

    # Build PAYLOAD
    payload = {
        'loginID': plugin.setting.get_string('vrt.login'),
        'password': plugin.setting.get_string('vrt.password'),
        'targetEnv': 'jssdk',
        'APIKey': get_api_key(),
        'includeSSOToken': 'true',
        'authMode': 'cookie'
    }
    # Login / Verify
    resp = session_requests.post(URL_LOGIN, data=payload)
    json_parser = json.loads(resp.text)
    if json_parser['statusCode'] != 200:
        plugin.notify('ERROR', 'VRT NU : ' + plugin.localize(30711))
        return False
    # Request Token
    headers = {
        'Content-Type': 'application/json',
        'Referer': URL_ROOT + '/vrtnu/'
    }
    data = '{"uid": "%s", ' \
        '"uidsig": "%s", ' \
        '"ts": "%s", ' \
        '"email": "%s"}' % (
            json_parser['UID'],
            json_parser['UIDSignature'],
            json_parser['signatureTimestamp'],
            plugin.setting.get_string('vrt.login'))
    session_requests.post(URL_TOKEN, data=data, headers=headers)
    # Video ID
    video_id_datas_url = video_url[:-1] + '.mssecurevideo.json'
    resp3 = session_requests.get(video_id_datas_url)
    json_parser2 = json.loads(resp3.text)
    video_id = ''
    for video_id_datas in list(json_parser2.items()):
        video_id = json_parser2[video_id_datas[0]]['videoid']
    # Stream Url
    resp4 = session_requests.get(URL_STREAM_JSON % video_id)
    json_parser3 = json.loads(resp4.text)
    stream_url = ''
    for stream_datas in json_parser3['targetUrls']:
        if 'HLS' in stream_datas['type']:
            stream_url = stream_datas['url']

    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.post(URL_TOKEN_LIVE, max_age=-1)
    json_parser_token = json.loads(resp.text)
    resp2 = urlquick.get(URL_LIVE %
                         (item_id, json_parser_token["vrtPlayerToken"]),
                         max_age=-1)
    json_parser_stream_datas = json.loads(resp2.text)
    stream_url = ''
    if "code" in json_parser_stream_datas:
        if json_parser_stream_datas["code"] == "INVALID_LOCATION":
            plugin.notify('ERROR', plugin.localize(30713))
        return False
    for stream_datas in json_parser_stream_datas["targetUrls"]:
        if stream_datas["type"] == "hls_aes":
            stream_url = stream_datas["url"]
    return stream_url
