# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import time
from builtins import str
from datetime import datetime

# noinspection PyUnresolvedReferences
import urlquick
# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, utils, Script
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui, xbmcplugin

from resources.lib import resolver_proxy, web_utils
from resources.lib.addon_utils import get_item_media_path
from resources.lib.menu_utils import item_post_treatment

MYTF1_ROOT = "https://www.tf1.fr"

API_KEY = "3_hWgJdARhz_7l1oOp3a8BDLoR9cuWZpUaKG4aqF7gum9_iK3uTZ2VlDBl8ANf8FVk"

# uid, signature, timestamp
BODY_GIGYA = "{\"uid\":\"%s\",\"signature\":\"%s\",\"timestamp\":%s,\"consent_ids\":[\"1\",\"2\",\"3\",\"4\",\"10001\",\"10003\",\"10005\",\"10007\",\"10013\",\"10015\",\"10017\",\"10019\",\"10009\",\"10011\",\"13002\",\"13001\",\"10004\",\"10014\",\"10016\",\"10018\",\"10020\",\"10010\",\"10012\",\"10006\",\"10008\"]}"
TOKEN_GIGYA_WEB = "https://www.tf1.fr/token/gigya/web"

# TO DO
# Readd Playlist (if needed)
# Add more infos videos (saison, episodes, casts, etc ...)
# Find a way to get Id for each API call

URL_ROOT = utils.urljoin_partial(MYTF1_ROOT)

URL_VIDEO_STREAM = 'https://mediainfo.tf1.fr/mediainfocombo/%s'

URL_API = 'https://www.tf1.fr/graphql/web'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}

USER_AGENT_FIREFOX = "Mozilla/5.0 (Windows NT 10.0; rv:114.0) Gecko/20100101 Firefox/114.0"

URL_LICENCE_KEY = 'https://drm-wide.tf1.fr/proxy?id=%s'
# videoId


ACCOUNTS_LOGIN = "https://compte.tf1.fr/accounts.login"
ACCOUNTS_BOOTSTRAP = "https://compte.tf1.fr/accounts.webSdkBootstrap"

DESIRED_QUALITY = Script.setting['quality']

VIDEO_TYPES = {
    'Replay': 'REPLAY',
    'Extrait': 'EXTRACT',
    'Exclu': 'BONUS'
}


def get_token(plugin):
    session = urlquick.session()
    bootstrap_headers = {
        "User-Agent": USER_AGENT_FIREFOX,
        "referrer": MYTF1_ROOT
    }
    bootstrap_params = {
        'apiKey': API_KEY,
        'pageURL': 'https%3A%2F%2Fwww.tf1.fr%2F',
        'sd': 'js_latest',
        'sdkBuild': '13987',
        'format': 'json'
    }

    session.get(ACCOUNTS_BOOTSTRAP, headers=bootstrap_headers, params=bootstrap_params, max_age=-1)
    headers_login = {
        "User-Agent": USER_AGENT_FIREFOX,
        "Content-Type": "application/x-www-form-urlencoded",
        "referrer": MYTF1_ROOT
    }

    if plugin.setting.get_string('mytf1.login') == '' or plugin.setting.get_string('mytf1.password') == '':
        xbmcgui.Dialog().ok('Info', plugin.localize(30604) % ('myft1', 'https://www.tf1.fr/mon-compte'))
        return False, None, None

    post_body_login = {
        "loginID": (plugin.setting.get_string('mytf1.login')),
        "password": (plugin.setting.get_string('mytf1.password')),
        "sessionExpiration": 31536000,
        "targetEnv": "jssdk",
        "include": "identities-all,data,profile,preferences,",
        "includeUserInfo": "true",
        "loginMode": "standard",
        "lang": "fr",
        "APIKey": API_KEY,
        "sdk": "js_latest",
        "authMode": "cookie",
        "pageURL": MYTF1_ROOT,
        "sdkBuild": 13987,
        "format": "json"
    }
    response = session.post(ACCOUNTS_LOGIN, headers=headers_login, data=post_body_login, max_age=-1)
    login_json = response.json()
    headers_gigya = {
        "User-Agent": web_utils.get_random_ua(),
        "content-type": "application/json"
    }
    post_body_gigya = BODY_GIGYA % (login_json['userInfo']['UID'],
                                    login_json['userInfo']['UIDSignature'],
                                    int(login_json['userInfo']['signatureTimestamp']))
    response = session.post(TOKEN_GIGYA_WEB, headers=headers_gigya, data=post_body_gigya, max_age=-1)
    json_token = response.json()
    token = json_token['token']
    return True, session, token


@Route.register
def mytf1_root(plugin, **kwargs):
    # (item_id, label, thumb, fanart)
    channels = [
        ('tf1', 'TF1', 'tf1.png', 'tf1_fanart.jpg'),
        ('tmc', 'TMC', 'tmc.png', 'tmc_fanart.jpg'),
        ('tfx', 'TFX', 'tfx.png', 'tfx_fanart.jpg'),
        ('tf1-series-films', 'TF1 Séries Films', 'tf1seriesfilms.png', 'tf1seriesfilms_fanart.jpg')
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/fr/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/fr/' + channel_infos[3])
        item.set_callback(list_categories, channel_infos[0])
        item_post_treatment(item)
        yield item

    # Search feature
    item = Listitem.search(search)
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
    params = {
        'id': '909c68c0',
        'variables': '{}'
    }
    headers = {
        'content-type': 'application/json',
        'referer': 'https://www.tf1.fr/programmes-tv',
        'User-Agent': web_utils.get_random_ua()
    }
    json_parser = urlquick.get(URL_API, params=params, headers=headers, max_age=-1).json()

    for json_key in list(json_parser['data'].keys()):
        category = json_parser['data'][json_key] or {}

        if category.get('label'):
            item = Listitem()
            item.label = category['label']
            item.params['item_id'] = item_id
            item.params['category_id'] = category['id']
            item.set_callback(list_programs)
            item_post_treatment(item)

            yield item


@Route.register
def search(plugin, search_query, **kwargs):
    plugin.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED)
    headers = {
        'content-type': 'application/json',
        'User-Agent': web_utils.get_random_ua()
    }

    # Programs
    params = {
        'id': 'e78b188',
        'variables': '{"query":"%s","offset":0,"limit":500}' % search_query
    }
    json_parser = urlquick.get(URL_API, params=params, headers=headers, max_age=-1).json()
    for program_item in handle_programs(json_parser['data']['searchPrograms']['items']):
        yield program_item

    # Videos
    params = {
        'id': 'b2dc9439',
        'variables': '{"query":"%s","offset":0,"limit":500}' % search_query
    }
    json_parser = urlquick.get(URL_API, params=params, headers=headers, max_age=-1).json()
    for video_item in handle_videos(json_parser['data']['searchVideos']['items']):
        yield video_item


def handle_programs(program_items, category_id=None):
    for program_datas in program_items:
        is_category = False
        for category_datas in program_datas['categories']:
            if category_id is None:
                is_category = True
            elif category_id in category_datas['id']:
                is_category = True
        if is_category:
            program_name = program_datas['name']
            program_slug = program_datas['slug']
            program_image = program_datas['decoration']['image']['sources'][0]['url']
            program_background = program_datas['decoration']['background']['sources'][0]['url']

            item = Listitem()
            item.label = program_name
            item.art['thumb'] = item.art['landscape'] = program_image
            item.art['fanart'] = program_background
            item.set_callback(list_program_categories,
                              program_slug=program_slug)
            item_post_treatment(item)
            yield item


def handle_videos(video_items):
    for video_datas in video_items:
        video_title = video_datas['decoration']['label']
        try:
            video_image = video_datas['decoration']['images'][1]['sources'][0]['url']
        except Exception:
            video_image = ''
        video_plot = video_datas['decoration']['description']
        video_duration = video_datas['playingInfos']['duration']
        video_id = video_datas['id']

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.info.date(video_datas['date'].split('T')[0], '%Y-%m-%d')

        item.set_callback(get_video_url,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item


@Route.register
def list_programs(plugin, item_id, category_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """

    params = {
        'id': '483ce0f',
        'variables': '{"context":{"persona":"PERSONA_2","application":"WEB","device":"DESKTOP","os":"WINDOWS"},"filter":{"channel":"%s"},"offset":0,"limit":500}' % item_id
    }
    headers = {
        'content-type': 'application/json',
        'referer': 'https://www.tf1.fr/programmes-tv',
        'User-Agent': web_utils.get_random_ua()
    }
    json_parser = urlquick.get(URL_API, params=params, headers=headers, max_age=-1).json()
    for program_item in handle_programs(json_parser['data']['programs']['items'], category_id):
        yield program_item


@Route.register
def list_program_categories(plugin, program_slug, **kwargs):
    """
    Build program categories
    - Toutes les vidéos
    - Tous les replay
    - Saison 1
    - ...
    """
    for video_type_title, video_type_value in list(VIDEO_TYPES.items()):
        item = Listitem()
        item.label = video_type_title
        item.set_callback(list_videos,
                          program_slug=program_slug,
                          video_type_value=video_type_value,
                          offset='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, program_slug, video_type_value, offset, **kwargs):
    plugin.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED)
    params = {
        'id': 'a6f9cf0e',
        'variables': '{"programSlug":"%s","offset":%d,"limit":20,'
                     '"sort":{"type":"DATE","order":"DESC"},"types":["%s"]}' % (
                         program_slug, int(offset), video_type_value)
    }
    headers = {
        'content-type': 'application/json',
        'referer': 'https://www.tf1.fr/programmes-tv',
        'User-Agent': web_utils.get_random_ua()
    }
    json_parser = urlquick.get(URL_API, params=params, headers=headers, max_age=-1).json()

    video_items = json_parser['data']['programBySlug']['videos']['items']

    for video_item in handle_videos(video_items):
        yield video_item

    if len(video_items) == 20:
        yield Listitem.next_page(program_slug=program_slug,
                                 video_type_value=video_type_value,
                                 offset=str(int(offset) + 1))


@Resolver.register
def get_video_url(plugin,
                  video_id,
                  download_mode=False,
                  **kwargs):
    is_ok, session, token = get_token(plugin)
    if not is_ok:
        return False

    headers_video_stream = {
        "User-Agent": USER_AGENT_FIREFOX,
        "authorization": "Bearer %s" % token,
    }
    params = {
        'context': 'MYTF1',
        'pver': '5010000',
        'platform': 'web',
        'device': 'desktop',
        'os': 'windows',
        'osVersion': '10.0',
        'topDomain': 'unknown',
        'playerVersion': '5.10.0',
        'productName': 'mytf1',
        'productVersion': '2.59.1'
    }

    url_json = URL_VIDEO_STREAM % video_id
    json_parser = session.get(url_json, headers=headers_video_stream, params=params, max_age=-1).json()

    if json_parser['delivery']['code'] >= 400:
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    if download_mode:
        xbmcgui.Dialog().ok('Info', plugin.localize(30603))
        return False

    video_url = json_parser['delivery']['url']
    try:
        license_url = json_parser['delivery']['drm-server']
    except Exception:
        license_url = URL_LICENCE_KEY % video_id

    license_headers = {
        'Content-Type': '',
        'User-Agent': web_utils.get_random_ua()
    }

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="mpd",
                                                  license_url=license_url, headers=license_headers)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    video_id = 'L_%s' % item_id.upper()

    is_ok, session, token = get_token(plugin)
    if not is_ok:
        return False

    headers_video_stream = {
        "User-Agent": USER_AGENT_FIREFOX,
        "authorization": "Bearer %s" % token,
    }
    params = {
        'context': 'MYTF1',
        'pver': '5010000',
        'platform': 'web',
        'device': 'desktop',
        'os': 'windows',
        'osVersion': '10.0',
        'topDomain': 'unknown',
        'playerVersion': '5.10.0',
        'productName': 'mytf1',
        'productVersion': '2.59.1'
    }

    url_json = URL_VIDEO_STREAM % video_id
    json_parser = session.get(url_json, headers=headers_video_stream, params=params, max_age=-1).json()

    if json_parser['delivery']['code'] > 400:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    video_url = json_parser['delivery']['url']
    license_headers = {
        'Content-Type': '',
        'User-Agent': web_utils.get_random_ua()
    }

    if 'drms' in json_parser['delivery']:
        license_url = json_parser['delivery']['drms'][0]['url']
        license_headers.update({'Authorization': json_parser['delivery']['drms'][0]['h'][0]['v']})
    else:
        license_url = URL_LICENCE_KEY % video_id

    if video_id == 'L_TF1-SERIES-FILMS':
        workaround = None
    else:
        workaround = '1'

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url,
                                                  manifest_type="mpd", license_url=license_url,
                                                  workaround=workaround, headers=license_headers)
