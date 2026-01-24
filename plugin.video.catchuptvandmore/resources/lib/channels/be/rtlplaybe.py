# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# Copyright: (c) 2023, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import base64
import json
import random
import re
import sys
from builtins import str
import requests
from datetime import datetime, timezone

# noinspection PyUnresolvedReferences
import xbmcvfs
# noinspection PyUnresolvedReferences
import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui

from resources.lib import download, resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

PUBLIC_SITE = 'https://www.rtlplay.be'

# Url to get channel's categories
# e.g. Info, Divertissement, Séries, ...
# We get an id by category
BASE_URL = "https://www.rtlplay.be/rtlplay"
URL_LFVP_API = 'https://lfvp-api.dpgmedia.net'
URL_CONFIG = 'https://videoplayer-service.dpgmedia.net/play-config/%s'
URL_SSO_LOGIN = 'https://sso.rtl.be/api/account/login'
URL_SSO_AUTH = 'https://sso.rtl.be/oidc/account/authenticate'
URL_LICENCE_KEY = ('https://lic.drmtoday.com/license-proxy-widevine/cenc/'
                   '|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64)'
                   ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36'
                   '&Host=lic.drmtoday.com&x-dt-auth-token=%s&x-customer-name=rtlbe|R{SSM}|JBlicense')

POPCORN_SDK = '8'
REQUESTS_TIMEOUT = 8

LIVE_CHANNEL = {
    "rtl_tvi": "tvi",
    "club_rtl": "club",
    "plug_rtl": "plug",
    "rtl_info": "rtl_info",
    "rtl_sport": "rtl_sport",
    "bel_rtl": "bel",
    "contact": "contact",
    "rtl_play": "rtlplay",
    "rtl_district": "RTLdistrict"
}

GENERIC_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
    'Accept': '*/*',
    'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Sec-GPC': '1',
    'Priority': 'u=0, i',
}

RTLPLAY_HEADERS = {
    'User-Agent': 'RTL_PLAY/23.251217 (com.tapptic.rtl.tvi; build:26234; Android 30)',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip',
    'Connection': 'Keep-Alive',
    'Content-Type': 'application/json; charset=UTF-8',
    'lfvp-device-segment': 'TV>Android',
    'x-app-version': '23',
}


@Route.register
def rtlplay_root(plugin, item_id, **kwargs):
    # Category items
    _PARAMS = {
        'temsPerSwimlane': '20',
        'defaultImageOrientation': 'landscape',
        'hideBannerRow': 'true',
    }
    resp = urlquick.get(URL_LFVP_API + '/RTL_PLAY/storefronts/accueil', headers=RTLPLAY_HEADERS, params=_PARAMS, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    for array in json_parser.get('rows'):
        category_id = ''
        category_name = ''
        if array.get('rowType') in ['SWIMLANE_DEFAULT', 'SWIMLANE_PORTRAIT', 'SWIMLANE_LANDSCAPE']:
            category_id = str(array.get('id'))
            category_name = array.get('title').strip()
        if len(category_name) == 0:
            continue

        item = Listitem()
        item.label = category_name
        item.set_callback(list_programs,
                          item_id=item_id,
                          category_id=category_id)
        item_post_treatment(item)
        yield item

    # Search items
    item = Listitem.search(list_videos_search, item_id=item_id, page='0')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos_search(plugin, search_query, item_id, page, **kwargs):
    if search_query is None or len(search_query) == 0:
        return False

    resp = urlquick.get(URL_LFVP_API + '/RTL_PLAY/search?query=' + search_query, headers=RTLPLAY_HEADERS, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    at_least_one_item = False
    for array in json_parser.get('results', []):
        if "exact" == array.get('type'):
            for datas in array.get('teasers'):
                datas_id = datas.get('detailId')
                datas_title = datas.get('title')
                datas_image = datas.get('imageUrl')

                at_least_one_item = True
                item = Listitem()
                item.label = datas_title
                item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = datas_image
                item.set_callback(list_program_categories,
                                  item_id=item_id,
                                  program_id=datas_id)
                item_post_treatment(item)
                yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Route.register
def list_programs(plugin, item_id, category_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_LFVP_API + '/RTL_PLAY/storefronts/accueil/detail/' + category_id, headers=RTLPLAY_HEADERS, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    for array in json_parser.get('row').get('teasers'):
        program_title = array.get('title')
        program_id = array.get('detailId')
        program_image = array.get('imageUrl')
        program_desc = array.get('description')

        item = Listitem()
        item.label = program_title
        item.info['plot'] = program_desc
        item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = program_image
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
    - Tous les replays
    - Saison 1
    - ...
    """
    resp = urlquick.get(URL_LFVP_API + '/RTL_PLAY/detail3/' + program_id, headers=RTLPLAY_HEADERS, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    channel_image = json_parser.get('landscapeTeaserImageUrl')
    channel_id = json_parser.get('id')
    channel_title = json_parser.get('title').get('label')
    channel_desc = json_parser.get('description')
    if not json_parser.get('seasonPicker', []):
        item = Listitem()
        item.label = channel_title
        item.info['plot'] = channel_desc
        item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = channel_image
        item.info['duration'] = json_parser.get('durationSeconds')
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=channel_id)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item
    else:
        for item_season in json_parser.get('seasonPicker').get('indices', []):
            item = Listitem()
            item.label = 'Saison ' + str(item_season)
            item.info['plot'] = channel_desc
            item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = channel_image
            item.set_callback(list_videos,
                              item_id=item_id,
                              program_id=program_id,
                              season_id=item_season)
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, program_id, season_id, **kwargs):
    if season_id is not None:
        params = {'selectedSeasonIndex': season_id, }
    else:
        params = None

    resp = urlquick.get(URL_LFVP_API + '/RTL_PLAY/detail3/' + program_id, headers=RTLPLAY_HEADERS, params=params, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    at_least_one_item = False
    for array in json_parser.get('seasonPicker').get('selected').get('episodes'):
        video_id = array.get('id')
        video_title = array.get('title')
        video_desc = array.get('description')
        video_image = array.get('imageUrl')
        video_duration = array.get('durationSeconds')

        at_least_one_item = True
        item = Listitem()
        item.label = video_title
        item.info['plot'] = video_desc
        item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = video_image
        item.info['duration'] = video_duration
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(30718), '')
        yield False


def is_valid_token():
    with xbmcvfs.File('special://userdata/addon_data/plugin.video.catchuptvandmore/tokenrtlplay', 'r') as f1:
        token_ = f1.read()
        f1.close()

    if len(token_) == 0:
        return None

    LOGIN_TOKEN = json.loads(token_)
    if LOGIN_TOKEN.get('lfvp_access_token') is not None:
        # Verify our token to see if it's still valid.
        bstr = LOGIN_TOKEN.get('lfvp_access_token').split(".")[1]
        b64str = base64.b64decode(bstr + '=' * (-len(bstr) % 4))

        # Check expiration time
        lfvp_access_token_b64 = json.loads(b64str)
        exp = round(datetime.fromtimestamp(lfvp_access_token_b64.get('exp'), tz=timezone.utc).timestamp())
        now = round(datetime.utcnow().timestamp())

        if exp > now:
            return LOGIN_TOKEN

    return None


def save_token(buffer):
    with xbmcvfs.File('special://userdata/addon_data/plugin.video.catchuptvandmore/tokenrtlplay', 'wb') as f1:
        result = json.dump(buffer, f1, ensure_ascii=False, indent=4)
        f1.close()

    return result


@Resolver.register
def get_login_token(plugin, **kwargs):
    # Check is valide token
    LOGIN_TOKEN = is_valid_token()
    if LOGIN_TOKEN:
        return LOGIN_TOKEN

    login = plugin.setting.get_string('rtlplaybe.login')
    password = plugin.setting.get_string('rtlplaybe.password')
    if login == '' or password == '':
        xbmcgui.Dialog().ok(
            plugin.localize(30600),
            plugin.localize(30604) % ('RTLPlay (BE)', ('%s' % PUBLIC_SITE)))
        return None

    # RTLPLAY Device_Id
    response = urlquick.get(BASE_URL, headers=GENERIC_HEADERS, max_age=-1)
    cookies = response.cookies.get_dict()
    lfvp_device_id = cookies['lfvp_device_id']
    lfvp_disabled_storefronts = cookies['lfvp_disabled_storefronts']
    ak_bmsc = cookies['ak_bmsc']

    # SSO token
    cnx_cookies = {
        'lfvp_device_id': lfvp_device_id,
        'lfvp_disabled_storefronts': lfvp_disabled_storefronts,
        'ak_bmsc': ak_bmsc,
        'lfvp_auth.redirect_uri': BASE_URL,
    }
    response = urlquick.get(BASE_URL + '/connexion', cookies=cnx_cookies, headers=GENERIC_HEADERS, allow_redirects=True, timeout=REQUESTS_TIMEOUT, max_age=-1)
    sso_url = []
    if response.history:
        for resp in response.history:
            sso_url.append(resp.url)
        sso_url.append(response.url)

    json_data = {
        'username': login,
        'password': password,
    }
    response = urlquick.post(URL_SSO_LOGIN, headers=GENERIC_HEADERS, json=json_data, timeout=10, max_age=-1)
    json_parser = response.json()
    if json_parser['httpStatusCode'] == 400:
        xbmcgui.Dialog().ok(
            plugin.localize(30600),
            plugin.localize(30604) % ('RTLPlay (BE)', ('%s' % PUBLIC_SITE)))
        return None

    sso_token = json_parser['data']['userAccount']['session']['encryptedToken']
    sso_cookies = response.cookies.get_dict()

    # SSO auth
    params = {
        'redirectUrl': sso_url[1].replace('https://sso.rtl.be', ''),
        'token': sso_token,
    }
    response = urlquick.get(URL_SSO_AUTH, params=params, cookies=sso_cookies, headers=GENERIC_HEADERS, timeout=REQUESTS_TIMEOUT, max_age=-1)
    sso_code = re.findall(r'name=\"code\" value=\"(.*)\"', response.content.decode())
    sso_state = re.findall(r'name=\"state\" value=\"(.*)\"', response.content.decode())

    # RTLPlay callback
    cookies = {
        'lfvp_device_id': lfvp_device_id,
        'lfvp_disabled_storefronts': lfvp_disabled_storefronts,
        'ak_bmsc': ak_bmsc,
        'lfvp_auth.redirect_uri': BASE_URL,
        'lfvp_auth.state': sso_state[0],
    }
    data = {
        'code': sso_code[0],
        'state': sso_state[0],
        'iss': 'https://sso.rtl.be/oidc/',
    }
    response = requests.post(BASE_URL + '/login-callback', cookies=cookies, headers=GENERIC_HEADERS, data=data, allow_redirects=True, timeout=REQUESTS_TIMEOUT)
    login_cookie = []
    if response.history:
        for resp in response.history:
            login_cookie.append(resp.cookies.get_dict())
    callback_cookie = response.cookies.get_dict()

    login_token = {
        "ak_bmsc": ak_bmsc,
        "bm_sv": callback_cookie['bm_sv'],
        "lfvp_access_token": login_cookie[0]['lfvp_access_token'],
        "lfvp_device_id": lfvp_device_id,
        "lfvp_disabled_storefronts": "",
        "lfvp_id_token": login_cookie[0]['lfvp_id_token'],
        "lfvp_refresh_token": login_cookie[0]['lfvp_refresh_token'],
    }
    for profile_id in login_cookie:
        if 'lfvp_auth.profile' in profile_id:
            x_dpp_profile = re.match(r"^([a-f\d]{8}(-[a-f\d]{4}){3}-[a-f\d]{12})", profile_id.get('lfvp_auth.profile'), re.IGNORECASE).group(1)
            login_token.update({"lfvp_auth.profile": x_dpp_profile, })
        if 'lfvp_auth_token' in profile_id:
            login_token.update({"lfvp_auth_token": profile_id.get('lfvp_auth_token'), })

    save_token(login_token)

    return login_token


@Resolver.register
def get_video_url(plugin, item_id, video_id, download_mode=False, **kwargs):
    video_url = BASE_URL + '/player/' + video_id
    manifest, license_url, lic_token = get_final_video_url(plugin, item_id, video_url)

    if manifest is None:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    if license_url is not None:
        license_url = URL_LICENCE_KEY % lic_token

    return resolver_proxy.get_stream_with_quality(
        plugin, video_url=manifest, manifest_type='mpd',
        license_url=license_url)


def get_final_video_url(plugin, item_id, video_url):
    login_token = get_login_token(plugin)
    if login_token is None:
        return False

    is_live = "/direct/" in video_url and "/player/" not in video_url
    response = urlquick.get(video_url, headers=RTLPLAY_HEADERS, cookies=login_token, max_age=-1)
    if response.status_code != 200:
        return None, None, None

    response = response.content.decode()
    pattern = re.search(r'apiKey: "([^"]*)"', response)
    if pattern is not None:
        api_key = pattern.group(1)
    else:
        api_key = None

    pattern = re.search(r'token: "([^"]*)"', response)
    if pattern is not None:
        bearer_token = pattern.group(1)
    else:
        bearer_token = None

    if is_live:
        for r1, r2 in [(r"playerData\s*=", "assetId"), (r"channel\s*:", "id")]:
            pattern_r1 = re.search(r1 + "[^{}]+{([^{}]+)}", response)
            if pattern_r1 is not None:
                content_id = pattern_r1.group(1)
                pattern_r2 = re.search(r2 + "[^\"']+[\"']([^\"']+)[\"']", content_id)
                if pattern_r2 is not None:
                    content_id = pattern_r2.group(1)
                    assert len(content_id) > 0
                    break
                else:
                    content_id = None
            else:
                content_id = None
    else:
        content_id = re.search(r"/player/([^/?]*)", video_url).group(1)

    if bearer_token is None or api_key is None:
        return None, None, None

    headers_cfg = RTLPLAY_HEADERS.copy()
    headers_cfg.update({'x-api-key': api_key, })
    headers_cfg.update({'popcorn-sdk-version': POPCORN_SDK, })
    headers_cfg.update({'authorization': 'Bearer ' + bearer_token, })
    params_cfg = {'startPosition': '0.0', 'autoPlay': 'true'}
    # json_cfg = {'deviceType': 'web', 'zone': 'rtlplay'}
    json_cfg = {"deviceType": "android-phone", "zone": "rtlplay"}
    response = urlquick.post(URL_CONFIG % content_id,
                             params=params_cfg,
                             headers=headers_cfg,
                             json=json_cfg,
                             timeout=REQUESTS_TIMEOUT,
                             max_age=-1)
    if response.status_code == 403:
        return None, None, None

    response = json.loads(response.content.decode())

    if response.get("code", None) == 103 and "available" in response.get("type", "").lower():
        return None, None, None
    if response.get("code", None) == 104 and "found" in response.get("type", "").lower():
        return None, None, None

    response = response["video"]
    manifest = None
    lic_token = None
    license_url = None
    for stream in response["streams"]:
        if stream["type"] != "dash" or ".mpd" not in stream["url"]:
            continue
        manifest = stream["url"]

        drm = stream.get("drm", None)
        if drm is None:
            break

        for k in drm:
            if "widevine" in k.lower():
                drm = drm[k]
                break

        lic_token = drm["drmtoday"]["authToken"]
        license_url = drm["licenseUrl"]
        break

    return manifest, license_url, lic_token


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    video_url = BASE_URL + '/direct/' + LIVE_CHANNEL[item_id]
    manifest, license_url, lic_token = get_final_video_url(plugin, item_id, video_url)

    if manifest is None:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    if license_url is not None:
        license_url = URL_LICENCE_KEY % lic_token

    return resolver_proxy.get_stream_with_quality(
        plugin, video_url=manifest, manifest_type='mpd',
        license_url=license_url)
