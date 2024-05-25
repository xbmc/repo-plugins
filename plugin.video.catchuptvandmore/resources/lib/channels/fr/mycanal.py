# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import base64
import json
import math
import pickle
import random
import re
import time

# noinspection PyUnresolvedReferences
import inputstreamhelper
import requests
import urlquick
# noinspection PyUnresolvedReferences
import xbmcvfs
# noinspection PyUnresolvedReferences
from xbmc import getCondVisibility

try:
    from urllib.parse import quote, urlencode
except ImportError:
    # noinspection PyUnresolvedReferences
    from urllib import quote, urlencode
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui

from resources.lib import resolver_proxy, web_utils
from resources.lib.addon_utils import get_item_media_path
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, \
    get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.canalplus.com/'
URL_REPLAY_CHANNEL = URL_ROOT + 'chaines/%s'
# Channel name


OFFER_ZONE = "cpfra"
DEVICE_ID = "3"
DRM_ID = "31"
OFFER_LOCATION = 'fr'

URL_TOKEN = 'https://pass-api-v2.canal-plus.com/services/apipublique/createToken'

SECURE_GEN_HAPI = 'https://secure-gen-hapi.canal-plus.com'
URL_VIDEO_DATAS = SECURE_GEN_HAPI + '/conso/playset/unit/%s'
URL_STREAM_DATAS = SECURE_GEN_HAPI + '/conso/view'

URL_JSON = "https://dsh-m013.ora02.live-scy.canalplus-cdn.net/plfiles/v2/metr/dash-ssl/%s-hd.json"

PARAMS_URL_JSON = {
    'device': 'PC',
    'route': 'scy-ora02',
    'edge': 'routemeup.canalplus-bo.net'
}

CANALPLUS_BO_NET_API = 'https://secure-browser.canalplus-bo.net/WebPortal/ottlivetv/api/V4'
LICENSE_URL = CANALPLUS_BO_NET_API + '/zones/cpfra/devices/31/apps/1/jobs/GetLicence'

CANALPLUSTECH_PRO_API = 'https://ltv.slc-app-aka.prod.bo.canal.canalplustech.pro/api/V4'
LIVE_TOKEN_URL = CANALPLUSTECH_PRO_API + '/zones/cpfra/devices/3/apps/1/jobs/InitLiveTV'

CERTIFICATE_URL = 'https://secure-webtv-static.canal-plus.com/widevine/cert/cert_license_widevine_com.bin'

# The channel need to be on the same order has the website
LIVE_MYCANAL = {
    'canalplus': 'canalplus',
    'c8': 'c8',
    'cnews': "cnews",
    'cstar': 'cstar',
}

LIVE_DAILYMOTION = {
    'c8': 'x5gv5rr',
    'cstar': 'x5gv5v0',
    'canalplus': 'x5gv6be'
}

REACT_QUERY_STATE = re.compile(r'window.REACT_QUERY_STATE\s*=\s*(.*?);\s*document\.documentElement\.classList\.remove')
WINDOW_DATA = re.compile(r'window.__data=(.*?);\s*window.REACT_QUERY_STATE')


class CustomSSLContextHTTPAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)


def get_key_id():
    def rnd():
        floor = math.floor((1 + random.random()) * 9007199254740991)
        s = hex(int(floor))
        return str(s)[4:]

    ts = int(1000 * time.time())

    device_key_id = str(ts) + '-' + rnd()
    device_id_full = device_key_id + ':0:' + str(ts + 2000) + '-' + rnd()
    session_id = str(ts + 3000) + '-' + rnd()
    return device_key_id, device_id_full, session_id


def create_item_mpd(plugin, certificate_data, item, json_stream_data, secure_gen_hapi_headers, subtitles):
    headers = secure_gen_hapi_headers.copy()
    headers.update({'Content-Type': 'text/plain'})
    with xbmcvfs.File('special://userdata/addon_data/plugin.video.catchuptvandmore/headersCanal', 'wb') as f1:
        pickle.dump(headers, f1)
    # Return HTTP 200 but the response is not correctly interpreted by inputstream
    # (https://github.com/peak3d/inputstream.adaptive/issues/267)
    license_url = "http://127.0.0.1:5057/license=" + SECURE_GEN_HAPI + json_stream_data['@licence']
    license_url += '?drmConfig=mkpl::true|%s|b{SSM}|B' % urlencode(headers)

    if getCondVisibility('system.platform.android') or plugin.setting.get_boolean('device_l1'):
        input_stream_properties = {"server_certificate": certificate_data}
    else:
        # image doesn't work for big resolutions if device is not certified like android
        input_stream_properties = {
            "server_certificate": certificate_data,
            "chooser_resolution_secure_max": "640p"
        }

    return resolver_proxy.get_stream_with_quality(plugin, video_url=item.path, manifest_type="mpd",
                                                  license_url=license_url, headers=headers,
                                                  subtitles=subtitles,
                                                  input_stream_properties=input_stream_properties)


def set_subtitles(plugin, stream, item):
    url = ''
    if plugin.setting.get_boolean('active_subtitle'):
        for file in stream["files"]:
            if 'vtt' in file["mimeType"] or file["type"] == 'subtitle':
                url = file['distribURL']
    if 'http' in url:
        item.subtitles.append(url)
        return url
    return None


def is_valid_drm(drm_type):
    return (drm_type == "DRM MKPC Widevine DASH"
            or drm_type == "Non protégé"
            or drm_type == "UNPROTECTED"
            or drm_type == 'DRM_MKPC_WIDEVINE_DASH'
            or drm_type == 'DRM_WIDEVINE')


def get_certificate_data(plugin, certificate_url, session_requests):
    headers = {
        "User-Agent": web_utils.get_random_ua(),
        "Accept": "application/json, text/plain, */*",
        "referrer": URL_ROOT
    }
    resp = session_requests.get(certificate_url, headers=headers)
    if not resp:
        plugin.notify(plugin.localize(30600), 'get_certificate_data response: empty')
        return None
    return base64.b64encode(resp.content).decode('utf-8')


def get_pass_token(plugin, data_pass, pass_url, session_requests):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": URL_ROOT,
        "Referer": URL_ROOT,
        "User-Agent": web_utils.get_random_ua()
    }
    resp = session_requests.post(pass_url, data=data_pass, headers=headers, timeout=3)
    if not resp:
        plugin.notify(plugin.localize(30600), 'get_pass_token response: empty')
        return None, None
    resp_json = resp.json()
    pass_token = resp_json['response']['passToken']
    device_id = resp_json["response"]["userData"]["deviceId"].split(':')[0]
    return pass_token, device_id


def get_config(plugin, session_requests):
    resp = session_requests.get("https://player.canalplus.com/one/configs/v2/10/mycanal/prod.json")
    if not resp:
        plugin.notify(plugin.localize(30600), 'get_config response: empty')
        return None
    resp_json = resp.json()
    live_init = resp_json['live']['init'].format(offerZone=OFFER_ZONE, deviceId=DEVICE_ID)
    pass_url = resp_json['pass']['url'].format(offerLocation=OFFER_LOCATION)
    certificate_url = resp_json['drm']['certificates']['widevine']
    portail_id = resp_json['pass']['portailId']
    license_url = resp_json['live']['licence'].format(offerZone=OFFER_ZONE, drmId=DRM_ID)
    return certificate_url, license_url, live_init, pass_url, portail_id


@Route.register
def mycanal_root(plugin, **kwargs):
    # (item_id, label, thumb, fanart)
    channels = [
        ('canalplus-en-clair', 'Canal +', 'canalplus.png', 'canalplus_fanart.jpg'),
        ('c8', 'C8', 'c8.png', 'c8_fanart.jpg'),
        ('cstar', 'CStar', 'cstar.png', 'cstar_fanart.jpg'),
        ('cnews', 'CNews', 'cnews.png', 'cnews_fanart.jpg'),
        # ('seasons', 'Seasons', 'seasons.png', 'seasons_fanart.jpg'),
        ('comedie', 'Comédie +', 'comedie.png', 'comedie_fanart.jpg'),
        ('les-chaines-planete', 'Les chaînes planètes +', 'leschainesplanete.png', 'leschainesplanete_fanart.jpg'),
        ('golfplus', 'Golf +', 'golfplus.png', 'golfplus_fanart.jpg'),
        ('cineplus-en-clair', 'Ciné +', 'cineplus.png', 'cineplus_fanart.jpg'),
        ('infosportplus', 'INFOSPORT+', 'infosportplus.png', 'infosportplus_fanart.jpg'),
        ('polar-plus', 'Polar+', 'polarplus.png', 'polarplus_fanart.jpg'),
        ('clique-tv', 'Clique TV', 'cliquetv.png', 'cliquetv_fanart.jpg'),
        ('piwi', 'Piwi +', 'piwiplus.png', 'piwiplus_fanart.jpg'),
        ('teletoon', 'TéléToon +', 'teletoonplus.png', 'teletoonplus_fanart.jpg'),
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/fr/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/fr/' + channel_infos[3])
        item.set_callback(list_channel, channel_infos[0])
        item_post_treatment(item)
        yield item


@Route.register
def list_channel(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """

    resp = urlquick.get(URL_REPLAY_CHANNEL % item_id)
    react_query_state = REACT_QUERY_STATE.findall(resp.text)[0]
    json_react_query_state = json.loads(react_query_state)

    for category in json_react_query_state["queries"][0]["state"]["data"]["strates"]:
        if category["type"] == "carrousel":
            title = category['context']['context_page_title']
            key_value = category['reactKey'] if 'reactKey' in category else None
            item = Listitem()
            item.label = title
            item.set_callback(list_contents, item_id=item_id, key_value=key_value, category=category)
            item_post_treatment(item)
            yield item
        elif category["type"] == "contentRow":
            if 'title' in category:
                title = category['title']
            elif 'no title' not in category['context']['context_list_category']:
                title = category['context']['context_list_category']
            else:
                # title = category['context']['context_list_id']
                continue
            key_value = category['reactKey'] if 'reactKey' in category else None
            if 'strateMode' in category and category['strateMode'] == 'liveTV':
                continue
            item = Listitem()
            item.label = title
            item.set_callback(list_contents, item_id=item_id, key_value=key_value, category=category)
            item_post_treatment(item)
            yield item


@Route.register
def list_contents(plugin, item_id, key_value, category, **kwargs):
    if category is None:
        if key_value is None:
            yield False
        category = find_category(item_id, key_value)

    if category is None:
        yield False

    for content in category["contents"]:
        if content["type"] == 'article':
            continue

        content_title = content["onClick"]["displayName"]
        content_image = ''
        if 'URLImageOptimizedRegular' in content_image:
            if 'http' in content["URLImageOptimizedRegular"]:
                content_image = content["URLImageOptimizedRegular"]
            else:
                content_image = content["URLImage"]
        else:
            if 'URLImage' in content:
                content_image = content["URLImage"]
        content_url = content["onClick"]["URLPage"]

        item = Listitem()
        item.label = content_title
        item.art['thumb'] = item.art['landscape'] = content_image
        item.set_callback(list_programs, item_id=item_id, next_url=content_url)
        item_post_treatment(item)
        yield item


def find_category(item_id, key_value):
    resp = urlquick.get(URL_REPLAY_CHANNEL % item_id)
    react_query_state = REACT_QUERY_STATE.findall(resp.text)[0]
    json_react_query_state = json.loads(react_query_state)
    for category in json_react_query_state["queries"][0]["state"]["data"]["strates"]:
        if 'reactKey' in category and category['reactKey'] == key_value:
            return category
    return None


@Route.register
def list_programs(plugin, item_id, next_url, **kwargs):
    json_parser = urlquick.get(next_url).json()

    if 'strates' in json_parser:

        program_title = json_parser['currentPage']['displayName']

        for strate in json_parser["strates"]:
            if strate["type"] == "contentRow" or strate["type"] == "contentGrid":
                strate_title = program_title + ' - ' + strate["title"]

                item = Listitem()
                item.label = strate_title

                item.set_callback(list_sub_programs, item_id=item_id, next_url=next_url, strate_title=strate_title)
                item_post_treatment(item)
                yield item

    elif 'episodes' in json_parser:

        program_title = json_parser['currentPage']['displayName']

        for video_datas in json_parser["episodes"]['contents']:
            video_title = program_title + ' - ' + video_datas['title']
            video_image = video_datas['URLImage']
            video_plot = video_datas['summary'] if 'summary' in video_datas else ''
            if 'contentAvailability' in video_datas:
                video_url = video_datas["contentAvailability"]["availabilities"]["stream"]["URLMedias"]
            else:
                video_url = video_datas["URLMedias"]

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

        if json_parser["episodes"]["paging"]["hasNextPage"]:
            yield Listitem.next_page(item_id=item_id,
                                     next_url=json_parser["episodes"]["paging"]["URLPage"])

    elif 'detail' in json_parser:

        if 'seasons' in json_parser['detail']:
            for seasons_datas in json_parser['detail']['seasons']:
                display_name = seasons_datas['onClick']['displayName']
                if 'seasonNumber' in seasons_datas:
                    season_number = str(seasons_datas["seasonNumber"])
                    season_title = display_name + ' (Saison ' + season_number + ')'
                else:
                    season_title = display_name
                season_url = seasons_datas['onClick']['URLPage']

                item = Listitem()
                item.label = season_title
                item.set_callback(
                    list_videos, item_id=item_id, next_url=season_url)
                item_post_treatment(item)
                yield item

        else:
            # Case just one video
            program_title = json_parser['currentPage']['displayName']
            video_datas = json_parser['detail']['informations']

            if 'subtitle' in video_datas:
                video_title = program_title + ' - ' + video_datas['title'] + ' - ' + video_datas['subtitle']
            else:
                video_title = program_title + ' - ' + video_datas['title']
            video_image = video_datas['URLImage']
            video_plot = video_datas['summary'] if 'summary' in video_datas else ''
            if 'contentAvailability' in video_datas:
                video_url = video_datas["contentAvailability"]["availabilities"]["stream"]["URLMedias"]
            else:
                video_url = video_datas["URLMedias"]

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

        for content_datas in json_parser['contents']:
            if content_datas["type"] != 'article':
                title = content_datas['title']
                if 'subtitle' in content_datas:
                    content_title = title + ' - ' + content_datas['subtitle']
                else:
                    content_title = title
                content_image = content_datas['URLImage']
                content_url = content_datas['onClick']['URLPage']

                item = Listitem()
                item.label = content_title
                item.art['thumb'] = item.art['landscape'] = content_image

                item.set_callback(
                    list_programs,
                    item_id=item_id,
                    next_url=content_url)
                item_post_treatment(item)
                yield item


@Route.register
def list_sub_programs(plugin, item_id, next_url, strate_title, **kwargs):
    json_parser = urlquick.get(next_url).json()

    if 'strates' in json_parser:

        for strate in json_parser["strates"]:
            if strate["type"] != "contentRow" and strate["type"] != "contentGrid":
                continue

            if strate["title"] not in strate_title:
                continue

            for content_datas in strate['contents']:
                if content_datas["type"] != 'article':
                    if 'subtitle' in content_datas:
                        content_title = '{title} - {subtitle}'.format(**content_datas)
                    else:
                        content_title = content_datas['title']
                    content_image = content_datas['URLImage']
                    content_url = content_datas['onClick']['URLPage']

                    item = Listitem()
                    item.label = content_title
                    item.art['thumb'] = item.art['landscape'] = content_image
                    item.set_callback(
                        list_programs,
                        item_id=item_id,
                        next_url=content_url)
                    item_post_treatment(item)
                    yield item


@Route.register
def list_videos(plugin, item_id, next_url, **kwargs):
    json_parser = urlquick.get(next_url).json()

    program_title = json_parser['currentPage']['displayName']

    for video_datas in json_parser["episodes"]['contents']:
        video_title = program_title + ' - ' + video_datas['title']
        video_image = video_datas['URLImage']
        video_plot = video_datas['summary'] if 'summary' in video_datas else ''
        if 'contentAvailability' in video_datas:
            video_url = video_datas["contentAvailability"]["availabilities"]["stream"]["URLMedias"]
        else:
            video_url = video_datas["URLMedias"]

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

    if json_parser["episodes"]["paging"]["hasNextPage"]:
        yield Listitem.next_page(item_id=item_id,
                                 next_url=json_parser["episodes"]["paging"]["URLPage"])


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  next_url,
                  download_mode=False,
                  **kwargs):
    if 'tokenCMS' in next_url:
        if get_kodi_version() < 18:
            xbmcgui.Dialog().ok('Info', plugin.localize(30602))
            return False

        if download_mode:
            xbmcgui.Dialog().ok('Info', plugin.localize(30603))
            return False

        device_key_id, device_id_full, session_id = get_key_id()

        session_requests = requests.sessions.Session()
        session_requests.adapters.pop("https://", None)
        session_requests.mount("https://", CustomSSLContextHTTPAdapter(ctx))

        certificate_url, license_url, live_init, pass_url, portail_id = get_config(plugin, session_requests)

        data_pass = {
            "deviceId": device_id_full,
            "media": "web",
            "noCache": "false",
            "portailId": portail_id,
            "sessionId": session_id,
            "passIdType": "pass",
            "vect": "INTERNET",
            "offerZone": OFFER_ZONE,
        }

        pass_token, device_id = get_pass_token(plugin, data_pass, pass_url, session_requests)
        if pass_token is None:
            return False

        video_id = next_url.split('/')[-1].split('.json')[0]
        secure_gen_hapi_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Authorization': 'PASS Token="%s"' % pass_token,
            'Content-Type': 'application/json; charset=UTF-8',
            'XX-DEVICE': 'pc %s' % device_id,
            'XX-DOMAIN': OFFER_ZONE,
            'XX-OPERATOR': 'pc',
            'XX-Profile-Id': '0',
            'XX-SERVICE': 'mycanal',
            'User-Agent': web_utils.get_random_ua(),
            'Origin': 'https://www.mycanal.fr'
        }

        value_datas_jsonparser = session_requests.get(URL_VIDEO_DATAS % video_id,
                                                      headers=secure_gen_hapi_headers).json()

        if 'available' not in value_datas_jsonparser:
            # Some videos require an account
            # Get error
            plugin.notify('ERROR', plugin.localize(30712))
            return False

        payload = None
        drm_type = None
        for stream_datas in value_datas_jsonparser["available"]:
            if 'drmType' in stream_datas and is_valid_drm(stream_datas['drmType']):
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
                drm_type = stream_datas['drmType']
                break

        if payload is None:
            return False

        payload = json.dumps(payload)
        json_stream_data = session_requests.put(URL_STREAM_DATAS, data=payload,
                                                headers=secure_gen_hapi_headers).json()

        if ('@medias' not in json_stream_data
                and 'message' in json_stream_data
                and 'status' in json_stream_data
                and json_stream_data['status'] != 200):
            xbmcgui.Dialog().ok('Info', json_stream_data['message'])
            return False

        json_real_stream_data = session_requests.get(SECURE_GEN_HAPI +
                                                     json_stream_data['@medias'],
                                                     headers=secure_gen_hapi_headers).json()

        certificate_data = base64.b64encode(requests.get(CERTIFICATE_URL).content).decode('utf-8')

        item = Listitem()
        stream_data_type = "VM" if 'VM' in json_real_stream_data else "VF"

        if stream_data_type in json_real_stream_data:
            first_stream = json_real_stream_data[stream_data_type][0]
            item.path = first_stream["media"][0]["distribURL"]
        else:
            first_stream = json_real_stream_data[0]
            found_file = False
            for file in first_stream["files"]:
                if file["type"] == 'video':
                    item.path = file["distribURL"]
                    found_file = True
                    break
            if not found_file:
                return False

        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'

        subtitles = set_subtitles(plugin, first_stream, item)

        if ".ism" in item.path:
            is_helper = inputstreamhelper.Helper('ism')
            if not is_helper.check_inputstream():
                return False

            if drm_type != "UNPROTECTED":
                plugin.notify("INFO", "ism + drm not implemented", Script.NOTIFY_INFO)
                return False

            video_url = item.path + "/manifest"
            input_stream_properties = {"license_type": None}

            return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url,
                                                          manifest_type="ism",
                                                          input_stream_properties=input_stream_properties,
                                                          subtitles=subtitles)

        if ".mpd" in item.path:

            is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
            if not is_helper.check_inputstream():
                return False

            return create_item_mpd(plugin, certificate_data, item, json_stream_data, secure_gen_hapi_headers, subtitles)

        return item

    json_parser = urlquick.get(next_url, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1).json()
    return json_parser["detail"]["informations"]["playsets"]["available"][0]["videoURL"]


def get_live_token(plugin, device_key_id, live_init, pass_token, session_requests):
    data = {
        "ServiceRequest": {
            "InData": {
                "DeviceKeyId": device_key_id,
                "PassData": {"Id": 0, "Token": pass_token},
                "PDSData": {"GroupTypes": "1;2;4"},
                "UserKeyId": "_tl1sb683u"
            }
        }
    }
    headers = {
        "User-Agent": web_utils.get_random_ua(),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "referrer": URL_ROOT
    }
    resp = session_requests.post(live_init, json=data, headers=headers)
    if not resp:
        plugin.notify(plugin.localize(30600), 'get_pass_token response: empty')
        return None
    resp_json = resp.json()
    return resp_json['ServiceResponse']['OutData']['LiveToken']


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    if xbmcgui.Dialog().select(Script.localize(30174), ["MyCanal", "Dailymotion"]):
        return resolver_proxy.get_stream_dailymotion(plugin, LIVE_DAILYMOTION[item_id], False)

    device_key_id, device_id_full, session_id = get_key_id()

    session_requests = requests.sessions.Session()
    session_requests.adapters.pop("https://", None)
    session_requests.mount("https://", CustomSSLContextHTTPAdapter(ctx))

    certificate_url, license_url, live_init, pass_url, portail_id = get_config(plugin, session_requests)

    resp_app_config = session_requests.get(URL_REPLAY_CHANNEL % item_id)
    epg_id = re.compile('\"epgidOTT\":\"(.+?)\"').findall(resp_app_config.text)[0].split(",")

    data_pass = {
        "deviceId": device_id_full,
        "media": "web",
        "noCache": "false",
        "portailId": portail_id,
        "sessionId": session_id,
        "passIdType": "pass",
        "vect": "INTERNET",
        "offerZone": OFFER_ZONE,
    }

    pass_token, device_id = get_pass_token(plugin, data_pass, pass_url, session_requests)
    if pass_token is None:
        return False

    live_token = get_live_token(plugin, device_key_id, live_init, pass_token, session_requests)
    if live_token is None:
        return False

    index_epg = [i for i, t in enumerate(LIVE_MYCANAL) if t == item_id][0]
    # body_data = urllib.parse.quote(json.dumps(dict_data))
    data_drm = quote('''{
        "ServiceRequest":
        {
            "InData":
            {
                "ChallengeInfo": "b{SSM}",
                "DeviceKeyId": "''' + device_key_id + '''",
                "EpgId": ''' + epg_id[index_epg] + ''',
                "LiveToken": "''' + live_token + '''",
                "Mode": "MKPL",
                "UserKeyId": "_vf1itm7yv"
            }
        }
    }''')
    if item_id == "canalplus":
        item_id = "canalplusclair"
    resp = session_requests.get(URL_JSON % item_id, params=PARAMS_URL_JSON)
    if not resp:
        plugin.notify(plugin.localize(30600), 'get dash-ssl response: empty')
        return None
    resp_json = resp.json()
    url_stream = resp_json["primary"]["src"]

    certificate_data = get_certificate_data(plugin, certificate_url, session_requests)
    if certificate_data is None:
        return False

    headers_licence = {
        'User-Agent': web_utils.get_random_ua(),
        'Content-Type': ''
    }
    item = Listitem()
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.path = url_stream
    item.property[INPUTSTREAM_PROP] = "inputstream.adaptive"
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = license_url + '|' + urlencode(
        headers_licence) + '|' + data_drm + '|JBLicenseInfo'
    item.property['inputstream.adaptive.server_certificate'] = certificate_data
    return item
