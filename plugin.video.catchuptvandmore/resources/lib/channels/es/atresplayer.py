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
import resources.lib.cq_utils as cqu

from bs4 import BeautifulSoup as bs

import json
import re
import requests
import urlquick
import xbmc

# TO DO
# Add Account

URL_ROOT = 'https://www.atresplayer.com/'
# channel name

URL_LIVE_STREAM = 'https://api.atresplayer.com/client/v1/player/live/%s'
# Live Id

URL_COMPTE_LOGIN = 'https://account.atresmedia.com/api/login'

LIVE_ATRES_PLAYER = {
    'antena3': 'ANTENA_3_ID',
    'lasexta': 'LA_SEXTA_ID',
    'neox': 'NEOX_ID',
    'nova': 'NOVA_ID',
    'mega': 'MEGA_ID',
    'atreseries': 'ATRESERIES_ID'
}


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):

    resp = urlquick.get(URL_ROOT)
    json_value = re.compile(
        r'PRELOADED\_STATE\_\_ \= (.*?)\}\;').findall(resp.text)[0]
    json_parser = json.loads(json_value + '}')

    for categories_datas in json_parser["channels"]:
        for category_datas in json_parser["channels"][categories_datas]["categories"]:
            category_title = category_datas["title"]
            category_url = category_datas["link"]["href"]

            item = Listitem()
            item.label = category_title
            item.set_callback(
                list_programs,
                item_id=item_id,
                category_url=category_url,
                page='0')
            yield item


@Route.register
def list_programs(plugin, item_id, category_url, page):

    resp = urlquick.get(category_url)
    json_parser = json.loads(resp.text)

    resp2 = urlquick.get(json_parser["rows"][0]["href"] + '&page=%s' % page)
    json_parser2 = json.loads(resp2.text)

    for program_datas in json_parser2["itemRows"]:
        program_title = program_datas["title"]
        program_image = program_datas["image"]["pathHorizontal"]
        program_url = program_datas["link"]["href"]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(
            list_sub_programs,
            item_id=item_id,
            program_url=program_url)
        yield item

    if json_parser2["pageInfo"]["hasNext"]:
        yield Listitem.next_page(
            item_id=item_id,
            category_url=category_url,
            page=str(int(page) + 1))


@Route.register
def list_sub_programs(plugin, item_id, program_url):

    resp = urlquick.get(program_url)
    json_parser = json.loads(resp.text)

    for sub_program_datas in json_parser["rows"]:
        if 'EPISODE' in sub_program_datas["type"] or \
            'VIDEO' in sub_program_datas["type"]:
            sub_program_title = sub_program_datas["title"]
            sub_program_url = sub_program_datas["href"]

            item = Listitem()
            item.label = sub_program_title
            item.set_callback(
                list_videos,
                item_id=item_id,
                sub_program_url=sub_program_url,
                page='0')
            yield item


@Route.register
def list_videos(plugin, item_id, sub_program_url, page):

    resp = urlquick.get(sub_program_url + '&page=%s' % page)
    json_parser = json.loads(resp.text)

    if 'itemRows' in json_parser:
        for video_datas in json_parser["itemRows"]:

            video_title = video_datas["image"]["title"]
            video_image = video_datas["image"]["pathHorizontal"]
            video_url_info = video_datas["link"]["href"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image
            item.set_callback(
                list_video_more_infos,
                item_id=item_id,
                video_url_info=video_url_info)
            yield item

        if json_parser["pageInfo"]["hasNext"]:
            yield Listitem.next_page(
                item_id=item_id,
                sub_program_url=sub_program_url,
                page=str(int(page) + 1))


@Route.register
def list_video_more_infos(plugin, item_id, video_url_info):

    resp = urlquick.get(video_url_info)
    json_parser = json.loads(resp.text)

    video_title = json_parser["seoTitle"]
    video_image = json_parser["image"]["pathHorizontal"]
    video_plot = json_parser["seoDescription"]
    video_duration = int(json_parser["duration"])
    video_url = json_parser["urlVideo"]

    item = Listitem()
    item.label = video_title
    item.art['thumb'] = video_image
    item.info['duration'] = video_duration
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
        video_url=video_url,
        item_dict=cqu.item2dict(item))
    yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, item_dict, download_mode=False, video_label=None):

    # # Create session
    # # KO - session_urlquick = urlquick.Session()
    # session_requests = requests.session()

    # # headers = {
    # #     'referer': 'https://www.atresplayer.com/',
    # #     'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'
    # # }

    # # session_requests.get('https://account.atresmedia.com/login?origin=atresplayer&additionalData=eyJwcm9tb1NpZ251cCI6ImludC1yZWdpc3RybyIsInNraXBBY3RpdmF0aW9uIjp0cnVlfQ==', headers=headers)

    # # Build PAYLOAD
    # payload = {
    #     "username": plugin.setting.get_string(
    #         'atresplayer.login'),
    #     "password": plugin.setting.get_string(
    #         'atresplayer.password')
    # }
    # print 'Username ' + plugin.setting.get_string('atresplayer.login')
    # print 'password ' + plugin.setting.get_string('atresplayer.password')

    # headers = {
    #     'origin': 'https://account.atresmedia.com',
    #     # 'referer': 'https://account.atresmedia.com/login?origin=atresplayer&additionalData=eyJwcm9tb1NpZ251cCI6ImludC1yZWdpc3RybyIsInNraXBBY3RpdmF0aW9uIjp0cnVlfQ==',
    #     'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'
    # }

    # # LOGIN
    # # KO - resp2 = session_urlquick.post(
    # #     URL_COMPTE_LOGIN, data=payload,
    # #     headers={'User-Agent': web_utils.get_ua, 'referer': URL_COMPTE_LOGIN})
    # resp2 = session_requests.post(
    #     URL_COMPTE_LOGIN, data=payload, headers=headers)
    # if resp2.status_code >= 400:
    #     plugin.notify('ERROR ' + str(resp2.status_code), 'Atresplayer : ' + plugin.localize(30711))
    #     return False
    # cookies = resp2.cookies

    # # headers = {
    # #     'origin': 'https://api.atresplayer.com',
    # #     # 'referer': 'https://account.atresmedia.com/login?origin=atresplayer&additionalData=eyJwcm9tb1NpZ251cCI6ImludC1yZWdpc3RybyIsInNraXBBY3RpdmF0aW9uIjp0cnVlfQ==',
    # #     # 'referer': 'https://www.atresplayer.com/international-login?target=https://www.atresplayer.com/',
    # #     'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'
    # # }

    # # session_requests.get(
    # #     'https://account.atresmedia.com/api/oauth/authorize?client_id=atresplayer&redirect_uri=https://api.atresplayer.com/authCallback&response_type=code&scope=openid&state=BuI9tT&additionalData=eyJwcm9tb1NpZ251cCI6ImludC1yZWdpc3RybyIsInNraXBBY3RpdmF0aW9uIjp0cnVlfQ==', headers=headers)

    # # # session_requests.get(
    # # #     'https://api.atresplayer.com/client/v1/ipLocation', headers=headers)

    # # session_requests.get(
    # #     'https://api.atresplayer.com/purchases/v1/products/available', headers=headers)

    # # session_requests.get(
    # #     'https://api.atresplayer.com/purchases/v1/packages/acquired', headers=headers)

    # headers = {
    #     'origin': 'https://www.atresplayer.com',
    #     # 'referer': 'https://account.atresmedia.com/login?origin=atresplayer&additionalData=eyJwcm9tb1NpZ251cCI6ImludC1yZWdpc3RybyIsInNraXBBY3RpdmF0aW9uIjp0cnVlfQ==',
    #     'referer': 'https://www.atresplayer.com/antena3/series/presunto-culpable/temporada-1/capitulo-1_5b9f64067ed1a8176b10eb66/',
    #     'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'
    # }

    # resp = session_requests.get(video_url, cookies=cookies, headers=headers)
    resp = urlquick.get(video_url)
    json_parser = json.loads(resp.text)
    
    if 'error' in json_parser:
        # Add Notification
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    # TODO Add verification inputstream available Kodi 17.6
    xbmc_version = int(xbmc.getInfoLabel("System.BuildVersion").split('-')[0].split('.')[0])
    if xbmc_version < 17:
        # Add Notification
        plugin.notify('ERROR', plugin.localize(30720))
        return False

    # Code from here : https://github.com/asciidisco/plugin.video.telekom-sport/blob/master/resources/lib/Utils.py
    # Thank you asciidisco
    payload = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'Addons.GetAddonDetails',
        'params': {
            'addonid': 'inputstream.adaptive',
            'properties': ['enabled', 'version']
        }
    }
    # execute the request
    response = xbmc.executeJSONRPC(json.dumps(payload))
    responses_uni = unicode(response, 'utf-8', errors='ignore')
    response_serialized = json.loads(responses_uni)
    if 'error' not in response_serialized.keys():
        result = response_serialized.get('result', {})
        addon = result.get('addon', {})
        if addon.get('enabled', False) is True:
            item = Listitem()
            item.path = json_parser["sources"][1]["src"]
            item.property['inputstreamaddon'] = 'inputstream.adaptive'
            item.property['inputstream.adaptive.manifest_type'] = 'mpd'
            item.label = item_dict['label']
            item.info.update(item_dict['info'])
            item.art.update(item_dict['art'])
            return item
    # Add Notification
    plugin.notify('ERROR', plugin.localize(30719))
    return False

    


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(
        URL_ROOT,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    lives_json = re.compile(
        r'window.__ENV__ = (.*?)\;').findall(resp.text)[0]
    json_parser = json.loads(lives_json)
    live_stream_json = urlquick.get(
        URL_LIVE_STREAM % json_parser[LIVE_ATRES_PLAYER[item_id]],
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    live_stream_jsonparser = json.loads(live_stream_json.text)
    if "sources" in live_stream_jsonparser:
        return live_stream_jsonparser["sources"][0]["src"]
    else:
        plugin.notify('ERROR', plugin.localize(30713))
        return False
