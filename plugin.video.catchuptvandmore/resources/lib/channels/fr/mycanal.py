# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re
import requests
import time
import random
import math
import inputstreamhelper
import urlquick
import base64
import pickle
import xbmcvfs

try:
    from urllib.parse import quote, urlencode
except ImportError:
    from urllib import quote, urlencode
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui

from resources.lib import resolver_proxy, web_utils
from resources.lib.addon_utils import get_item_media_path, Enum
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, \
    get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment

# URL :
URL_ROOT_SITE = 'https://www.mycanal.fr'
# Channel

# Replay channel :
URL_REPLAY = URL_ROOT_SITE + '/chaines/%s'
# Channel name

URL_TOKEN = 'https://pass-api-v2.canal-plus.com/services/apipublique/createToken'

URL_VIDEO_DATAS = 'https://secure-gen-hapi.canal-plus.com/conso/playset/unit/%s'

URL_STREAM_DATAS = 'https://secure-gen-hapi.canal-plus.com/conso/view'

LIVE_MYCANAL = {
    'c8': 'c8',
    'cstar': 'cstar',
    'canalplus': 'canalplus'
}

LIVE_DAILYMOTION = {
    'c8': 'x5gv5rr',
    'cstar': 'x5gv5v0',
    'canalplus': 'x5gv6be'
}


class CANALPLUS_links(Enum):
    DAILYMOTION = "1"
    DEFAULT = "0"


def getKeyID():
    def rnd():
        return str(hex(math.floor((1 + random.random()) * 9007199254740991)))[4:]
    ts = int(1000 * time.time())

    deviceKeyId = str(ts) + '-' + rnd()
    deviceId = deviceKeyId + ':0:' + str(ts + 2000) + '-' + rnd()
    sessionId = str(ts + 3000) + '-' + rnd()
    return deviceKeyId, deviceId, sessionId


@Route.register
def mycanal_root(plugin, **kwargs):
    # (item_id, label, thumb, fanart)
    channels = [
        ('canalplus-en-clair', 'Canal +', 'canalplus.png', 'canalplus_fanart.jpg'),
        ('c8', 'C8', 'c8.png', 'c8_fanart.jpg'),
        ('cstar', 'CStar', 'cstar.png', 'cstar_fanart.jpg'),
        ('seasons', 'Seasons', 'seasons.png', 'seasons_fanart.jpg'),
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

    resp = urlquick.get(URL_REPLAY % item_id)
    json_replay = re.compile(
        r'window.__data=(.*?); window.app_config').findall(resp.text)[0]
    json_parser = json.loads(json_replay)

    for category in json_parser["templates"]["landing"]["strates"]:
        if category["type"] == "carrousel":
            title = category['context']['context_page_title']
            key_value = category['reactKey']
            item = Listitem()
            item.label = title
            item.set_callback(
                list_contents, item_id=item_id, key_value=key_value)
            item_post_treatment(item)
            yield item
        elif category["type"] == "contentRow":
            if 'title' in category:
                title = category['title']
            else:
                title = json_parser["page"]["displayName"]
            key_value = category['reactKey']
            item = Listitem()
            item.label = title
            item.set_callback(
                list_contents, item_id=item_id, key_value=key_value)
            item_post_treatment(item)
            yield item


@Route.register
def list_contents(plugin, item_id, key_value, **kwargs):
    resp = urlquick.get(URL_REPLAY % item_id)
    json_replay = re.compile(
        r'window.__data=(.*?); window.app_config').findall(resp.text)[0]
    json_parser = json.loads(json_replay)

    for category in json_parser["templates"]["landing"]["strates"]:
        if category['reactKey'] != key_value:
            continue

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
            item.set_callback(
                list_programs,
                item_id=item_id,
                next_url=content_url)
            item_post_treatment(item)
            yield item


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

                item.set_callback(
                    list_sub_programs,
                    item_id=item_id,
                    next_url=next_url,
                    strate_title=strate_title)
                item_post_treatment(item)
                yield item

    elif 'episodes' in json_parser:

        program_title = json_parser['currentPage']['displayName']

        for video_datas in json_parser["episodes"]['contents']:
            video_title = program_title + ' - ' + video_datas['title']
            video_image = video_datas['URLImage']
            video_plot = ''
            if 'summary' in video_datas:
                video_plot = video_datas['summary']
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
            video_plot = ''
            if 'summary' in video_datas:
                video_plot = video_datas['summary']
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
        video_plot = ''
        if 'summary' in video_datas:
            video_plot = video_datas['summary']
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

        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
        if not is_helper.check_inputstream():
            return False

        if download_mode:
            xbmcgui.Dialog().ok('Info', plugin.localize(30603))
            return False

        deviceKeyId, device_id_first, sessionId = getKeyID()

        # Get Portail Id
        session_requests = requests.session()
        resp_app_config = session_requests.get(URL_REPLAY % item_id)
        json_app_config = re.compile('window.app_config=(.*?)};').findall(
            resp_app_config.text)[0]
        json_app_config_parser = json.loads(json_app_config + ('}'))
        portail_id = json_app_config_parser["api"]["pass"]["portailIdEncrypted"]

        headers = {"User-Agent": web_utils.get_random_ua(),
                   "Origin": "https://www.canalplus.com",
                   "Referer": "https://www.canalplus.com/", }

        # Get PassToken
        payload = {
            'deviceId': device_id_first,
            'vect': 'INTERNET',
            'media': 'web',
            'portailId': portail_id,
            'sessionId': sessionId,
        }

        json_token_parser = session_requests.post(URL_TOKEN, data=payload, headers=headers).json()
        pass_token = json_token_parser["response"]["passToken"]
        device_id = json_token_parser["response"]["userData"]["deviceId"].split(':')[0]

        video_id = next_url.split('/')[-1].split('.json')[0]
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Authorization': 'PASS Token="%s"' % pass_token,
            'Content-Type': 'application/json; charset=UTF-8',
            'XX-DEVICE': 'pc %s' % device_id,
            'XX-DOMAIN': 'cpfra',
            'XX-OPERATOR': 'pc',
            'XX-Profile-Id': '0',
            'XX-SERVICE': 'mycanal',
            'User-Agent': web_utils.get_random_ua(),
        }

        # Fix an ssl issue on some device.
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
        try:
            requests.packages.urllib3.contrib.pyopenssl.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'
        except AttributeError:
            # no pyopenssl support used / needed / available
            pass

        value_datas_jsonparser = session_requests.get(URL_VIDEO_DATAS % video_id, headers=headers).json()

        if 'available' not in value_datas_jsonparser:
            # Some videos required an account
            # Get error
            return False

        for stream_datas in value_datas_jsonparser["available"]:
            if stream_datas['drmType'] == "DRM MKPC Widevine DASH" or stream_datas['drmType'] == "Non protégé":
                payload = {
                    'comMode': stream_datas['comMode'],
                    'contentId': stream_datas['contentId'],
                    'distMode': stream_datas['distMode'],
                    'distTechnology': stream_datas['distTechnology'],
                    'drmType': stream_datas['drmType'],
                    'functionalType': stream_datas['functionalType'],
                    'hash': stream_datas['hash'],
                    'idKey': stream_datas['idKey'],
                    'quality': stream_datas['quality']}
                break

        payload = json.dumps(payload)
        headers = {'Accept': 'application/json, text/plain, */*',
                   'Authorization': 'PASS Token="%s"' % pass_token,
                   'Content-Type': 'application/json; charset=UTF-8',
                   'XX-DEVICE': 'pc %s' % device_id,
                   'XX-DOMAIN': 'cpfra',
                   'XX-OPERATOR': 'pc',
                   'XX-Profile-Id': '0',
                   'XX-SERVICE': 'mycanal',
                   'User-Agent': web_utils.get_random_ua(),
                   }

        jsonparser_stream_datas = session_requests.put(
            URL_STREAM_DATAS, data=payload, headers=headers).json()

        jsonparser_real_stream_datas = session_requests.get(
            jsonparser_stream_datas['@medias'], headers=headers).json()

        certificate_data = base64.b64encode(requests.get(
            'https://secure-webtv-static.canal-plus.com/widevine/cert/cert_license_widevine_com.bin').content).decode(
            'utf-8')

        subtitle_url = ''
        item = Listitem()
        stream_data_type = "VM" if 'VM' in jsonparser_real_stream_datas else "VF"

        item.path = jsonparser_real_stream_datas[stream_data_type][0]["media"][0]["distribURL"]
        if plugin.setting.get_boolean('active_subtitle'):
            for asset in jsonparser_real_stream_datas[stream_data_type][0]["files"]:
                if 'vtt' in asset["mimeType"]:
                    subtitle_url = asset['distribURL']

        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'

        if 'http' in subtitle_url:
            item.subtitles.append(subtitle_url)

        if ".mpd" in item.path:
            item.property['inputstream.adaptive.manifest_type'] = 'mpd'
            item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            headers2 = {
                'Accept': 'application/json, text/plain, */*',
                'Authorization': 'PASS Token="%s"' % pass_token,
                'Content-Type': 'text/plain',
                'User-Agent': web_utils.get_random_ua(),
                'Origin': 'https://www.mycanal.fr',
                'XX-DEVICE': 'pc %s' % device_id,
                'XX-DOMAIN': 'cpfra',
                'XX-OPERATOR': 'pc',
                'XX-Profile-Id': '0',
                'XX-SERVICE': 'mycanal',
            }

            with xbmcvfs.File('special://userdata/addon_data/plugin.video.catchuptvandmore/headersCanal', 'wb') as f1:
                pickle.dump(headers2, f1)

            # Return HTTP 200 but the response is not correctly interpreted by inputstream
            # (https://github.com/peak3d/inputstream.adaptive/issues/267)
            licence = "http://127.0.0.1:5057/license=" + jsonparser_stream_datas['@licence']
            licence += '?drmConfig=mkpl::true|%s|b{SSM}|B' % urlencode(headers2)
            item.property['inputstream.adaptive.license_key'] = licence
            item.property['inputstream.adaptive.server_certificate'] = certificate_data
        return item

    json_parser = urlquick.get(next_url, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1).json()
    return json_parser["detail"]["informations"]["playsets"]["available"][0]["videoURL"]


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    if CANALPLUS_links.DAILYMOTION.value == plugin.setting.get_string('canalplusgroup'):
        return resolver_proxy.get_stream_dailymotion(plugin, LIVE_DAILYMOTION[item_id], False)

    deviceKeyId, deviceId, sessionId = getKeyID()

    resp_app_config = requests.get("https://www.canalplus.com/chaines/%s" % item_id)
    EPGID = re.compile('expertMode.+?"epgID":(.+?),').findall(
        resp_app_config.text)[0]

    json_app_config = re.compile('window.app_config=(.*?)};').findall(
        resp_app_config.text)[0]
    json_app_config_parser = json.loads(json_app_config + ('}'))
    portail_id = json_app_config_parser["api"]["pass"]["portailIdEncrypted"]

    data = {
        "deviceId": deviceId,
        "sessionId": sessionId,
        "vect": "INTERNET",
        "media": "PC",
        "portailId": portail_id,
        "zone": "cpfra",
        "noCache": "false",
        "analytics": "false",
        "trackingPub": "false",
        "anonymousTracking": "true"
    }

    hdr = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://www.canalplus.com",
        "Referer": "https://www.canalplus.com/",
        "User-Agent": web_utils.get_random_ua()
    }

    resp = requests.post('https://pass-api-v2.canal-plus.com/services/apipublique/createToken', data=data, headers=hdr).json()
    passToken = resp['response']['passToken']

    data = {
        "ServiceRequest": {
            "InData": {
                "DeviceKeyId": deviceKeyId,
                "PassData": {
                    "Id": 0,
                    "Token": passToken
                },
                "PDSData": {
                    "GroupTypes": "1;2;4"
                },
                "UserKeyId": "_tl1sb683u"
            }
        }
    }

    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
    try:
        requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += 'HIGH:!DH:!aNULL'
    except AttributeError:
        # no pyopenssl support used / needed / available
        pass
    resp = requests.post('https://secure-webtv.canal-plus.com/WebPortal/ottlivetv/api/V4/zones/cpfra/devices/3/apps/1/jobs/InitLiveTV', json=data, headers=hdr).json()
    liveToken = resp['ServiceResponse']['OutData']['LiveToken']

    data_drm = quote('''{
        "ServiceRequest":
        {
            "InData":
            {
                "ChallengeInfo": "b{SSM}",
                "DeviceKeyId": "''' + deviceKeyId + '''",
                "EpgId": ''' + EPGID + ''',
                "LiveToken": "''' + liveToken + '''",
                "Mode": "MKPL",
                "UserKeyId": "_tl1sb683u"
            }
        }
    }''')

    if item_id == "canalplus":
        item_id = "canalplusclair"

    resp = requests.get("https://routemeup.canalplus-bo.net/plfiles/v2/metr/dash-ssl/" + item_id + "-hd.json").json()
    url_stream = resp["primary"]["src"]

    LICENSE_URL = 'https://secure-webtv.canal-plus.com/WebPortal/ottlivetv/api/V4/zones/cpfra/devices/31/apps/1/jobs/GetLicence'

    certificate_data = base64.b64encode(requests.get('https://secure-webtv-static.canal-plus.com/widevine/cert/cert_license_widevine_com.bin').content).decode('utf-8')

    item = Listitem()
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())

    item.path = url_stream
    item.property[INPUTSTREAM_PROP] = "inputstream.adaptive"

    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = LICENSE_URL + '||' + data_drm + '|JBLicenseInfo'
    item.property['inputstream.adaptive.server_certificate'] = certificate_data
    return item
