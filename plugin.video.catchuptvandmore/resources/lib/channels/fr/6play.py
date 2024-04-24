# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

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
URL_ROOT = 'http://android.middleware.6play.fr/6play/v2/platforms/' \
           'm6group_androidmob/services/%s/folders?limit=999&offset=0'

URL_ALL_PROGRAMS = 'http://android.middleware.6play.fr/6play/v2/platforms/' \
                   'm6group_androidmob/services/6play/programs'

# Url to get catgory's programs
# e.g. Le meilleur patissier, La france à un incroyable talent, ...
# We get an id by program
URL_CATEGORY = 'http://android.middleware.6play.fr/6play/v2/platforms/' \
               'm6group_androidmob/services/6play/folders/%s/programs' \
               '?limit=999&offset=0&csa=6&with=parentcontext'

# Url to get program's subfolders
# e.g. Saison 5, Les meilleurs moments, les recettes pas à pas, ...
# We get an id by subfolder
URL_SUBCATEGORY = 'http://android.middleware.6play.fr/6play/v2/platforms/' \
                  'm6group_androidmob/services/6play/programs/%s' \
                  '?with=links,subcats,rights'

# Url to get shows list
# e.g. Episode 1, Episode 2, ...
URL_VIDEOS = 'http://chromecast.middleware.6play.fr/6play/v2/platforms/' \
             'chromecast/services/6play/programs/%s/videos?' \
             'csa=6&with=clips,freemiumpacks&type=vi,vc,playlist&limit=999' \
             '&offset=0&subcat=%s&sort=subcat'

URL_VIDEOS2 = 'https://chromecast.middleware.6play.fr/6play/v2/platforms/' \
              'chromecast/services/6play/programs/%s/videos?' \
              'csa=6&with=clips,freemiumpacks&type=vi&limit=999&offset=0'

URL_JSON_VIDEO = 'https://chromecast.middleware.6play.fr/6play/v2/platforms/' \
                 'chromecast/services/6play/videos/%s' \
                 '?csa=6&with=clips,freemiumpacks'

URL_IMG = 'https://images.6play.fr/v1/images/%s/raw'

URL_COMPTE_LOGIN = 'https://login.6play.fr/accounts.login'
# https://login.6play.fr/accounts.login?loginID=*****&password=*******&targetEnv=mobile&format=jsonp&apiKey=3_hH5KBv25qZTd_sURpixbQW6a4OsiIzIEF2Ei_2H7TXTGLJb_1Hr4THKZianCQhWK&callback=jsonp_3bbusffr388pem4
# TODO get value Callback
# callback: jsonp_3bbusffr388pem4

URL_GET_JS_ID_API_KEY = 'https://www.6play.fr/connexion'

# Id
URL_API_KEY = 'https://www.6play.fr/main-%s.bundle.js'

PATTERN_API_KEY = re.compile(r'\"eu1.gigya.com\",key:\"(.*?)\"')

PATTERN_JS_ID = re.compile(r'main-(.*?)\.bundle\.js')

API_KEY = "3_hH5KBv25qZTd_sURpixbQW6a4OsiIzIEF2Ei_2H7TXTGLJb_1Hr4THKZianCQhWK"

URL_TOKEN_DRM = 'https://6play-users.6play.fr/v2/platforms/chromecast/services/6play/users/%s/videos/%s/upfront-token'

# URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&Origin=https://www.6play.fr&Referer=%s&x-dt-auth-token=%s|R{SSM}|JBlicense'
URL_LICENCE_KEY = 'https://lic.drmtoday.com/license-proxy-widevine/cenc/|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=lic.drmtoday.com&x-dt-auth-token=%s|R{SSM}|JBlicense'
# Referer, Token

URL_LIVE_JSON = 'https://chromecast.middleware.6play.fr/6play/v2/platforms/chromecast/services/6play/live'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}
M6_HEADERS = {
    'User-Agent': web_utils.get_random_ua(),
    'x-customer-name': 'm6web'
}

# Chaine


def get_api_key():
    resp_js_id = urlquick.get(URL_GET_JS_ID_API_KEY, headers=GENERIC_HEADERS)
    found_js_id = PATTERN_JS_ID.findall(resp_js_id.text)
    if len(found_js_id) == 0:
        return API_KEY
    js_id = found_js_id[0]
    resp = urlquick.get(URL_API_KEY % js_id, headers=GENERIC_HEADERS)
    # Hack to force encoding of the response
    resp.encoding = 'utf-8'
    found_items = PATTERN_API_KEY.findall(resp.text)
    if len(found_items) == 0:
        return API_KEY
    return found_items[0]


@Route.register
def sixplay_root(plugin, **kwargs):
    # (item_id, label, thumb, fanart)
    channels = [
        ('m6', 'M6', 'm6.png', 'm6_fanart.jpg'),
        ('w9', 'W9', 'w9.png', 'w9_fanart.jpg'),
        ('6ter', '6ter', '6ter.png', '6ter_fanart.jpg'),
        ('gulli', 'Gulli', 'gulli.png', 'gulli_fanart.jpg'),
        ('fun_radio', 'Fun Radio', 'funradio.png', 'funradio_fanart.jpg'),
        ('rtl2', 'RTL 2', 'rtl2.png', 'rtl2_fanart.jpg'),
        ('courses', 'Cage Warriors', 'cagewarriors.png', 'cagewarriors_fanart.jpg')
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
    if item_id == 'rtl2' or \
            item_id == 'fun_radio' or \
            item_id == 'courses' or \
            item_id == 'gulli':
        resp = urlquick.get(URL_ROOT % item_id, headers=GENERIC_HEADERS)
    else:
        resp = urlquick.get(URL_ROOT % (item_id + 'replay'), headers=GENERIC_HEADERS)
    json_parser = resp.json()

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


@Route.register
def list_programs(plugin, item_id, category_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_CATEGORY % category_id, headers=GENERIC_HEADERS)
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
    resp = urlquick.get(URL_SUBCATEGORY % program_id, headers=GENERIC_HEADERS)
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
    resp = urlquick.get(url, headers=GENERIC_HEADERS)
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
    if get_kodi_version() < 18:
        video_json = urlquick.get(URL_JSON_VIDEO % video_id, headers=M6_HEADERS, max_age=-1)
        json_parser = json.loads(video_json.text)

        video_assets = json_parser['clips'][0]['assets']

        final_video_url = get_final_video_url(plugin, video_assets)
        if final_video_url is None:
            return False

        if download_mode:
            return download.download_video(final_video_url)

        return final_video_url

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
        'User-Agent': web_utils.get_random_ua(),
        'referer': 'https://www.6play.fr/connexion'
    }
    resp2 = urlquick.post(URL_COMPTE_LOGIN, data=payload, headers=headers, max_age=-1)
    json_parser = json.loads(resp2.text.replace('jsonp_3bbusffr388pem4(', '').replace(');', ''))

    if "UID" not in json_parser:
        plugin.notify('ERROR', '6play : ' + plugin.localize(30711))
        return False
    account_id = json_parser["UID"]
    account_timestamp = json_parser["signatureTimestamp"]
    account_signature = json_parser["UIDSignature"]

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    # Build PAYLOAD headers
    payload_headers = {
        'x-auth-gigya-signature': account_signature,
        'x-auth-gigya-signature-timestamp': account_timestamp,
        'x-auth-gigya-uid': account_id,
        'x-customer-name': 'm6web'
    }

    token_json = urlquick.get(URL_TOKEN_DRM % (account_id, video_id),
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

    for asset in video_assets:
        if 'usp_dashcenc_h264' in asset["type"]:
            dummy_req = urlquick.get(asset['full_physical_path'], headers=GENERIC_HEADERS, allow_redirects=False)
            if 'location' in dummy_req.headers:
                video_url = dummy_req.headers['location']
            else:
                video_url = asset['full_physical_path']
            return resolver_proxy.get_stream_with_quality(
                plugin, video_url=video_url, manifest_type='mpd',
                subtitles=subtitle_url, license_url=URL_LICENCE_KEY % token)

    for asset in video_assets:
        if 'http_h264' in asset["type"]:
            if "hd" in asset["video_quality"]:
                video_url = asset['full_physical_path']
                return resolver_proxy.get_stream_with_quality(
                    plugin, video_url=video_url, subtitles=subtitle_url)

    return False


def get_final_video_url(plugin, video_assets, asset_type=None):
    if video_assets is None:
        plugin.notify('ERROR', plugin.localize(30721))
        return None

    all_datas_videos_quality = []
    all_datas_videos_path = []
    for asset in video_assets:
        if asset_type is None:
            if 'http_h264' in asset["type"]:
                all_datas_videos_quality.append(asset["video_quality"])
                all_datas_videos_path.append(asset['full_physical_path'])
            elif 'h264' in asset["type"]:
                manifest = urlquick.get(asset['full_physical_path'], headers=GENERIC_HEADERS, max_age=-1)
                if 'drm' not in manifest.text:
                    all_datas_videos_quality.append(asset["video_quality"])
                    all_datas_videos_path.append(asset['full_physical_path'])
        elif asset_type in asset["type"]:
            all_datas_videos_quality.append(asset["video_quality"])
            all_datas_videos_path.append(asset['full_physical_path'])

    if len(all_datas_videos_quality) == 0:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return None

    final_video_url = all_datas_videos_path[0]

    desired_quality = Script.setting.get_string('quality')
    if desired_quality == Quality['DIALOG']:
        selected_item = xbmcgui.Dialog().select(
            plugin.localize(30709),
            all_datas_videos_quality)
        if selected_item == -1:
            return None
        final_video_url = all_datas_videos_path[selected_item]

    elif desired_quality == Quality['BEST']:
        url_best = ''
        i = 0
        for data_video in all_datas_videos_quality:
            if 'lq' not in data_video:
                url_best = all_datas_videos_path[i]
            i = i + 1
        final_video_url = url_best

    elif desired_quality == Quality['WORST']:
        final_video_url = all_datas_videos_path[0]
        i = 0
        for data_video in all_datas_videos_quality:
            if 'lq' in data_video:
                final_video_url = all_datas_videos_path[i]
                return final_video_url

    return final_video_url


@Resolver.register
def get_playlist_urls(plugin,
                      item_id,
                      video_id,
                      url,
                      **kwargs):
    resp = urlquick.get(url, headers=GENERIC_HEADERS)
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

            video = get_video_url(
                plugin,
                item_id=item_id,
                video_id=clip_id)

            yield video


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    api_key = get_api_key()

    if plugin.setting.get_string('6play.login') == '' or \
            plugin.setting.get_string('6play.password') == '':
        xbmcgui.Dialog().ok(
            plugin.localize(30600),
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
    resp2 = urlquick.post(
        URL_COMPTE_LOGIN,
        data=payload,
        headers={
            'User-Agent': web_utils.get_random_ua(),
            'referer': 'https://www.6play.fr/connexion'})
    json_parser = json.loads(
        resp2.text.replace('jsonp_3bbusffr388pem4(', '').replace(');', ''))

    if "UID" not in json_parser:
        plugin.notify('ERROR', '6play : ' + plugin.localize(30711))
        return False
    account_id = json_parser["UID"]
    account_timestamp = json_parser["signatureTimestamp"]
    account_signature = json_parser["UIDSignature"]

    # Build PAYLOAD headers
    payload_headers = {
        'User-Agent': web_utils.get_random_ua(),
        'x-auth-gigya-signature': account_signature,
        'x-auth-gigya-signature-timestamp': account_timestamp,
        'x-auth-gigya-uid': account_id,
        'x-customer-name': 'm6web'
    }

    live_item_id = item_id.upper()
    if item_id == '6ter':
        live_item_id = '6T'
    elif item_id in {'fun_radio', 'rtl2', 'gulli'}:
        live_item_id = item_id

    url_token = URL_TOKEN_DRM % (account_id, 'dashcenc_%s' % live_item_id)
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
    if final_video_url is None:
        return False

    for asset in video_assets:
        if 'delta_dashcenc_h264' in asset["type"]:
            return resolver_proxy.get_stream_with_quality(
                plugin, video_url=final_video_url, manifest_type='mpd',
                subtitles=subtitle_url, license_url=URL_LICENCE_KEY % token)
    return False
