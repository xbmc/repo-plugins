# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

import inputstreamhelper
import requests

from codequick import Listitem, Resolver, Route
from kodi_six import xbmcgui
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import (get_kodi_version, get_selected_item_art, get_selected_item_label,
                                      get_selected_item_info, INPUTSTREAM_PROP)

try:  # Python 3
    from urllib.error import HTTPError
    from urllib.parse import quote, urlencode
except ImportError:  # Python 2
    from urllib import urlencode
    from urllib2 import quote, HTTPError

# TO DO
# Find a way to get APIKey ?

# URL_JSON_LIVES = 'https://services.vrt.be/videoplayer/r/live.json'
# All lives in this JSON

URL_ROOT = 'https://www.vrt.be'

# Replay

URL_CATEGORIES_JSON = 'https://search.vrt.be/suggest?facets[categories]=%s'
# Category Name

URL_LOGIN = 'https://accounts.eu1.gigya.com/accounts.login'

URL_TOKEN = 'https://token.vrt.be'

URL_STREAM_JSON = ('https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/'
                   'external/v1/videos/%s%%24%s?vrtPlayerToken=%s&client=vrtvideo@PROD')
# publicationid, videoid, vrtplayertoken

URL_API = 'https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1'

URL_TOKEN_LIVE = URL_API + '/tokens'

URL_LIVE = URL_API + '/videos/vualto_%s_geo?vrtPlayerToken=%s&client=vrtvideo'
# ChannelName

ROOT_VRT = {'/vrtnu/a-z/': 'A-Z', '/vrtnu/categorieen/': 'Categorieën'}

VUPLAY_API_URL = 'https://api.vuplay.co.uk'


def get_api_key():
    # resp = urlquick.get(
    #     URL_ROOT + '/vrtnu/')
    # return re.compile(
    #     'apiKey=(.*?)\&').findall(api_key_html)[0]
    return '3_qhEcPa5JGFROVwu5SWKqJ4mVOIkwlFNMSKwzPDAh8QZOtHqu6L4nD5Q7lk0eXOOG'


@Route.register
def list_root(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    for root_part_url, root_title in list(ROOT_VRT.items()):
        root_url = URL_ROOT + root_part_url

        if 'categorieen' in root_part_url:
            next_value = 'list_categories'
        else:
            next_value = 'list_programs'

        item = Listitem()
        item.label = root_title
        item.set_callback(eval(next_value), item_id=item_id, root_url=root_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, root_url, **kwargs):
    resp = urlquick.get(root_url)
    root = resp.parse()

    for program_datas in root.iterfind(".//nui-tile"):
        program_title = program_datas.find('.//a').text.strip()
        program_image = 'https:' + program_datas.find('.//img').get(
            'data-responsive-image')
        program_url = URL_ROOT + program_datas.find('.//a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos, item_id=item_id, next_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_categories(plugin, item_id, root_url, **kwargs):
    resp = urlquick.get(root_url, max_age=-1)
    root = resp.parse()

    for category_datas in root.iterfind(".//nui-tile"):
        category_title = category_datas.find('.//a').text.strip()
        category_image = 'https:' + category_datas.find(
            ".//img").get('data-responsive-image')
        category_url = URL_ROOT + category_datas.find('.//a').get('href')

        item = Listitem()
        item.label = category_title
        item.art['thumb'] = item.art['landscape'] = category_image
        item.set_callback(list_category_programs,
                          item_id=item_id,
                          next_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_category_programs(plugin, item_id, next_url, **kwargs):
    category_id = re.compile('categorieen/(.*?)/').findall(next_url)[0]
    resp = urlquick.get(URL_CATEGORIES_JSON % category_id)
    json_parser = json.loads(resp.text)

    for category_program_datas in json_parser:
        category_program_title = category_program_datas['title']
        category_program_image = 'https:' + category_program_datas['thumbnail']
        category_program_url = 'https:' + category_program_datas['targetUrl']

        item = Listitem()
        item.label = category_program_title
        item.art['thumb'] = item.art['landscape'] = category_program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          next_url=category_program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, next_url, **kwargs):
    resp = urlquick.get(next_url)
    root = resp.parse()

    if root.find(".//ul[@id='seasons-list']") is not None:
        # show has multiple seasons
        list_videos_datas = root.find(".//ul[@id='seasons-list']")
        for season_item in list_videos_datas.iterfind('.//li/a'):
            season_name = season_item.find('nui-replace-text').text.strip('\n\t\r ')
            try:
                season_name = 'Seizoen %d' % int(season_name)
            except (TypeError, ValueError):
                pass

            season_url = URL_ROOT + season_item.get('href')
            season_image = 'https:' + root.find('.//nui-media').get('posterimage')
            season_plot = root.find('.//h1[@class="title"]').text.strip()

            item = Listitem()
            item.label = season_name
            item.art['thumb'] = item.art['landscape'] = season_image
            item.info['plot'] = season_plot

            item.set_callback(list_videos,
                              item_id=item_id,
                              next_url=season_url)
            item_post_treatment(item)
            yield item
    elif root.find(".//nui-tile") is not None:
        for video_datas in root.iterfind(".//nui-tile"):
            video_url = URL_ROOT + video_datas.get('href')
            video_title = video_datas.find('.//h3/a').text.strip()
            video_image = 'https:' + video_datas.find('.//img').get('data-responsive-image')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            try:
                video_duration = video_datas.find('.//span[@class="duration"]').text
                item.info['duration'] = video_duration
            except AttributeError:
                pass
            # try:
            #     date_value = video_datas.find(
            #         './/time[@class="date-long"]').get('datetime').split('T')[0]
            #     item.info.date(date_value, '%Y-%m-%d')
            # except AttributeError:
            #     pass

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    else:
        video_title = root.find('.//h1[@class="title"]').text.strip()
        video_image = root.find('.//meta[@property="og:image"]').get('content')
        video_plot = root.find('.//meta[@property="og:description"]').get('content')
        video_duration = root.find('.//meta[@property="og:video:duration"]').get('content').rstrip('imn')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=next_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    session_requests = requests.session()

    if plugin.setting.get_string('vrt.login') == '' or \
            plugin.setting.get_string('vrt.password') == '':
        xbmcgui.Dialog().ok(
            'Info',
            plugin.localize(30604) % ('VRT NU', 'https://www.vrt.be/vrtnu/'))
        return False

    # Build PAYLOAD
    payload = {
        'loginID': plugin.setting.get_string('vrt.login'),
        'password': plugin.setting.get_string('vrt.password'),
        'targetEnv': 'jssdk',
        'APIKey': get_api_key(),
        'includeSSOToken': 'true',
        'authMode': 'cookie'
    }
    # Login / Verify
    resp = session_requests.post(URL_LOGIN, data=payload)
    json_parser = json.loads(resp.text)
    if json_parser['statusCode'] != 200:
        plugin.notify('ERROR', 'VRT NU : ' + plugin.localize(30711))
        return False
    # Request Token
    headers = {
        'Content-Type': 'application/json',
        'Referer': URL_ROOT + '/vrtnu/'
    }
    data = '{"uid": "%s", ' \
           '"uidsig": "%s", ' \
           '"ts": "%s", ' \
           '"email": "%s"}' % (
               json_parser['UID'],
               json_parser['UIDSignature'],
               json_parser['signatureTimestamp'],
               plugin.setting.get_string('vrt.login'))
    session_requests.post(URL_TOKEN, data=data, headers=headers)

    resp2 = session_requests.post(URL_TOKEN_LIVE)
    json_parser_token = json.loads(resp2.text)
    vrtplayertoken = json_parser_token["vrtPlayerToken"]

    resp3 = urlquick.get(video_url)
    root = resp3.parse()
    if root.find(".//nui-media") is not None:
        publicationid = root.find(".//nui-media").get('publicationid')
        videoid = root.find(".//nui-media").get('videoid')

        resp4 = session_requests.get(URL_STREAM_JSON % (publicationid, videoid, vrtplayertoken))
        json_parser4 = json.loads(resp4.text)

        if "targetUrls" not in json_parser4:
            plugin.notify('ERROR', plugin.localize(30713))
            return False

        stream_url = None
        for stream_datas in json_parser4['targetUrls']:
            if 'hls' in stream_datas['type']:
                stream_url = stream_datas['url']

        if stream_url is None:
            return False

        if download_mode:
            return download.download_video(stream_url)
        return stream_url

    return False


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.post(URL_TOKEN_LIVE, max_age=-1)
    json_parser_token = resp.json()
    resp2 = urlquick.get(URL_LIVE %
                         (item_id, json_parser_token["vrtPlayerToken"]),
                         max_age=-1)
    json_parser_stream_data = resp2.json()

    if "code" in json_parser_stream_data:
        if json_parser_stream_data["code"] == "INVALID_LOCATION":
            plugin.notify('ERROR', plugin.localize(30713))
        return False

    for target_url in json_parser_stream_data["targetUrls"]:
        if target_url["type"] == "hls_aes":
            return target_url["url"]
        if target_url["type"] == "mpeg_dash" and json_parser_stream_data["drm"]:

            if get_kodi_version() < 18:
                continue

            is_helper = inputstreamhelper.Helper("mpd", drm='widevine')
            if not is_helper.check_inputstream():
                continue

            json_api = urlquick.get(VUPLAY_API_URL).json()

            drm_token = json_parser_stream_data["drm"]
            headers_licence = {'Content-Type': 'text/plain;charset=UTF-8'}
            payload_licence = '{{"token":"{0}","drm_info":[D{{SSM}}],"kid":"{{KID}}"}}'.format(drm_token)
            license_url = json_api.get('drm_providers', {}).get('widevine', {}).get('la_url') + '|%s|%s|'
            licence_key = license_url % (urlencode(headers_licence), quote(payload_licence))

            item = Listitem()
            item.path = target_url["url"]
            item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
            item.property['inputstream.adaptive.manifest_type'] = 'mpd'
            item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            item.property['inputstream.adaptive.license_key'] = licence_key
            item.label = get_selected_item_label()
            item.art.update(get_selected_item_art())
            item.info.update(get_selected_item_info())
            return item

    plugin.notify(plugin.localize(30600), plugin.localize(30716))
    return False
