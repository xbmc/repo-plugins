# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re
import uuid

from builtins import str

import inputstreamhelper
import urlquick

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui

from resources.lib import download, resolver_proxy, web_utils
from resources.lib.kodi_utils import get_kodi_version
from resources.lib.addon_utils import get_item_media_path, Quality

from resources.lib.menu_utils import item_post_treatment

# TO DO
# Playlists (cas les blagues de TOTO)
# Some DRM (m3u8) not working old videos (Kamelot)

# Thank you (https://github.com/peak3d/plugin.video.simple)

# Url to get channel's categories
# e.g. Info, Divertissement, Séries, ...
# We get an id by category
URL_ROOT = 'https://android.middleware.6play.fr/6play/v2/platforms/' \
           'm6group_androidmob/services/%s/folders?limit=999&offset=0'

URL_ALL_PROGRAMS = 'https://android.middleware.6play.fr/6play/v2/platforms/' \
                   'm6group_androidmob/services/6play/programs'

# Url to get catgory's programs
# e.g. Le meilleur patissier, La france à un incroyable talent, ...
# We get an id by program
URL_CATEGORY = 'https://android.middleware.6play.fr/6play/v2/platforms/' \
               'm6group_androidmob/services/6play/folders/%s/programs' \
               '?limit=999&offset=0&csa=6&with=parentcontext'

# Url to get program's subfolders
# e.g. Saison 5, Les meilleurs moments, les recettes pas à pas, ...
# We get an id by subfolder
URL_SUBCATEGORY = 'https://android.middleware.6play.fr/6play/v2/platforms/' \
                  'm6group_androidmob/services/6play/programs/%s' \
                  '?with=links,subcats,rights'

# Url to get shows list
# e.g. Episode 1, Episode 2, ...
URL_VIDEOS = 'https://android.middleware.6play.fr/6play/v2/platforms/' \
             'm6group_androidmob/services/6play/programs/%s/videos?' \
             'csa=6&with=clips,freemiumpacks&type=vi,vc,playlist&limit=999' \
             '&offset=0&subcat=%s&sort=subcat'

URL_VIDEOS2 = 'https://android.middleware.6play.fr/6play/v2/platforms/' \
              'm6group_androidmob/services/6play/programs/%s/videos?' \
              'csa=6&with=clips,freemiumpacks&type=vi&limit=999&offset=0'

URL_JSON_VIDEO = 'https://android.middleware.6play.fr/6play/v2/platforms/' \
                 'm6group_androidmob/services/6play/videos/%s' \
                 '?csa=6&with=clips,freemiumpacks'

URL_IMG = 'https://images.6play.fr/v1/images/%s/raw'

URL_COMPTE_LOGIN = 'https://login-gigya.m6.fr/accounts.login'
# https://login.6play.fr/accounts.login?loginID=*****&password=*******&targetEnv=mobile&format=jsonp&apiKey=3_hH5KBv25qZTd_sURpixbQW6a4OsiIzIEF2Ei_2H7TXTGLJb_1Hr4THKZianCQhWK&callback=jsonp_3bbusffr388pem4
# TODO get value Callback
# callback: jsonp_3bbusffr388pem4

URL_GET_JS_ID_API_KEY = 'https://www.6play.fr/connexion'

# Id
URL_API_KEY = 'https://www.6play.fr/main-%s.bundle.js'

PATTERN_API_KEY = re.compile(r'\"eu1.gigya.com\",key:\"(.*?)\"')
PATTERN_JS_ID = re.compile(r'main-(.*?)\.bundle\.js')

API_KEY = "3_hH5KBv25qZTd_sURpixbQW6a4OsiIzIEF2Ei_2H7TXTGLJb_1Hr4THKZianCQhWK"

URL_TOKEN_REPLAY = 'https://drm.6cloud.fr/v1/customers/m6web/platforms/m6group_web/services/m6replay/users/%s/videos/%s/upfront-token'
URL_TOKEN_LIVE = 'https://drm.6cloud.fr/v1/customers/m6web/platforms/m6group_web/services/6play/users/%s/live/%s/upfront-token'
URL_TOKEN_UUID = 'https://front-auth.6cloud.fr/v2/platforms/m6group_web/getJwt'
DEVICEID = '_luid_' + str(uuid.UUID(int=uuid.getnode()))

# URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&Origin=https://www.6play.fr&Referer=%s&x-dt-auth-token=%s|R{SSM}|JBlicense'
URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&x-dt-auth-token=%s|R{SSM}|JBlicense'
# Referer, Token

URL_LIVE_JSON = 'https://android.middleware.6play.fr/6play/v2/platforms/m6group_androidmob/services/6play/live'

# Search
URL_SEARCH = 'https://nhacvivxxk-dsn.algolia.net/1/indexes/*/queries'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_windows_ua()}
M6_HEADERS = {
    'User-Agent': web_utils.get_random_windows_ua(),
    'x-customer-name': 'm6web'
}


def get_api_key():
    resp_js_id = urlquick.get(URL_GET_JS_ID_API_KEY, headers=GENERIC_HEADERS, max_age=-1)
    found_js_id = PATTERN_JS_ID.findall(resp_js_id.text)
    if len(found_js_id) == 0:
        return API_KEY
    js_id = found_js_id[0]
    resp = urlquick.get(URL_API_KEY % js_id, headers=GENERIC_HEADERS, max_age=-1)
    # Hack to force encoding of the response
    resp.encoding = 'utf-8'
    found_items = PATTERN_API_KEY.findall(resp.text)
    if len(found_items) == 0:
        return API_KEY
    return found_items[0]


@Resolver.register
def get_login_token(plugin, **kwargs):
    api_key = get_api_key()

    if plugin.setting.get_string('6play.login') == '' or \
            plugin.setting.get_string('6play.password') == '':
        xbmcgui.Dialog().ok(
            'Info',
            plugin.localize(30604) % ('6play', 'https://www.6play.fr'))
        return False

    # Build PAYLOAD
    payload = {
        "loginID": plugin.setting.get_string('6play.login'),
        "password": plugin.setting.get_string('6play.password'),
        "apiKey": api_key,
        "format": "jsonp",
        "callback": "jsonp_3bbusffr388pem4"
    }
    # LOGIN
    headers = {
        'User-Agent': web_utils.get_random_windows_ua(),
        'referer': 'https://www.6play.fr/connexion'
    }
    resp = urlquick.post(URL_COMPTE_LOGIN, data=payload, headers=headers, max_age=-1)
    json_parser = json.loads(resp.text.replace('jsonp_3bbusffr388pem4(', '').replace(');', ''))

    if "UID" not in json_parser:
        plugin.notify('ERROR', '6play : ' + plugin.localize(30711))
        return False
    account_id = json_parser["UID"]
    account_timestamp = json_parser["signatureTimestamp"]
    account_signature = json_parser["UIDSignature"]

    # Build PAYLOAD headers
    uuid_headers = {
        'x-auth-gigya-signature': account_signature,
        'x-auth-gigya-signature-timestamp': account_timestamp,
        'x-auth-gigya-uid': account_id,
        'x-auth-device-id': DEVICEID,
        'x-customer-name': 'm6web'
    }
    uuid_json = urlquick.get(URL_TOKEN_UUID, headers=uuid_headers, max_age=-1)
    uuid_jsonparser = json.loads(uuid_json.text)
    login_token = uuid_jsonparser["token"]
    return account_id, login_token


@Route.register
def sixplay_root(plugin, **kwargs):
    # (item_id, label, thumb, fanart)
    channels = [
        ('m6', 'M6', 'm6.png', 'm6_fanart.jpg'),
        ('w9', 'W9', 'w9.png', 'w9_fanart.jpg'),
        ('6ter', '6ter', '6ter.png', '6ter_fanart.jpg'),
        ('gulli', 'Gulli', 'gulli.png', 'gulli_fanart.jpg'),
        ('categories', 'Catégories', 'm6.png', 'm6_fanart.jpg'),
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/fr/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/fr/' + channel_infos[3])
        item.set_callback(list_categories, channel_infos[0])
        item_post_treatment(item)
        yield item

    # all programs
    item = Listitem()
    item.label = plugin.localize(30717)
    item.art["thumb"] = get_item_media_path('channels/fr/m6.png')
    item.art["fanart"] = get_item_media_path('channels/fr/m6_fanart.jpg')
    item.set_callback(list_all_programs, 'm6')
    item_post_treatment(item)
    yield item

    # Search feature
    item = Listitem.search(search)
    item_post_treatment(item)
    yield item


@Route.register
def search(plugin, search_query, **kwargs):
    if search_query is None or len(search_query) == 0:
        return False

    params = {
        'x-algolia-agent': 'Algolia for JavaScript (4.24.0); Browser',
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'x-algolia-api-key': '6ef59fc6d78ac129339ab9c35edd41fa',
        'x-algolia-application-id': 'NHACVIVXXK',
    }
    json_data = {
        'requests': [
            {
                'indexName': 'rtlmutu_prod_bedrock_layout_items_v2_m6web_main',
                'query': '%s' % search_query,
                'params': 'clickAnalytics=true&hitsPerPage=50&facetFilters=[["metadata.item_type:program"], ["metadata.platforms_assets:m6group_web"]]',
            }
        ]
    }
    resp = urlquick.post(URL_SEARCH, headers=headers, params=params, json=json_data, max_age=-1)
    json_parser = resp.json()

    at_least_one_item = False
    for data in json_parser['results']:
        if len(data.get('hits')) > 0:
            at_least_one_item = True
            for array in data['hits']:
                program_id = str(array['content']['id'])
                program_title = array['item']['itemContent']['title']

                item = Listitem()
                item.label = program_title
                item.set_callback(list_program_categories,
                                  item_id='categories',
                                  program_id=program_id)
                item_post_treatment(item)
                yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Route.register
def list_all_programs(plugin, item_id, **kwargs):
    letters = ['@', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
               'u', 'v', 'w', 'y', 'z']

    for letter in letters:
        item = Listitem()
        item.label = plugin.localize(30717) + ' : ' + letter
        item.art["thumb"] = get_item_media_path('channels/fr/m6.png')
        item.art["fanart"] = get_item_media_path('channels/fr/m6_fanart.jpg')
        item.set_callback(list_all_programs_by_letter, item_id, letter)
        item_post_treatment(item)
        yield item


@Route.register
def list_all_programs_by_letter(plugin, item_id, letter, **kwargs):

    params = {
        'limit': '999',
        'offset': '0',
        'csa': '6',
        'firstLetter': letter,
        'with': 'rights'
    }

    resp = urlquick.get(URL_ALL_PROGRAMS, headers=M6_HEADERS, params=params, max_age=-1)
    json_parser = resp.json()

    at_least_one_item = False
    for array in json_parser:
        at_least_one_item = True
        item = Listitem()
        program_id = str(array['id'])
        item.label = array['title']
        populate_item(item, array)
        item.set_callback(list_program_categories,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item)
        yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    if item_id == 'categories':
        account_id, login_token = get_login_token(plugin)
        headers = {
            'authorization': 'Bearer ' + login_token,
            'user-agent': web_utils.get_random_windows_ua(),
            'x-customer-name': 'm6web',
            'x-client-release': '5.43.7',
            'request-timeout': '20000',
        }
        params = {
            'nbPages': '2',
        }
        resp = urlquick.get(
            'https://layout.6cloud.fr/front/v1/m6web/m6group_web/main/token-web-4/navigation/desktop',
            params=params,
            headers=headers,
            max_age=-1
        )
        json_parser = resp.json()
        if len(json_parser) > 0:
            for array in json_parser[0]["entries"]:
                array_id = array['id']
                if array_id == 'categories':
                    for categories in array["groups"][0]["entries"]:
                        category_name = categories["image"]["caption"]
                        category_id = categories["target"]["value_layout"]["id"]
                        item = Listitem()
                        item.label = category_name
                        item.set_callback(list_programs,
                                          item_id=item_id,
                                          category_id=category_id)
                        item_post_treatment(item)
                        yield item
                    break
        else:
            # No items found
            item = Listitem()
            item.label = Script.localize(30896)
            yield item
    else:
        if item_id == 'gulli':
            resp = urlquick.get(URL_ROOT % item_id, headers=GENERIC_HEADERS, max_age=-1)
        else:
            resp = urlquick.get(URL_ROOT % (item_id + 'replay'), headers=GENERIC_HEADERS, max_age=-1)
        json_parser = resp.json()
        if len(json_parser) > 0:
            for array in json_parser:
                category_id = str(array['id'])
                category_name = array['name']
                item = Listitem()
                item.label = category_name
                item.set_callback(list_programs,
                                  item_id=item_id,
                                  category_id=category_id)
                item_post_treatment(item)
                yield item
        else:
            # No items found
            item = Listitem()
            item.label = Script.localize(30896)
            yield item


@Route.register
def list_programs(plugin, item_id, category_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_CATEGORY % category_id, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = resp.json()

    for array in json_parser:
        item = Listitem()
        program_id = str(array['id'])
        item.label = array['title']
        populate_item(item, array)
        item.set_callback(list_program_categories,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_program_categories(plugin, item_id, program_id, **kwargs):
    """
    Build program categories
    - Toutes les vidéos
    - Tous les replay
    - Saison 1
    - ...
    """
    resp = urlquick.get(URL_SUBCATEGORY % program_id, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = resp.json()

    for sub_category in json_parser['program_subcats']:
        item = Listitem()
        sub_category_id = str(sub_category['id'])
        sub_category_title = sub_category['title']

        item.label = sub_category_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_id=program_id,
                          sub_category_id=sub_category_id)
        item_post_treatment(item)
        yield item

    item = Listitem()
    item.label = plugin.localize(30701)
    item.set_callback(list_videos,
                      item_id=item_id,
                      program_id=program_id,
                      sub_category_id=None)
    item_post_treatment(item)
    yield item


def populate_item(item, clip_dict):
    duration = clip_dict.get('duration', None)
    if duration is not None:
        item.info['duration'] = duration

    item.info['plot'] = clip_dict.get('description', None)

    try:
        aired = clip_dict['product']['last_diffusion']
        aired = aired
        aired = aired[:10]
        item.info.date(aired, '%Y-%m-%d')
    except Exception:
        pass

    program_imgs = clip_dict['images']
    for img in program_imgs:
        if img['role'] == 'vignette' or img['role'] == 'carousel':
            external_key = img['external_key']
            program_img = URL_IMG % external_key
            item.art['thumb'] = item.art['landscape'] = program_img
            item.art['fanart'] = program_img
            break


@Route.register
def list_videos(plugin, item_id, program_id, sub_category_id, **kwargs):
    if sub_category_id is None:
        url = URL_VIDEOS2 % program_id
    else:
        url = URL_VIDEOS % (program_id, sub_category_id)

    resp = urlquick.get(url, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = resp.json()

    if not json_parser:
        plugin.notify(plugin.localize(30718), '')
        yield False

    at_least_one_item = False
    for video in json_parser:
        video_id = str(video['id'])

        item = Listitem()
        at_least_one_item = True
        item.label = video['title']

        is_downloadable = False
        if get_kodi_version() < 18:
            is_downloadable = True

        if 'type' in video and video['type'] == 'playlist':
            populate_item(item, video)
            item.set_callback(get_playlist_urls, item_id=item_id, video_id=video_id, url=url)
        else:
            populate_item(item, video['clips'][0])
            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)

        item_post_treatment(item, is_playable=True, is_downloadable=is_downloadable)
        yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Resolver.register
def get_video_url(plugin, item_id, video_id, download_mode=False, **kwargs):
    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    account_id, login_token = get_login_token(plugin)
    payload_headers = {
        'X-Customer-Name': 'm6web',
        'X-Client-Release': '5.103.3',
        'Authorization': 'Bearer ' + login_token,
    }
    token_json = urlquick.get(URL_TOKEN_REPLAY % (account_id, video_id),
                              headers=payload_headers,
                              max_age=-1)

    token_jsonparser = json.loads(token_json.text)
    token = token_jsonparser["token"]

    video_json = urlquick.get(URL_JSON_VIDEO % video_id, headers=M6_HEADERS, max_age=-1)
    json_parser = json.loads(video_json.text)

    video_assets = json_parser['clips'][0]['assets']

    if video_assets is None:
        plugin.notify('ERROR', plugin.localize(30721))
        return False

    subtitle_url = None
    if plugin.setting.get_boolean('active_subtitle'):
        for asset in video_assets:
            if 'subtitle_vtt' in asset["type"]:
                subtitle_url = asset['full_physical_path']

    final_video_url = get_final_video_url(plugin, video_assets, 'usp_dashcenc_h264')
    if final_video_url is not None:
        return resolver_proxy.get_stream_with_quality(
            plugin, video_url=final_video_url, manifest_type='mpd',
            subtitles=subtitle_url, license_url=URL_LICENCE_KEY % token)

    return False


def get_final_video_url(plugin, video_assets, asset_type=None):
    RES_PRIORITY = {"sd": 0, "hd": 1}
    manifests = []

    if video_assets is None:
        plugin.notify('ERROR', plugin.localize(30721))
        return None

    for asset in video_assets:
        if asset_type is None:
            if 'http_h264' in asset["type"]:
                manifest = (asset["video_quality"].lower(), asset["full_physical_path"])
                if manifest not in manifests:
                    manifests.append(manifest)
                continue
        elif asset["type"] == asset_type:
            manifest = (asset["video_quality"].lower(), asset["full_physical_path"])
            if manifest not in manifests:
                manifests.append(manifest)

    final_video_url = sorted(manifests, key=lambda m: RES_PRIORITY[m[0]], reverse=True)[0][1]

    if len(final_video_url) == 0:
        return None

    if 'usp_dashcenc_h264' in asset["type"]:
        dummy_req = urlquick.get(final_video_url, headers=GENERIC_HEADERS, allow_redirects=False, max_age=-1)
        if 'location' in dummy_req.headers:
            final_video_url = dummy_req.headers['location']

    return final_video_url


@Resolver.register
def get_playlist_urls(plugin, item_id, video_id, url, **kwargs):
    resp = urlquick.get(url, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = resp.json()

    for video in json_parser:
        current_video_id = str(video['id'])

        if current_video_id != video_id:
            continue

        for clip in video['clips']:
            clip_id = str(clip['video_id'])
            item = Listitem()
            item.label = clip['title']
            populate_item(item, clip)
            video = get_video_url(plugin, item_id=item_id, video_id=clip_id)
            yield video


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    account_id, login_token = get_login_token(plugin)

    payload_headers = {
        'X-Customer-Name': 'm6web',
        'X-Client-Release': '5.103.3',
        'Authorization': 'Bearer ' + login_token,
    }
    live_item_id = item_id.upper()
    if item_id == '6ter':
        live_item_id = '6T'
    elif item_id in {'fun_radio', 'rtl2', 'gulli'}:
        live_item_id = item_id

    url_token = URL_TOKEN_LIVE % (account_id, 'dashcenc_%s' % live_item_id)
    token_json = urlquick.get(url_token, headers=payload_headers, max_age=-1)
    token_jsonparser = json.loads(token_json.text)
    token = token_jsonparser["token"]

    params = {
        'channel': live_item_id,
        'with': 'service_display_images,nextdiffusion,extra_data'
    }
    video_json = urlquick.get(URL_LIVE_JSON, params=params, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(video_json.text)
    video_assets = json_parser[live_item_id][0]['live']['assets']

    if not video_assets:
        plugin.notify('INFO', plugin.localize(30716))
        return False

    subtitle_url = None
    if plugin.setting.get_boolean('active_subtitle'):
        for asset in video_assets:
            if 'subtitle_vtt' in asset["type"]:
                subtitle_url = asset['full_physical_path']

    final_video_url = get_final_video_url(plugin, video_assets, 'delta_dashcenc_h264')
    if final_video_url is not None:
        return resolver_proxy.get_stream_with_quality(
            plugin, video_url=final_video_url, manifest_type='mpd',
            subtitles=subtitle_url, license_url=URL_LICENCE_KEY % token)

    return False
