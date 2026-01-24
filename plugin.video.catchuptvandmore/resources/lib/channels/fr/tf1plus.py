# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import time
from builtins import str
from datetime import datetime

import json

# noinspection PyUnresolvedReferences
import urlquick
# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, utils, Script
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui, xbmcplugin

from resources.lib import resolver_proxy, web_utils
from resources.lib.addon_utils import get_item_media_path
from resources.lib.menu_utils import item_post_treatment

TF1PLUS_ROOT = "https://www.tf1.fr"

API_KEY = "3_hWgJdARhz_7l1oOp3a8BDLoR9cuWZpUaKG4aqF7gum9_iK3uTZ2VlDBl8ANf8FVk"

# uid, signature, timestamp
BODY_GIGYA = "{\"uid\":\"%s\",\"signature\":\"%s\",\"timestamp\":%s,\"consent_ids\":[\"1\",\"2\",\"3\",\"4\",\"10001\",\"10003\",\"10005\",\"10007\",\"10013\",\"10015\",\"10017\",\"10019\",\"10009\",\"10011\",\"13002\",\"13001\",\"10004\",\"10014\",\"10016\",\"10018\",\"10020\",\"10010\",\"10012\",\"10006\",\"10008\"]}"
TOKEN_GIGYA_WEB = "https://www.tf1.fr/token/gigya/web"

# TO DO
# Readd Playlist (if needed)
# Add more infos videos (saison, episodes, casts, etc ...)
# Find a way to get Id for each API call

URL_ROOT = utils.urljoin_partial(TF1PLUS_ROOT)
URL_VIDEO_STREAM = 'https://mediainfo.tf1.fr/mediainfocombo/%s'
URL_API = 'https://www.tf1.fr/graphql/web'
URL_SMARTTV = 'https://smart-tv.tf1.fr/catalog/fr-fr/smarttv'
URL_LICENCE_KEY = 'https://drm-wide.tf1.fr/proxy?id=%s'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_windows_ua()}

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
        "User-Agent": web_utils.get_random_windows_ua(),
        "referrer": TF1PLUS_ROOT
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
        "User-Agent": web_utils.get_random_windows_ua(),
        "Content-Type": "application/x-www-form-urlencoded",
        "referrer": TF1PLUS_ROOT
    }

    if plugin.setting.get_string('tf1plus.login') == '' or plugin.setting.get_string('tf1plus.password') == '':
        xbmcgui.Dialog().ok('Info', plugin.localize(30604) % ('TF1+', 'https://www.tf1.fr/mon-compte'))
        return False, None, None

    post_body_login = {
        "loginID": (plugin.setting.get_string('tf1plus.login')),
        "password": (plugin.setting.get_string('tf1plus.password')),
        "sessionExpiration": 31536000,
        "targetEnv": "jssdk",
        "include": "identities-all,data,profile,preferences,",
        "includeUserInfo": "true",
        "loginMode": "standard",
        "lang": "fr",
        "APIKey": API_KEY,
        "sdk": "js_latest",
        "authMode": "cookie",
        "pageURL": TF1PLUS_ROOT,
        "sdkBuild": 13987,
        "format": "json"
    }
    response = session.post(ACCOUNTS_LOGIN, headers=headers_login, data=post_body_login, max_age=-1)
    login_json = response.json()
    headers_gigya = {
        "User-Agent": web_utils.get_random_windows_ua(),
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
def tf1plus_root(plugin, **kwargs):
    # (item_id, label, thumb, fanart)
    channels = [
        ('tf1', 'TF1', 'tf1.png', 'tf1_fanart.jpg'),
        ('tmc', 'TMC', 'tmc.png', 'tmc_fanart.jpg'),
        ('tfx', 'TFX', 'tfx.png', 'tfx_fanart.jpg'),
        ('tf1-series-films', 'TF1 Séries Films', 'tf1seriesfilms.png', 'tf1seriesfilms_fanart.jpg'),
        ('lci', 'LCI', 'lci.png', 'lci_fanart.jpg'),
        ('all', 'ALL', 'mytf1.png', 'mytf1_fanart.png')
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
        'User-Agent': web_utils.get_random_windows_ua()
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
        'User-Agent': web_utils.get_random_windows_ua()
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
    is_item = False
    for program_datas in program_items:
        is_category = False
        for category_datas in program_datas['categories']:
            if category_id is None:
                is_category = True
            elif category_id in category_datas['id']:
                is_category = True
        if is_category:
            is_item = True
            program_name = program_datas['name']
            program_slug = program_datas['slug']
            program_id = program_datas['id']
            program_image = program_datas['decoration']['image']['sources'][0]['url']
            program_background = program_datas['decoration']['background']['sources'][0]['url']

            item = Listitem()
            item.label = program_name
            item.art['thumb'] = item.art['landscape'] = program_image
            item.art['fanart'] = program_background
            item.set_callback(list_program_categories,
                              program_slug=program_slug,
                              program_id=program_id)
            item_post_treatment(item)
            yield item

    if not is_category and not is_item:
        item = Listitem()
        item.label = Script.localize(30896)
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
    headers = {
        'content-type': 'application/json',
        'referer': 'https://www.tf1.fr/programmes-tv',
        'User-Agent': web_utils.get_random_windows_ua()
    }

    base_variables = {
        "context": {
            "persona": "PERSONA_2",
            "application": "WEB",
            "device": "DESKTOP",
            "os": "WINDOWS"
        },
        "filter": {
            "channel": ''
        },
        "offset": 0,
        "limit": 500
    }

    all_items = []
    max_pages = 10 if item_id == 'all' else 1

    for i in range(max_pages):
        offset = i if item_id == 'all' else 0
        variables = base_variables.copy()
        variables["filter"] = variables["filter"].copy()
        variables["filter"]["channel"] = item_id if item_id != 'all' else ''
        variables["offset"] = offset

        params = {
            'id': '483ce0f',
            "variables": json.dumps(variables)
        }

        json_parser = urlquick.get(URL_API, params=params, headers=headers, max_age=-1).json()
        items = json_parser['data']['programs']['items']

        if not items:
            break

        all_items.extend(items)

        if len(items) < 500:
            break

    for program_item in handle_programs(all_items, category_id):
        yield program_item


@Route.register
def list_program_categories(plugin, program_slug, program_id, **kwargs):
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
                          program_id=program_id,
                          video_type_value=video_type_value,
                          offset='0')
        item_post_treatment(item)
        yield item


def list_seasons(program_slug, program_id):
    headers = {
        'content-type': 'application/json',
        'referer': 'https://www.tf1.fr/programmes-tv',
        'User-Agent': web_utils.get_random_windows_ua()
    }
    params = {
        'id': '379fec96081ab1a2',
        'variables': '{"programId":"%s"}' % program_id
    }
    # Check valid url and id
    response = urlquick.get(URL_SMARTTV, params=params, headers=headers, max_age=-1, raise_for_status=False)
    if response.status_code != 200:
        return
    json_parser = response.json()
    checked_ep = False
    for data in json_parser['data']['programById']['editorialSections']:
        if data.get('lists'):
            program_desc = json_parser['data']['programById']['decoration']['description']
            program_image = json_parser['data']['programById']['decoration']['image']['sourcesWithScales'][0]['url']
            for array in data['lists']:
                lists_id = array.get('id')
                lists_total = array.get('total')
                lists_label = array.get('decoration').get('label')

                # Check valid url and id. Only first pass
                if not checked_ep:
                    checked_ep = True
                    params_ep = {
                        'id': '76bc5c35edb166fa637a6c6686cb05c7140d2a8b',
                        'variables': '{"programSlug":"%s","listId":"%s","offset":0,"limit":%s}' % (program_slug, lists_id, lists_total)
                    }
                    response_ep = urlquick.get(URL_API, params=params_ep, headers=headers, max_age=-1, raise_for_status=False)
                    if response_ep.status_code != 200:
                        return

                item = Listitem()
                item.label = lists_label
                item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = program_image
                item.info['plot'] = program_desc
                item.set_callback(list_episodes,
                                  program_slug=program_slug,
                                  lists_id=lists_id,
                                  lists_total=lists_total)
                item_post_treatment(item)
                yield item
            break


@Route.register
def list_episodes(plugin, program_slug, lists_id, lists_total, **kwargs):
    headers = {
        'content-type': 'application/json',
        'referer': 'https://www.tf1.fr/programmes-tv',
        'User-Agent': web_utils.get_random_windows_ua()
    }
    params = {
        'id': '76bc5c35edb166fa637a6c6686cb05c7140d2a8b',
        'variables': '{"programSlug":"%s","listId":"%s","offset":0,"limit":%s}' % (program_slug, lists_id, lists_total)
    }
    json_parser = urlquick.get(URL_API, params=params, headers=headers, max_age=-1).json()

    for data in json_parser['data']['programBySlug']['editorialSections']:
        for video_datas in data['listById']['items']:
            video_title = video_datas['video']['decoration']['label']
            try:
                video_image = video_datas['image']['sourcesWithScales'][0]['url']
            except Exception:
                video_image = ''
            video_plot = video_datas['video']['decoration']['summary']
            video_duration = video_datas['video']['playingInfos']['duration']
            video_id = video_datas['video']['id']

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = video_image
            item.info['plot'] = video_plot
            item.info['duration'] = video_duration
            # item.info.date(video_datas['date'].split('T')[0], '%Y-%m-%d')
            item.set_callback(get_video_url,
                              video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=False)
            yield item


@Route.register
def list_videos(plugin, program_slug, program_id, video_type_value, offset, **kwargs):
    is_seasons = False
    if video_type_value == 'REPLAY':
        for video_item in list_seasons(program_slug=program_slug, program_id=program_id):
            is_seasons = True
            yield video_item

    if is_seasons:
        return

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
        'User-Agent': web_utils.get_random_windows_ua()
    }
    json_parser = urlquick.get(URL_API, params=params, headers=headers, max_age=-1).json()

    video_items = json_parser['data']['programBySlug']['videos']['items']

    if len(video_items) > 0:
        for video_item in handle_videos(video_items):
            yield video_item
    else:
        item = Listitem()
        item.label = Script.localize(30896)
        yield item

    if len(video_items) == 20:
        yield Listitem.next_page(program_slug=program_slug,
                                 program_id=program_id,
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
        "User-Agent": web_utils.get_random_windows_ua(),
        "authorization": "Bearer %s" % token,
    }
    params = {
        'context': 'MYTF1',
        'pver': '5010000',
        'platform': 'web',
        'device': 'desktop',
        'os': 'linux',
        'osVersion': 'unknown',
        'topDomain': TF1PLUS_ROOT,
        'playerVersion': '5.19.0',
        'productName': 'mytf1',
        'productVersion': '3.22.0'
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
        license_url = json_parser['delivery']['drms'][0]['url']
    except Exception:
        license_url = URL_LICENCE_KEY % video_id

    license_headers = {
        'Content-Type': '',
        'User-Agent': web_utils.get_random_windows_ua()
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
        "User-Agent": web_utils.get_random_windows_ua(),
        "authorization": "Bearer %s" % token,
    }
    params = {
        'context': 'MYTF1',
        'pver': '5029000',
        'platform': 'web',
        'device': 'desktop',
        'os': 'windows',
        'osVersion': '10.0',
        'topDomain': 'unknown',
        'playerVersion': '5.29.0',
        'productName': 'mytf1',
        'productVersion': '3.37.0'
    }

    url_json = URL_VIDEO_STREAM % video_id
    json_parser = session.get(url_json, headers=headers_video_stream, params=params, max_age=-1).json()

    if json_parser['delivery']['code'] > 400:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    video_url = json_parser['delivery']['url']
    license_headers = {
        'Content-Type': '',
        'User-Agent': web_utils.get_random_windows_ua()
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
                                                  workaround=workaround, headers=headers_video_stream,
                                                  custom_license_headers=license_headers)
