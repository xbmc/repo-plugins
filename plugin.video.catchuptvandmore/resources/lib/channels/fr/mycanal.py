# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017 SylvainCecchetto

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


from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info
from resources.lib.addon_utils import get_item_media_path

import inputstreamhelper
import re
import json
import urlquick
from kodi_six import xbmc
from kodi_six import xbmcgui
import requests
# Working for Python 2/3
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

# TO DO
# Wait Kodi 18 to use live with DRM

# URL :
URL_ROOT_SITE = 'https://www.mycanal.fr'
# Channel

# Replay channel :
URL_REPLAY = URL_ROOT_SITE + '/chaines/%s'
# Channel name

URL_TOKEN = 'https://pass-api-v2.canal-plus.com/services/apipublique/createToken'

URL_VIDEO_DATAS = 'https://secure-gen-hapi.canal-plus.com/conso/playset?contentId=%s'

URL_STREAM_DATAS = 'https://secure-gen-hapi.canal-plus.com/conso/view'

URL_DEVICE_ID = 'https://pass.canal-plus.com/service/HelloJSON.php'

# TODO
URL_LICENCE_DRM = '[license-server url]|[Header]|[Post-Data]|[Response]'
# com.widevine.alpha
# license_key must be a string template with 4 | separated fields: [license-server url]|[Header]|[Post-Data]|[Response] in which [license-server url] allows B{SSM} placeholder and [Post-Data] allows [b/B/R]{SSM} and [b/B/R]{SID} placeholders to transport the widevine challenge and if required the DRM SessionId in base64NonURLencoded, Base64URLencoded or Raw format.
# [Response] can be a.) empty or R to specify that the response payload of the license request is binary format, b.) B if the response payload is base64 encoded or c.) J[licensetoken] if the license key data is located in a JSON struct returned in the response payload.
# inputstream.adaptive searches for the key [licensetoken] and handles the value as base64 encoded data.

# Dailymotion Id get from these pages below
# - http://www.dailymotion.com/cstar
# - http://www.dailymotion.com/canalplus
# - http://www.dailymotion.com/C8TV
LIVE_DAILYMOTION_ID = {
    'c8': 'x5gv5rr',
    'cstar': 'x5gv5v0',
    'canalplus': 'x5gv6be'
}


@Route.register
def mycanal_root(plugin, **kwargs):

    # (item_id, label, thumb, fanart)
    channels = [
        ('canalplus', 'Canal +', 'canalplus.png', 'canalplus_fanart.jpg'),
        ('c8', 'C8', 'c8.png', 'c8_fanart.jpg'),
        ('cstar', 'CStar', 'cstar.png', 'cstar_fanart.jpg'),
        ('seasons', 'Seasons', 'seasons.png', 'seasons_fanart.jpg'),
        ('comedie', 'Comédie +', 'comedie.png', 'comedie_fanart.jpg'),
        ('les-chaines-planete', 'Les chaînes planètes +', 'leschainesplanete.png', 'leschainesplanete_fanart.jpg'),
        ('golfplus', 'Golf +', 'golfplus.png', 'golfplus_fanart.jpg'),
        ('cineplus', 'Ciné +', 'cineplus.png', 'cineplus_fanart.jpg'),
        ('infosportplus', 'INFOSPORT+', 'infosportplus.png', 'infosportplus_fanart.jpg'),
        ('polar-plus', 'Polar+', 'polarplus.png', 'polarplus_fanart.jpg'),
        ('cliquetv', 'Clique TV', 'cliquetv.png', 'cliquetv_fanart.jpg'),
        ('piwiplus', 'Piwi +', 'piwiplus.png', 'piwiplus_fanart.jpg'),
        ('teletoonplus', 'TéléToon +', 'teletoonplus.png', 'teletoonplus_fanart.jpg'),
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/fr/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/fr/' + channel_infos[3])
        item.set_callback(list_categories, channel_infos[0])
        item_post_treatment(item)
        yield item


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """

    channel_mycanal_id = ''
    if 'piwiplus' in item_id:
        channel_mycanal_id = 'Piwi+'
    elif 'teletoonplus' in item_id:
        channel_mycanal_id = 'Télétoon+'
    else:
        channel_mycanal_id = item_id

    resp = urlquick.get(URL_REPLAY % channel_mycanal_id)
    json_replay = re.compile(
        r'window.__data\=(.*?)\; window.app_config').findall(resp.text)[0]
    json_parser = json.loads(json_replay)

    for category in json_parser["templates"]["landing"]["strates"]:
        if category["type"] == "contentRow" or category["type"] == "contentGrid":
            if 'title' in category:
                title = category['title']
            else:
                title = json_parser["page"]["displayName"]

            item = Listitem()
            item.label = title
            item.set_callback(
                list_contents, item_id=item_id, title_value=title)
            item_post_treatment(item)
            yield item


@Route.register
def list_contents(plugin, item_id, title_value, **kwargs):

    channel_mycanal_id = ''
    if 'piwiplus' in item_id:
        channel_mycanal_id = 'Piwi+'
    elif 'teletoonplus' in item_id:
        channel_mycanal_id = 'Télétoon+'
    else:
        channel_mycanal_id = item_id

    resp = urlquick.get(URL_REPLAY % channel_mycanal_id)
    json_replay = re.compile(
        r'window.__data\=(.*?)\; window.app_config').findall(resp.text)[0]
    json_parser = json.loads(json_replay)

    for category in json_parser["templates"]["landing"]["strates"]:
        if category["type"] == "contentRow" or category["type"] == "contentGrid":
            if 'title' in category:
                title = category['title']
            else:
                title = json_parser["page"]["displayName"]

            if title_value == title:
                for content in category["contents"]:
                    if content["type"] == 'article':
                        continue
                    else:
                        if 'subtitle' in content:
                            program_title = content["onClick"]["displayName"] + ' (' + content["subtitle"] + ')'
                        else:
                            program_title = content["onClick"]["displayName"]
                        program_image = content['URLImage']
                        program_url = content["onClick"]["URLPage"]

                        item = Listitem()
                        item.label = program_title
                        item.art['thumb'] = item.art['landscape'] = program_image
                        item.set_callback(
                            list_sub_programs,
                            item_id=item_id,
                            next_url=program_url)
                        item_post_treatment(item)
                        yield item


@Route.register
def list_sub_programs(plugin, item_id, next_url, **kwargs):

    resp = urlquick.get(next_url)
    json_parser = json.loads(resp.text)

    if 'strates' in json_parser:
        for sub_program_datas in json_parser["strates"]:

            if 'title' in sub_program_datas:
                sub_program_title = sub_program_datas["title"]
            else:
                sub_program_title = json_parser["currentPage"]["displayName"]

            item = Listitem()
            item.label = sub_program_title
            item.set_callback(
                list_videos,
                item_id=item_id,
                next_url=next_url,
                sub_program_title=sub_program_title)
            item_post_treatment(item)
            yield item

    elif 'parentShow' in json_parser:
        if 'seasons' in json_parser['parentShow']:
            for seasons_datas in json_parser['parentShow']['seasons']:
                season_title = seasons_datas['onClick']['displayName']
                season_url = seasons_datas['onClick']['URLPage']

                item = Listitem()
                item.label = season_title
                item.set_callback(
                    list_videos_seasons, item_id=item_id, next_url=season_url)
                item_post_treatment(item)
                yield item

    elif 'detail' in json_parser:

        if 'seasons' in json_parser['detail']:
            for seasons_datas in json_parser['detail']['seasons']:
                season_title = seasons_datas['onClick']['displayName']
                season_url = seasons_datas['onClick']['URLPage']

                item = Listitem()
                item.label = season_title
                item.set_callback(
                    list_videos_seasons, item_id=item_id, next_url=season_url)
                item_post_treatment(item)
                yield item
        else:
            # Case just one video
            program_title = json_parser['currentPage']['displayName']
            video_datas = json_parser['detail']['informations']

            if 'subtitle' in video_datas:
                video_title = program_title + ' ' + video_datas['title'] + ' ' + video_datas['subtitle']
            else:
                video_title = program_title + ' ' + video_datas['title']
            video_image = video_datas['URLImage']
            video_plot = ''
            if 'summary' in video_datas:
                video_plot = video_datas['summary']
            if 'URLMedias' in video_datas:
                video_url = video_datas['URLMedias']
            else:
                video_url = URL_ROOT_SITE + json_parser['currentPage']['path']

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(
                get_video_url,
                item_id=item_id,
                next_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    elif 'contents' in json_parser:

        for video_datas in json_parser['contents']:
            if 'subtitle' in video_datas:
                video_title = video_datas['title'] + ' ' + video_datas['subtitle']
            else:
                video_title = video_datas['title']
            video_image = video_datas['URLImage']
            video_url = URL_ROOT_SITE + video_datas['onClick']['path']

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(
                get_video_url,
                item_id=item_id,
                next_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Route.register
def list_videos_seasons(plugin, item_id, next_url, **kwargs):

    resp = urlquick.get(next_url)
    json_parser = json.loads(resp.text)

    program_title = json_parser['currentPage']['displayName']

    for video_datas in json_parser['episodes']['contents']:
        if 'subtitle' in video_datas:
            video_title = program_title + ' ' + video_datas['title'] + ' ' + video_datas['subtitle']
        else:
            video_title = program_title + ' ' + video_datas['title']
        video_image = video_datas['URLImage']
        video_plot = ''
        if 'summary' in video_datas:
            video_plot = video_datas['summary']
        video_url = URL_ROOT_SITE + video_datas['path']

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(
            get_video_url,
            item_id=item_id,
            next_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos(plugin, item_id, next_url, sub_program_title, **kwargs):

    resp = urlquick.get(next_url)
    json_parser = json.loads(resp.text)

    for sub_program_datas in json_parser["strates"]:
        if 'title' in sub_program_datas:
            if sub_program_title == sub_program_datas["title"]:
                if 'contents' in sub_program_datas:
                    for video_datas in sub_program_datas["contents"]:
                        if video_datas["type"] == 'quicktime' or video_datas["type"] == 'pfv' or video_datas["type"] == 'VoD' or video_datas["type"] == 'detailPage':
                            if 'title' in video_datas:
                                if 'subtitle' in video_datas:
                                    video_title = video_datas['subtitle'] + ' - ' + video_datas['title']
                                else:
                                    video_title = video_datas['title']
                            else:
                                video_title = video_datas["onClick"][
                                    "displayName"]
                            video_image = video_datas['URLImage']
                            video_url = ''
                            if video_datas["type"] == 'quicktime':
                                video_url = video_datas["onClick"]["URLMedias"]
                            else:
                                resp2 = urlquick.get(
                                    video_datas["onClick"]["URLPage"])
                                json_parser2 = json.loads(resp2.text)
                                video_url = json_parser2['detail'][
                                    'informations']['URLMedias']

                            item = Listitem()
                            item.label = video_title
                            item.art['thumb'] = item.art['landscape'] = video_image

                            item.set_callback(
                                get_video_url,
                                item_id=item_id,
                                next_url=video_url)
                            item_post_treatment(
                                item, is_playable=True, is_downloadable=True)
                            yield item
        else:
            if sub_program_title == json_parser["currentPage"]["displayName"]:
                if 'contents' in sub_program_datas:
                    for video_datas in sub_program_datas["contents"]:
                        if video_datas["type"] == 'quicktime' or video_datas["type"] == 'pfv' or video_datas["type"] == 'VoD' or video_datas["type"] == 'detailPage':
                            if 'title' in video_datas:
                                if 'subtitle' in video_datas:
                                    video_title = video_datas['subtitle'] + ' - ' + video_datas['title']
                                else:
                                    video_title = video_datas['title']
                            else:
                                video_title = video_datas["onClick"][
                                    "displayName"]
                            video_image = video_datas['URLImage']
                            video_url = ''
                            if video_datas["type"] == 'quicktime':
                                video_url = video_datas["onClick"]["URLMedias"]
                            else:
                                resp2 = urlquick.get(
                                    video_datas["onClick"]["URLPage"])
                                json_parser2 = json.loads(resp2.text)
                                video_url = json_parser2['detail'][
                                    'informations']['URLMedias']

                            item = Listitem()
                            item.label = video_title
                            item.art['thumb'] = item.art['landscape'] = video_image

                            item.set_callback(
                                get_video_url,
                                item_id=item_id,
                                next_url=video_url)
                            item_post_treatment(
                                item, is_playable=True, is_downloadable=True)
                            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  next_url,
                  download_mode=False,
                  **kwargs):

    if 'www.mycanal.fr' in next_url:

        if get_kodi_version() < 18:
            xbmcgui.Dialog().ok('Info', plugin.localize(30602))
            return False

        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
        if not is_helper.check_inputstream():
            return False

        if download_mode:
            xbmcgui.Dialog().ok('Info', plugin.localize(30603))
            return False

        # Get DeviceId
        header_device_id = {
            'referer':
            'https://secure-player.canal-plus.com/one/prod/v2/',
        }
        resp_device_id = urlquick.get(URL_DEVICE_ID, headers=header_device_id, max_age=-1)
        device_id = re.compile(
            r'deviceId\"\:\"(.*?)\"').findall(resp_device_id.text)[0]

        # Get Portail Id
        session_requests = requests.session()
        resp_app_config = session_requests.get(URL_REPLAY % item_id)
        json_app_config = re.compile('window.app_config=(.*?)};').findall(
            resp_app_config.text)[0]
        json_app_config_parser = json.loads(json_app_config + ('}'))
        portail_id = json_app_config_parser["api"]["pass"][
            "portailIdEncrypted"]

        # Get PassToken
        payload = {
            'deviceId': 'unknown',
            'vect': 'INTERNET',
            'media': 'PC',
            'portailId': portail_id
        }
        resp_token_mycanal = session_requests.post(URL_TOKEN, data=payload)
        json_token_parser = json.loads(resp_token_mycanal.text)
        pass_token = json_token_parser["response"]["passToken"]

        video_id = next_url.split('/')[-1]
        headers = {
            'Accept':
            'application/json, text/plain, */*',
            'Authorization':
            'PASS Token="%s"' % pass_token,
            'Content-Type':
            'application/json; charset=UTF-8',
            'XX-DEVICE':
            'pc %s' % device_id,
            'XX-DOMAIN':
            'cpfra',
            'XX-OPERATOR':
            'pc',
            'XX-Profile-Id':
            '0',
            'XX-SERVICE':
            'mycanal',
            'User-Agent':
            web_utils.get_random_ua()
        }
        value_datas_json = session_requests.get(URL_VIDEO_DATAS % video_id, headers=headers)
        value_datas_jsonparser = json.loads(value_datas_json.text)

        comMode_value = ''
        contentId_value = ''
        distMode_value = ''
        distTechnology_value = ''
        drmType_value = ''
        functionalType_value = ''
        hash_value = ''
        idKey_value = ''
        quality_value = ''

        if 'available' not in value_datas_jsonparser:
            return False

        for stream_datas in value_datas_jsonparser["available"]:
            if 'Widevine' in stream_datas["drmType"]:
                comMode_value = stream_datas['comMode']
                contentId_value = stream_datas['contentId']
                distMode_value = stream_datas['distMode']
                distTechnology_value = stream_datas['distTechnology']
                drmType_value = stream_datas['drmType']
                functionalType_value = stream_datas['functionalType']
                hash_value = stream_datas['hash']
                idKey_value = stream_datas['idKey']
                quality_value = stream_datas['quality']

        payload = {
            'comMode': comMode_value,
            'contentId': contentId_value,
            'distMode': distMode_value,
            'distTechnology': distTechnology_value,
            'drmType': drmType_value,
            'functionalType': functionalType_value,
            'hash': hash_value,
            'idKey': idKey_value,
            'quality': quality_value
        }
        payload = json.dumps(payload)
        headers = {
            'Accept':
            'application/json, text/plain, */*',
            'Authorization':
            'PASS Token="%s"' % pass_token,
            'Content-Type':
            'application/json; charset=UTF-8',
            'XX-DEVICE':
            'pc %s' % device_id,
            'XX-DOMAIN':
            'cpfra',
            'XX-OPERATOR':
            'pc',
            'XX-Profile-Id':
            '0',
            'XX-SERVICE':
            'mycanal',
            'User-Agent':
            web_utils.get_random_ua()
        }
        resp_stream_datas = session_requests.put(
            URL_STREAM_DATAS, data=payload, headers=headers)
        jsonparser_stream_datas = json.loads(resp_stream_datas.text)

        resp_real_stream_datas = session_requests.get(
            jsonparser_stream_datas['@medias'], headers=headers)
        jsonparser_real_stream_datas = json.loads(
            resp_real_stream_datas.text)

        item = Listitem()
        item.path = jsonparser_real_stream_datas["VF"][0]["media"][0]["distribURL"] + '/manifest'
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        item.property['inputstreamaddon'] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'ism'
        item.property[
            'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
        value_pass_token = 'PASS Token="%s"' % pass_token
        headers2 = {
            'Accept':
            'application/json, text/plain, */*',
            'Authorization':
            value_pass_token,
            'Content-Type':
            'text/plain',
            'User-Agent':
            web_utils.get_random_ua(),
            'Origin':
            'https://www.mycanal.fr',
            'XX-DEVICE':
            'pc %s' % device_id,
            'XX-DOMAIN':
            'cpfra',
            'XX-OPERATOR':
            'pc',
            'XX-Profile-Id':
            '0',
            'XX-SERVICE':
            'mycanal',
        }
        # Return HTTP 200 but the response is not correctly interpreted by inputstream (https://github.com/peak3d/inputstream.adaptive/issues/267)
        item.property['inputstream.adaptive.license_key'] = jsonparser_stream_datas['@licence'] + '?drmType=DRM%20Widevine' + '|%s|R{SSM}|' % urlencode(headers2)
        # return item
        Script.notify("INFO", plugin.localize(30702),
                      Script.NOTIFY_INFO)
        return False

    else:
        resp = urlquick.get(
            next_url, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
        json_parser = json.loads(resp.text)

        return json_parser["detail"]["informations"]["playsets"]["available"][0]["videoURL"]


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    return resolver_proxy.get_stream_dailymotion(
        plugin, LIVE_DAILYMOTION_ID[item_id], False)
