# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More
# Partially based on Diazole's work (https://github.com/Diazole/c4-dl)

from __future__ import unicode_literals

import base64
import re
import json
import time
from builtins import str

import xbmcgui
from kodi_six import xbmcvfs

import requests
from codequick import Listitem, Script, Resolver, Route
import urlquick

from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment
from resources.lib.py_utils import datetime_strptime

from resources.lib import resolver_proxy, web_utils

try:
    from Crypto.Cipher import AES
except ImportError:
    from Cryptodome.Cipher import AES

try:
    from Crypto.Util.Padding import unpad
except ImportError:
    from Cryptodome.Util.Padding import unpad

CACHE_FILE = 'special://userdata/addon_data/plugin.video.catchuptvandmore/channel4_auth.json'
URL_ROOT = 'https://www.channel4.com'
AUTH_ENV = 'https://api.channel4.com'
PREDICTIVE_SEARCH_URL = "https://all4nav.channel4.com/v1/api/search"
URL_API_HOMEPAGE = 'https://www.channel4.com/api/homepage'
URL_AUTH_TOKEN = AUTH_ENV + '/online/v2/auth/token'
URL_CATEGORIES = URL_ROOT + '/categories'
URL_PROGRAMMES = URL_ROOT + '/programmes'
URL_VOD_API = AUTH_ENV + '/online/v1/vod/stream/{programme_id}?client={client}'
URL_VOD_WEB = URL_ROOT + '/vod/stream/'
URL_LICENSE = 'https://c4.eme.lp.aws.redbeemedia.com/wvlicenceproxy-service/widevine/acquire'

URL_LIVE_API = AUTH_ENV + '/online/v1/live/simulcast/{item_id}?client={client}&quality=HD'
URL_LIVE_WEB = URL_ROOT + '/simulcast/channels/%s'

AUTH_TOKEN_HEADERS = {"authorization": "Basic MzZVVUN0OThWTVF2QkFnUTI3QXU4ekdIbDMxTjlMUTE6Sllzd3lIdkdlNjJWbGlrVw=="}
BASIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}
LICENSE_HEADERS = "User-Agent=%s&Content-Type=application/json&Referer=%s" % (web_utils.get_random_ua(), URL_ROOT)

KEYS = {
    'amazonfire-dash': {
        'key': 'K2C8Q09D7HJ385AB',
        'iv': 'B3LKVU05F3IDLVME'
    },
    'web': {
        'key': 'n9cLieYkqwzNCqvi',
        'iv': 'odzcU3WdUiXLucVd'
    }
}


def get_token_if_valid(channel4_auth):
    if channel4_auth and channel4_auth.get('accessToken'):
        issued_at = channel4_auth.get('issuedAt')
        expires_in = channel4_auth.get('expiresIn')
        if issued_at and expires_in:
            expiration_time = (int(issued_at) / 1000) + int(expires_in)
            if expiration_time > time.time():
                return channel4_auth.get('accessToken')
    return None


def get_refresh_token_if_refreshable(channel4_auth):
    if channel4_auth and channel4_auth.get('refreshToken'):
        refresh_token_issued_at = channel4_auth.get('refreshTokenIssuedAt')
        refresh_token_expires_in = channel4_auth.get('refreshTokenExpiresIn')
        if refresh_token_issued_at and refresh_token_expires_in:
            expiration_time = (int(refresh_token_issued_at) / 1000) + int(refresh_token_expires_in)
            if expiration_time > time.time():
                return channel4_auth.get('refreshToken')
    return None


def get_access_token(plugin):
    try:
        if plugin.setting.get_string('uk.channel4.login') and plugin.setting.get_string('uk.channel4.password'):
            channel4_auth = load_channel4_auth()
            token = get_token_if_valid(channel4_auth)
            if token:
                return token
            refresh_token = get_refresh_token_if_refreshable(channel4_auth)
            if refresh_token:
                token = refresh(plugin, refresh_token)
                if token:
                    return token
            token = login(plugin)
            if token:
                return token
    except Exception:
        pass

    return None


def refresh(plugin, refresh_token):
    data = {
        "grant_type": "refresh_token",
        "username": plugin.setting.get_string('uk.channel4.login'),
        "password": plugin.setting.get_string('uk.channel4.password'),
        "refresh_token": refresh_token,
    }
    r = requests.post(URL_AUTH_TOKEN, headers=AUTH_TOKEN_HEADERS, data=data)
    try:
        res = r.json()
    except Exception:
        error_text = 'Failed to refresh token.' + ' ' + r.text
        Script.log(error_text)
        plugin.notify('ERROR', 'Channel 4 : ' + error_text)

    if "error" in res:
        error_text = 'Failed to refresh token.' + ' ' + res['errorMessage']
        Script.log(error_text)
        plugin.notify('ERROR', 'Channel 4 : ' + error_text)

    channel4_auth = res
    save_channel4_auth(channel4_auth)
    return channel4_auth.get('accessToken', None)


def login(plugin):
    data = {
        "grant_type": "password",
        "username": plugin.setting.get_string('uk.channel4.login'),
        "password": plugin.setting.get_string('uk.channel4.password'),
    }
    r = requests.post(URL_AUTH_TOKEN, headers=AUTH_TOKEN_HEADERS, data=data)
    try:
        res = r.json()
    except Exception:
        Script.log('Failed to login. ' + r.text)
        plugin.notify('ERROR', 'Channel 4 : ' + plugin.localize(30711) + '. ' + r.text)

    if res and "error" in res:
        Script.log('Failed to login. ' + res['errorMessage'])
        plugin.notify('ERROR', 'Channel 4 : ' + plugin.localize(30711) + '. ' + res['errorMessage'])

    channel4_auth = res
    save_channel4_auth(channel4_auth)
    return channel4_auth.get('accessToken', None)


def load_channel4_auth():
    with xbmcvfs.File(CACHE_FILE, 'r') as f1:
        channel4_auth = f1.read()
        f1.close()
        if channel4_auth:
            return json.loads(channel4_auth)
    return None


def save_channel4_auth(channel4_auth):
    with xbmcvfs.File(CACHE_FILE, 'wb') as f1:
        json.dump(channel4_auth, f1, ensure_ascii=False, indent=4)
        f1.close()


@Route.register(content_type="videos")
def do_search(plugin, search_query):
    params = {
        "expand": "default",
        "q": search_query,
        "limit": 100,
        "offset": 0
    }

    search_json = json.loads(urlquick.get(PREDICTIVE_SEARCH_URL, headers=BASIC_HEADERS, params=params, max_age=-1).text)

    results = search_json.get("results", [])
    if isinstance(results, dict):
        # No results found
        xbmcgui.Dialog().ok('No Matches', results.get('summary', 'No items found'))
        yield False
        return

    for result in results:
        if result:
            brand = result["brand"]
            label = brand.get("label")
            item = Listitem()
            item.label = brand.get("title")
            thumbnail_url = brand.get("thumbnailUrl")
            thumbnail_url = web_utils.remove_params(thumbnail_url)  # Remove params lowering resolution
            item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = thumbnail_url
            url = brand.get("href")
            plot = brand.get("description")
            if label:
                plot = plot + '\n\n' + label
            item.info["plot"] = plot
            item.set_callback(list_seasons, url=url)
            item_post_treatment(item)
            yield item


@Route.register
def main_menu(plugin, **kwargs):
    yield Listitem.search(do_search)

    yield Listitem.from_dict(
        callback=list_categories,
        label='Categories'
    )

    try:
        json_data = json.loads(requests.get(URL_API_HOMEPAGE, headers=BASIC_HEADERS).text)
        for slice in json_data['slices']:
            if slice:
                label = slice.get('title')
                if label:
                    yield Listitem.from_dict(
                        callback=list_slice,
                        label=label,
                        params={'slice': slice}
                    )
                else:
                    for slice_item in slice['sliceItems']:
                        item = Listitem()
                        title = slice_item.get('title')
                        item.label = title
                        item.info['plot'] = get_slice_item_plot(slice_item)
                        item.art['thumb'] = item.art['landscape'] = slice_item["image"]["href"]
                        slice_item_type = slice_item.get('type')
                        if slice_item_type == 'brand':
                            item.info['genre'] = slice_item.get('brand', {}).get('categories', [])
                            item.art['fanart'] = get_brand_fan_art(slice_item)
                            url_item = URL_PROGRAMMES + '/' + slice_item.get('brand').get('websafeTitle')
                            item.set_callback(list_seasons, url=url_item)
                            item_post_treatment(item)
                            yield item
    except Exception:
        pass


def get_slice_item_plot(slice_item):
    plot = slice_item.get('summary')
    editorial_label = slice_item.get('editorialLabel')
    if editorial_label:
        plot = plot + '\n\n' + editorial_label
    return plot


def get_brand_fan_art(slice_item):
    images = slice_item.get('brand', {}).get('images', [])
    if images:
        for image in images:
            if image.get('imageType') == 'PRIMARY_HERO' or 'Apple_TV' in image.get('title'):
                return image.get('href')
    return None


def get_media_type(programme_type):
    if programme_type == 'FM':
        return 'movie'
    if programme_type in {'FB', 'MSU', 'MST', 'SSU'}:
        return 'episode'
    return 'video'


def extract_yyyy_mm_dd_date_str(date_label):
    try:
        if date_label:
            date_str = date_label.replace("First shown: ", "").strip()
            date_obj = datetime_strptime(date_str, "%a %d %b %Y")
            return date_obj.strftime("%Y-%m-%d")
    except Exception:
        pass
    return None


@Route.register
def list_categories(plugin, **kwargs):
    html_text = urlquick.get(URL_CATEGORIES, headers=BASIC_HEADERS, max_age=-1).parse()
    for script in html_text.iterfind('.//script'):
        script_text = script.text
        if script_text is not None and script_text.split()[0] == 'window.__PARAMS__':
            data = json.loads(re.sub(r'^.*?{', '{', script_text).replace("undefined", "{}"))
            initial_data = data.get('initialData', {})
            if initial_data:
                category_links = initial_data.get('categoryLinks', [])
                if category_links:
                    for category_link in category_links:
                        item = Listitem()
                        item.label = category_link.get('tagName')
                        url_item = URL_ROOT + category_link.get('href')
                        item.set_callback(list_programs, url=url_item, offset='0')
                        item_post_treatment(item)
                        yield item


@Route.register
def list_slice(plugin, slice, **kwargs):
    for slice_item in slice['sliceItems']:
        slice_item_type = slice_item.get('type')

        if slice_item_type == 'ip':
            continue

        item = Listitem()

        if slice_item_type != 'slot':
            item.label = slice_item.get('title')
            item.info['plot'] = get_slice_item_plot(slice_item)
            item.art['thumb'] = item.art['landscape'] = slice_item["image"]["href"]

        if slice_item_type == 'brand':
            item.info['genre'] = slice_item.get('brand', {}).get('categories', [])
            item.art['fanart'] = get_brand_fan_art(slice_item)
            url_item = URL_PROGRAMMES + '/' + slice_item.get('brand').get('websafeTitle')
            item.set_callback(list_seasons, url=url_item)
        elif slice_item_type == 'freeform':
            url_item = slice_item.get('url')
            item.set_callback(list_programs, url=url_item, offset='0')
        elif slice_item_type == 'slot':
            slot_tx_channel = slice_item.get('slot').get('slotTXChannel')
            item.label = slot_tx_channel
            item.set_callback(get_live_url, item_id=slot_tx_channel)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, url, offset, **kwargs):
    """
    Build programs listing
    """
    params = {
        'json': 'true',
        'offset': offset,
        'sort': Script.setting['uk.channel4.programmes.sort.by']
    }
    programs = json.loads(urlquick.get(url, headers=BASIC_HEADERS, params=params, max_age=-1).text)
    programs_number = programs['noOfShows']

    for program in programs["brands"]["items"]:
        item = Listitem()
        item.label = program["labelText"]
        item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = program["imageLink"]
        item.set_callback(list_seasons, url=program["hrefLink"])
        item.info["plot"] = program["overlayText"]
        expanded_tile = program.get("expandedTile")
        if expanded_tile:
            if "summary" in expanded_tile and expanded_tile["summary"]:
                item.info["plot"] = expanded_tile["summary"]
            if "genres" in expanded_tile and expanded_tile['genres']:
                item.info['genre'] = expanded_tile["genres"]
        item_post_treatment(item)
        yield item

    nboffset = int(offset) + len(programs["brands"]["items"])
    if nboffset < programs_number:
        item = Listitem.next_page(url=url, offset=str(nboffset))
        item.property['SpecialSort'] = 'bottom'
        yield item


@Route.register
def list_seasons(plugin, url, **kwargs):
    html_text = urlquick.get(url, headers=BASIC_HEADERS, max_age=-1).parse()

    for script in html_text.iterfind('.//script'):
        script_text = script.text
        if script_text is not None and script_text.split()[0] == 'window.__PARAMS__':
            datas = json.loads(re.sub(r'^.*?{', '{', script_text).replace("undefined", "{}"))['initialData']['brand']
            genres = []
            if "categories" in datas and datas['categories']:
                genres = [genre["displayName"].strip() for genre in datas["categories"]]
            fanart = datas.get('images', {}).get('hero', {}).get('landscape', {}).get('src', None)
            if bool(datas['allSeriesCount']) is False or len(datas['series']) == 0:
                for episode in datas['episodes']:
                    if episode.get('assetId'):
                        item = Listitem()
                        toreplace = re.compile(r'(.*?)Episode').findall(episode['title'])
                        if bool(toreplace):
                            item.label = episode['title'].replace(toreplace[0], '') + " ({})".format(episode['originalTitle'])
                        else:
                            item.label = episode['title'] + " ({})".format(episode['originalTitle'])
                        item.info['season'] = episode.get('seriesNumber')
                        item.info['episode'] = episode.get('episodeNumber')
                        item.info['mediatype'] = get_media_type(datas.get('programmeType'))
                        item.art['thumb'] = item.art['landscape'] = episode['image']['src']
                        item.art['fanart'] = fanart
                        item.set_callback(get_video, programmeId=episode['programmeId'], assetId=episode['assetId'])
                        item.info['plot'] = episode['summary']
                        if 'guidance' in episode and episode['guidance']:
                            item.info['plot'] = item.info['plot'] + '\n\n' + episode['guidance']
                        yyyy_mm_dd_date_str = extract_yyyy_mm_dd_date_str(episode.get('dateLabel'))
                        if yyyy_mm_dd_date_str:
                            item.info.date(yyyy_mm_dd_date_str, '%Y-%m-%d')
                        if 'durationLabel' in episode and episode['durationLabel']:
                            try:
                                item.info['duration'] = int(episode['durationLabel'].split()[0]) * 60
                            except Exception:
                                pass
                        item.info['genre'] = genres
                        item_post_treatment(item)
                        yield item
            else:
                series = datas['series']
                for season in series:
                    series_number = season['seriesNumber']
                    item = Listitem()
                    item.label = season['title']
                    if 'image16x9' in datas['images']:
                        image = datas['images']['image16x9']['src']
                    else:
                        image = datas['images']['hero']['landscape']['src']
                    item.art['thumb'] = item.art['landscape'] = image
                    item.art['fanart'] = fanart
                    item.set_callback(get_episodes_list, series, series_number, datas)
                    item.info['plot'] = season['summary']
                    item.info['genre'] = genres
                    item.info['mediatype'] = 'season'
                    item.info['season'] = series_number
                    item_post_treatment(item)
                    yield item


@Route.register
def get_episodes_list(plugin, series, series_number, datas, **kwargs):
    genres = []
    if "categories" in datas and datas['categories']:
        genres = [genre["displayName"].strip() for genre in datas["categories"]]
    fanart = datas.get('images', {}).get('hero', {}).get('landscape', {}).get('src', None)
    for episode in datas['episodes']:
        if episode['seriesNumber'] == series_number and episode.get('assetId'):
            item = Listitem()
            toreplace = re.compile(r'(.*?)Episode').findall(episode['title'])
            if bool(toreplace):
                item.label = episode['title'].replace(toreplace[0], '') + " ({})".format(episode['originalTitle'])
            else:
                item.label = episode['title'] + " ({})".format(episode['originalTitle'])
            item.info['season'] = episode.get('seriesNumber')
            item.info['episode'] = episode.get('episodeNumber')
            item.info['mediatype'] = get_media_type(datas.get('programmeType'))
            item.art['thumb'] = item.art['landscape'] = episode['image']['src']
            item.art['fanart'] = fanart
            item.set_callback(get_video, programmeId=episode['programmeId'], assetId=episode['assetId'])
            item.info['plot'] = episode['summary']
            if 'guidance' in episode and episode['guidance']:
                item.info['plot'] = item.info['plot'] + '\n\n' + episode['guidance']
            yyyy_mm_dd_date_str = extract_yyyy_mm_dd_date_str(episode.get('dateLabel'))
            if yyyy_mm_dd_date_str:
                item.info.date(yyyy_mm_dd_date_str, '%Y-%m-%d')
            if 'durationLabel' in episode and episode['durationLabel']:
                try:
                    item.info['duration'] = int(episode['durationLabel'].split()[0]) * 60
                except Exception:
                    pass
            item.info['genre'] = genres
            item_post_treatment(item)
            yield item


@Resolver.register
def get_video(plugin, programmeId, assetId, **kwargs):
    access_token = get_access_token(plugin)
    if access_token:  # Allows higher bitrate 1080p
        client = 'amazonfire-dash'
        url_video_json = URL_VOD_API.format(programme_id=programmeId, client=client)
        headers = {"authorization": f"Bearer {access_token}"}
    else:
        client = 'web'
        url_video_json = URL_VOD_WEB + '{}'.format(programmeId)
        headers = None

    resp = urlquick.get(url_video_json, max_age=-1, headers=headers)

    json_video = json.loads(resp.text)
    supported_video_profiles = {'bigscreendashwv-dyn-stream-1', 'dashwv-dyn-stream-1'}
    for field in json_video['videoProfiles']:
        if field['name'] in supported_video_profiles:
            token = field['streams'][0]['token']
            url = field['streams'][0]['uri']
            break

    subtitle_url = ''
    if plugin.setting.get_boolean('active_subtitle'):
        supported_subtitles_formats = ['srt_009', 'sami_001']
        if get_kodi_version() >= 20:
            supported_subtitles_formats.insert(0, 'webvtt_007')
        for subtitle_format in supported_subtitles_formats:
            if subtitle_url:
                break
            for field in json_video['subtitlesAssets']:
                if field['format'] == subtitle_format:
                    subtitle_url = field['url']
                    break

    keys = KEYS[client]
    cipher = AES.new(bytes(keys['key'], 'UTF-8'), AES.MODE_CBC, bytes(keys['iv'], 'UTF-8'))
    decoded_token = unpad(cipher.decrypt(base64.b64decode(token)), 16, style='pkcs7').decode('UTF-8').split('|')[1]

    payload = json.dumps({
        "request_id": assetId,
        "token": decoded_token,
        "video": {
            "type": "ondemand",
            "url": url
        },
        "message": "b{SSM}"
    })

    item = Listitem()
    item.path = url
    if 'http' in subtitle_url:
        item.subtitles.append(subtitle_url)
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = '%s|%s|%s|JBlicense' % (URL_LICENSE, LICENSE_HEADERS, payload)

    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    access_token = get_access_token(plugin)
    if access_token:
        client = 'amazonfire-dash'
        url_video_json = URL_LIVE_API.format(item_id=item_id, client=client)
        headers = {"authorization": f"Bearer {access_token}"}
    else:
        client = 'web'
        url_video_json = URL_LIVE_WEB % item_id
        headers = None

    resp = urlquick.get(url_video_json, headers=headers, max_age=-1)

    json_video = json.loads(resp.text)
    for field in json_video['channelInfo']['videoProfiles']:
        if field['name'] == 'dashwv-live-stream-iso-dash-sp-tl':
            token = field['streams'][0]['token']
            url = field['streams'][0]['uri']
            break

    keys = KEYS[client]
    cipher = AES.new(bytes(keys['key'], 'UTF-8'), AES.MODE_CBC, bytes(keys['iv'], 'UTF-8'))
    full_decoded_token = unpad(cipher.decrypt(base64.b64decode(token)), 16, style='pkcs7').decode('UTF-8')
    decoded_token = re.compile(r'\&t\=(.*?)$').findall(full_decoded_token)[0]

    payload = json.dumps({
        "token": decoded_token,
        "video": {
            "type": "simulcast",
            "url": url
        },
        "message": "b{SSM}"
    })

    item = Listitem()
    item.path = url
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = '%s|%s|%s|JBlicense' % (URL_LICENSE, LICENSE_HEADERS, payload)

    return item
