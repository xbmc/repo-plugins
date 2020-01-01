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

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict
import resources.lib.cq_utils as cqu

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


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


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
    json_replay = re.compile('window.__data=(.*?)};').findall(resp.text)[0]
    json_parser = json.loads(json_replay + ('}'))

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
    json_replay = re.compile('window.__data=(.*?)};').findall(resp.text)[0]
    json_parser = json.loads(json_replay + ('}'))

    for category in json_parser["templates"]["landing"]["strates"]:
        if category["type"] == "contentRow" or category["type"] == "contentGrid":
            if 'title' in category:
                title = category['title']
            else:
                title = json_parser["page"]["displayName"]

            if title_value == title:
                for content in category["contents"]:
                    if content["type"] == 'quicktime' or content["type"] == 'pfv' or content["type"] == 'detailPage':
                        if 'subtitle' in content:
                            video_title = content["onClick"]["displayName"] + ' (' + content["subtitle"] + ')'
                        else:
                            video_title = content["onClick"]["displayName"]
                        video_image = content['URLImage']
                        if content["type"] == 'quicktime':
                            video_url = content["onClick"]["URLMedias"]
                        else:
                            resp2 = urlquick.get(content["onClick"]["URLPage"])
                            json_parser2 = json.loads(resp2.text)
                            if 'URLMedias' in json_parser2['detail'][
                                    'informations']:
                                video_url = json_parser2['detail'][
                                    'informations']['URLMedias']
                            else:
                                video_url = ''

                        if video_url != '':
                            item = Listitem()
                            item.label = video_title
                            item.art['thumb'] = video_image
                            item.set_callback(
                                get_video_url,
                                item_id=item_id,
                                next_url=video_url)
                            item_post_treatment(item)
                            yield item
                    elif content["type"] == 'article':
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
                        item.art['thumb'] = program_image
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

            if sub_program_datas['type'] == 'plainTextHTML':
                continue

            if sub_program_datas['type'] == 'carrousel':
                continue

            if 'title' in sub_program_datas:
                sub_program_title = sub_program_datas["title"]

                item = Listitem()
                item.label = sub_program_title
                item.set_callback(
                    list_videos,
                    item_id=item_id,
                    next_url=next_url,
                    sub_program_title=sub_program_title)
                item_post_treatment(item)
                yield item
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

    elif 'episodes' in json_parser:

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
            video_url = video_datas['URLMedias']

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(
                get_video_url,
                item_id=item_id,
                next_url=video_url,
                video_label=LABELS[item_id] + ' - ' + item.label,
                item_dict=item2dict(item))
            item_post_treatment(item, is_playable=True, is_downloadable=True)
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
            video_url = video_datas['URLMedias']

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(
                get_video_url,
                item_id=item_id,
                next_url=video_url,
                video_label=LABELS[item_id] + ' - ' + item.label,
                item_dict=item2dict(item))
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    elif 'contents' in json_parser:

        for video_datas in json_parser['contents']:
            if 'subtitle' in video_datas:
                video_title = video_datas['title'] + ' ' + video_datas['subtitle']
            else:
                video_title = video_datas['title']
            video_image = video_datas['URLImage']
            video_url = video_datas['onClick']['URLPage']

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image

            item.set_callback(
                get_video_url,
                item_id=item_id,
                next_url=video_url,
                video_label=LABELS[item_id] + ' - ' + item.label,
                item_dict=item2dict(item))
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
        video_url = video_datas['URLMedias']

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(
            get_video_url,
            item_id=item_id,
            next_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            item_dict=item2dict(item))
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
                            item.art['thumb'] = video_image

                            item.set_callback(
                                get_video_url,
                                item_id=item_id,
                                next_url=video_url,
                                video_label=LABELS[item_id] + ' - ' +
                                item.label,
                                item_dict=item2dict(item))
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
                            item.art['thumb'] = video_image

                            item.set_callback(
                                get_video_url,
                                item_id=item_id,
                                video_label=LABELS[item_id] + ' - ' +
                                item.label,
                                next_url=video_url,
                                item_dict=item2dict(item))
                            item_post_treatment(
                                item, is_playable=True, is_downloadable=True)
                            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  next_url,
                  item_dict=None,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(
        next_url, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
    json_parser = json.loads(resp.text)

    if json_parser["detail"]["informations"]['consumptionPlatform'] == 'HAPI':

        # Get DeviceId
        header_device_id = {
            'referer':
            'https://secure-player.canal-plus.com/one/prod/v2/',
        }
        resp_device_id = urlquick.get(URL_DEVICE_ID, headers=header_device_id, max_age=-1)
        device_id = re.compile(
            r'deviceId\"\:\"(.*?)\"').findall(resp_device_id.text)[0]

        if xbmc.getCondVisibility('system.platform.android'):

            if cqu.get_kodi_version() < 18:
                xbmcgui.Dialog().ok('Info', plugin.localize(30602))
                return False

            is_helper = inputstreamhelper.Helper('mpd')
            if not is_helper.check_inputstream():
                return False

            if download_mode:
                xbmcgui.Dialog().ok('Info', plugin.localize(30603))
                return False

            Script.notify("INFO", plugin.localize(LABELS['drm_notification']),
                          Script.NOTIFY_INFO)
            return False

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

            # Get stream Id
            for stream_datas in json_parser["detail"]["informations"]["videoURLs"]:
                if stream_datas["drmType"] == "DRM PlayReady":
                    payload = {
                        'comMode': stream_datas['comMode'],
                        'contentId': stream_datas['contentId'],
                        'distMode': stream_datas['distMode'],
                        'distTechnology': stream_datas['distTechnology'],
                        'drmType': stream_datas['drmType'],
                        'functionalType': stream_datas['functionalType'],
                        'hash': stream_datas['hash'],
                        'idKey': stream_datas['idKey'],
                        'quality': stream_datas['quality']
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
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
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
                    item.label = item_dict['label']
                    item.info.update(item_dict['info'])
                    item.art.update(item_dict['art'])
                    item.property['inputstreamaddon'] = 'inputstream.adaptive'
                    item.property['inputstream.adaptive.manifest_type'] = 'ism'
                    item.property[
                        'inputstream.adaptive.license_type'] = 'com.microsoft.playready'
                    return item
        else:
            if cqu.get_kodi_version() < 18:
                xbmcgui.Dialog().ok('Info', plugin.localize(30602))
                return False

            is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
            if not is_helper.check_inputstream():
                return False

            if download_mode:
                xbmcgui.Dialog().ok('Info', plugin.localize(30603))
                return False

            Script.notify("INFO", plugin.localize(LABELS['drm_notification']),
                          Script.NOTIFY_INFO)
            return False

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

            # Get stream Id
            for stream_datas in json_parser["detail"]["informations"]["videoURLs"]:
                if 'Widevine' in stream_datas["drmType"]:
                    payload = {
                        'comMode': stream_datas['comMode'],
                        'contentId': stream_datas['contentId'],
                        'distMode': stream_datas['distMode'],
                        'distTechnology': stream_datas['distTechnology'],
                        'drmType': stream_datas['drmType'],
                        'functionalType': stream_datas['functionalType'],
                        'hash': stream_datas['hash'],
                        'idKey': stream_datas['idKey'],
                        'quality': stream_datas['quality']
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
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36'
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
                    item.label = item_dict['label']
                    item.info.update(item_dict['info'])
                    item.art.update(item_dict['art'])
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
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
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
                    item.property['inputstream.adaptive.license_key'] = jsonparser_stream_datas['@licence'] + '?drmType=DRM%20Widevine' + '|%s|b{SSM}|' % urlencode(headers2)
                    return item

    stream_url = ''
    for stream_datas in json_parser["detail"]["informations"]["videoURLs"]:
        if stream_datas["encryption"] == 'clear':
            stream_url = stream_datas["videoURL"]

    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    return resolver_proxy.get_stream_dailymotion(
        plugin, LIVE_DAILYMOTION_ID[item_id], False)
