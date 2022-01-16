# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import inputstreamhelper
import urlquick
from codequick import Listitem, Script
from kodi_six import xbmcgui
from random import randint
from resources.lib import download, web_utils
from resources.lib.addon_utils import get_quality_YTDL
from resources.lib.kodi_utils import (INPUTSTREAM_PROP, get_selected_item_art,
                                      get_selected_item_info,
                                      get_selected_item_label)

try:
    from urllib.parse import quote_plus
    from urllib.parse import urlencode
except ImportError:
    from urllib import quote_plus
    from urllib import urlencode

# TO DO
# Quality VIMEO
# Download Mode with Facebook (the video has no audio)

DESIRED_QUALITY = Script.setting['quality']

URL_DAILYMOTION_EMBED = 'http://www.dailymotion.com/embed/video/%s'
# Video_id

URL_VIMEO_BY_ID = 'https://player.vimeo.com/video/%s?byline=0&portrait=0&autoplay=1'
# Video_id

URL_FACEBOOK_BY_ID = 'https://www.facebook.com/allocine/videos/%s'
# Video_id

URL_YOUTUBE = 'https://www.youtube.com/embed/%s?&autoplay=0'
# Video_id

URL_BRIGHTCOVE_POLICY_KEY = 'http://players.brightcove.net/%s/%s_default/index.min.js'
# AccountId, PlayerId

URL_BRIGHTCOVE_VIDEO_JSON = 'https://edge.api.brightcove.com/'\
                            'playback/v1/accounts/%s/videos/%s'
# AccountId, VideoId

URL_MTVNSERVICES_STREAM = 'https://media-utils.mtvnservices.com/services/' \
                          'MediaGenerator/%s?&format=json&acceptMethods=hls'
# videoURI

URL_MTVNSERVICES_STREAM_ACCOUNT = 'https://media-utils.mtvnservices.com/services/' \
                                  'MediaGenerator/%s?&format=json&acceptMethods=hls' \
                                  '&accountOverride=%s'
# videoURI, accountOverride

URL_MTVNSERVICES_STREAM_ACCOUNT_EP = 'https://media-utils.mtvnservices.com/services/' \
                                     'MediaGenerator/%s?&format=json&acceptMethods=hls' \
                                     '&accountOverride=%s&ep=%s'
# videoURI, accountOverride, ep

URL_FRANCETV_PROGRAM_INFO = 'https://player.webservices.francetelevisions.fr/v1/videos/%s?country_code=%s&device_type=desktop&browser=chrome'
# VideoId

URL_FRANCETV_HDFAUTH_URL = 'https://hdfauthftv-a.akamaihd.net/esi/TA?format=json&url=%s'
# Url

URL_DAILYMOTION_EMBED_2 = 'https://www.dailymotion.com/player/metadata/video/%s?integration=inline&GK_PV5_NEON=1'

URL_REPLAY_ARTE = 'https://api.arte.tv/api/player/v2/config/%s/%s'
# desired_language, videoid


def get_stream_default(plugin,
                       video_url,
                       download_mode=False):
    if download_mode:
        return download.download_video(video_url)

    quality = get_quality_YTDL(download_mode=download_mode)
    return plugin.extract_source(video_url, quality)


# Kaltura Part
def get_stream_kaltura(plugin,
                       video_url,
                       download_mode=False):
    return get_stream_default(plugin, video_url, download_mode)


# DailyMotion Part
def get_stream_dailymotion(plugin,
                           video_id,
                           download_mode=False):

    url_dailymotion = URL_DAILYMOTION_EMBED % video_id
    return get_stream_default(plugin, url_dailymotion, download_mode)
    # Code to reactivate when youtubedl is KO for dailymotion
    # if download_mode:
    #     return False
    # url_dmotion = URL_DAILYMOTION_EMBED_2 % (video_id)
    # resp = urlquick.get(url_dmotion, max_age=-1)
    # json_parser = json.loads(resp.text)

    # if "qualities" not in json_parser:
    #     plugin.notify('ERROR', plugin.localize(30716))

    # all_datas_videos_path = []
    # if "auto" in json_parser["qualities"]:
    #     all_datas_videos_path.append(json_parser["qualities"]["auto"][0]["url"])
    # if "144" in json_parser["qualities"]:
    #     all_datas_videos_path.append(json_parser["qualities"]["144"][1]["url"])
    # if "240" in json_parser["qualities"]:
    #     all_datas_videos_path.append(json_parser["qualities"]["240"][1]["url"])
    # if "380" in json_parser["qualities"]:
    #     all_datas_videos_path.append(json_parser["qualities"]["380"][1]["url"])
    # if "480" in json_parser["qualities"]:
    #     all_datas_videos_path.append(json_parser["qualities"]["480"][1]["url"])
    # if "720" in json_parser["qualities"]:
    #     all_datas_videos_path.append(json_parser["qualities"]["720"][1]["url"])
    # if "1080" in json_parser["qualities"]:
    #     all_datas_videos_path.append(json_parser["qualities"]["1080"][1]["url"])

    # url_stream = ''
    # for video_path in all_datas_videos_path:
    #     url_stream = video_path

    # manifest = urlquick.get(url_stream, max_age=-1)
    # lines = manifest.text.splitlines()
    # inside_m3u8 = ''
    # for k in range(0, len(lines) - 1):
    #     if 'RESOLUTION=' in lines[k]:
    #         inside_m3u8 = lines[k + 1]
    # return inside_m3u8.split('#cell')[0]


# Vimeo Part
def get_stream_vimeo(plugin,
                     video_id,
                     download_mode=False,
                     referer=None):

    url_vimeo = URL_VIMEO_BY_ID % (video_id)

    if referer is not None:
        html_vimeo = urlquick.get(url_vimeo,
                                  headers={
                                      'User-Agent': web_utils.get_random_ua(),
                                      'Referer': referer
                                  },
                                  max_age=-1)
    else:
        html_vimeo = urlquick.get(
            url_vimeo,
            headers={'User-Agent': web_utils.get_random_ua()},
            max_age=-1)
    json_vimeo = json.loads(
        '{' +
        re.compile('var config \= \{(.*?)\}\;').findall(html_vimeo.text)[0] +
        '}')
    hls_json = json_vimeo["request"]["files"]["hls"]
    default_cdn = hls_json["default_cdn"]
    final_video_url = hls_json["cdns"][default_cdn]["url"]

    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url


# Facebook Part
def get_stream_facebook(plugin,
                        video_id,
                        download_mode=False):
    url_facebook = URL_FACEBOOK_BY_ID % (video_id)
    return get_stream_default(plugin, url_facebook, download_mode)


# Youtube Part
def get_stream_youtube(plugin, video_id, download_mode=False):
    url_youtube = URL_YOUTUBE % video_id
    return get_stream_default(plugin, url_youtube, download_mode)


# BRIGHTCOVE Part
def get_brightcove_policy_key(data_account, data_player):
    """Get policy key"""
    file_js = urlquick.get(URL_BRIGHTCOVE_POLICY_KEY %
                           (data_account, data_player))
    return re.compile(r'policyKey\:\"(.*?)\"').findall(file_js.text)[0]


def get_brightcove_video_json(plugin,
                              data_account,
                              data_player,
                              data_video_id,
                              download_mode=False):

    # Method to get JSON from 'edge.api.brightcove.com'
    resp = urlquick.get(
        URL_BRIGHTCOVE_VIDEO_JSON % (data_account, data_video_id),
        headers={
            'User-Agent':
            web_utils.get_random_ua(),
            'Accept':
            'application/json;pk=%s' %
            (get_brightcove_policy_key(data_account, data_player)),
            'X-Forwarded-For':
            plugin.setting.get_string('header_x-forwarded-for')
        })
    json_parser = json.loads(resp.text)

    video_url = ''
    if 'sources' in json_parser:
        for url in json_parser["sources"]:
            if 'src' in url:
                if 'm3u8' in url["src"]:
                    video_url = url["src"]
    else:
        if json_parser[0]['error_code'] == "ACCESS_DENIED":
            plugin.notify('ERROR', plugin.localize(30713))
            return False

    if video_url == '':
        return False

    if download_mode:
        return download.download_video(video_url)
    return video_url


# MTVN Services Part
def get_mtvnservices_stream(plugin,
                            video_uri,
                            download_mode=False,
                            account_override=None,
                            ep=None):

    if account_override is not None and ep is not None:
        json_video_stream = urlquick.get(URL_MTVNSERVICES_STREAM_ACCOUNT_EP %
                                         (video_uri, account_override, ep),
                                         max_age=-1)
    elif account_override is not None:
        json_video_stream = urlquick.get(URL_MTVNSERVICES_STREAM_ACCOUNT %
                                         (video_uri, account_override),
                                         max_age=-1)
    else:
        json_video_stream = urlquick.get(URL_MTVNSERVICES_STREAM % video_uri,
                                         max_age=-1)

    json_video_stream_parser = json.loads(json_video_stream.text)
    if 'rendition' not in json_video_stream_parser["package"]["video"]["item"][
            0]:
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    video_url = json_video_stream_parser["package"]["video"]["item"][0][
        "rendition"][0]["src"]
    if download_mode:
        return download.download_video(video_url)
    return video_url


# FranceTV Part
# FranceTV, FranceTV Sport, France Info, ...
def get_francetv_video_stream(plugin,
                              id_diffusion,
                              download_mode=False):

    geoip_value = web_utils.geoip()
    if not geoip_value:
        geoip_value = 'FR'
    resp = urlquick.get(URL_FRANCETV_PROGRAM_INFO % (id_diffusion, geoip_value),
                        max_age=-1)
    json_parser = resp.json()

    if 'video' not in json_parser:
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    all_video_datas = []
    video_datas = json_parser['video']
    # Implementer Caption (found case)
    # Implement DRM (found case)
    if video_datas['drm'] is not None:
        all_video_datas.append((video_datas['format'], video_datas['drm'], video_datas['token']))
    else:
        all_video_datas.append((video_datas['format'], None, video_datas['token']))

    url_selected = all_video_datas[0][2]
    if 'hls' in all_video_datas[0][0]:
        json_parser2 = json.loads(
            urlquick.get(url_selected, max_age=-1).text)
        final_video_url = json_parser2['url']
        if download_mode:
            return download.download_video(final_video_url)
        return final_video_url + '|X-Forwarded-For=' + '2.' + str(randint(0, 15)) + '.' + str(randint(0, 255)) + '.' + str(randint(0, 255)) + '&User-Agent=' + web_utils.get_random_ua()

    if 'dash' in all_video_datas[0][0]:

        is_helper = inputstreamhelper.Helper('mpd')
        if not is_helper.check_inputstream():
            return False

        item = Listitem()
        item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())

        if all_video_datas[0][1]:
            if download_mode:
                xbmcgui.Dialog().ok(plugin.localize(14116), plugin.localize(30603))
                return False
            item.path = video_datas['url']
            token_request = json.loads('{"id": "%s", "drm_type": "%s", "license_type": "%s"}' % (id_diffusion, video_datas['drm_type'], video_datas['license_type']))
            token = urlquick.post(video_datas['token'], json=token_request).json()['token']
            license_request = '{"token": "%s", "drm_info": [D{SSM}]}' % token
            license_key = 'https://widevine-proxy.drm.technology/proxy|Content-Type=application%%2Fjson|%s|' % quote_plus(license_request)
            item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            item.property['inputstream.adaptive.license_key'] = license_key
        else:
            headers = {
                'User-Agent': web_utils.get_random_ua(),
                # 2.0.0.0 -> 2.16.0.255 are french IP addresses, see https://lite.ip2location.com/france-ip-address-ranges
                'X-Forwarded-For': '2.' + str(randint(0, 15)) + '.' + str(randint(0, 255)) + '.' + str(randint(0, 255)),
            }
            stream_headers = urlencode(headers)
            json_parser2 = json.loads(urlquick.get(url_selected, headers=headers, max_age=-1).text)
            resp3 = urlquick.get(json_parser2['url'], headers=headers, max_age=-1, allow_redirects=False)
            location_url = resp3.headers['location']
            item.path = location_url
            item.property['inputstream.adaptive.stream_headers'] = stream_headers
            if download_mode:
                return download.download_video(item.path)
        return item

    # Return info the format is not known
    return False


def get_francetv_live_stream(plugin, live_id):
    geoip_value = web_utils.geoip()
    if not geoip_value:
        geoip_value = 'FR'

    # Move Live TV on the new API
    json_parser_liveId = json.loads(
        urlquick.get(URL_FRANCETV_PROGRAM_INFO % (live_id, geoip_value),
                     max_age=-1).text)['video']

    try:
        final_url = json_parser_liveId['url']
    except:
        return None

    json_parser2 = json.loads(urlquick.get(URL_FRANCETV_HDFAUTH_URL % (final_url), max_age=-1).text)
    return json_parser2['url'] + '|User-Agent=%s' % web_utils.get_random_ua()


# Arte Part
def get_arte_video_stream(plugin,
                          desired_language,
                          video_id,
                          download_mode=False):

    token = 'MzYyZDYyYmM1Y2Q3ZWRlZWFjMmIyZjZjNTRiMGY4MzY4NzBhOWQ5YjE4MGQ1NGFiODJmOTFlZDQwN2FkOTZjMQ'
    headers = {
        'Authorization': 'Bearer %s' % token
    }
    url = URL_REPLAY_ARTE % (desired_language, video_id)
    j = urlquick.get(url, headers=headers).json()

    all_streams_label = []
    all_streams_url = []

    for stream in j['data']['attributes']['streams']:
        try:
            all_streams_label.append(stream['versions'][0]['label'])
        except Exception:
            all_streams_label.append('Stream ' + str(len(all_streams_label)))
        all_streams_url.append(stream['url'])
    url_selected = ''

    if len(all_streams_url) == 1:
        url_selected = all_streams_url[0]
    else:
        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(30709),
            all_streams_label)
        if seleted_item > -1:
            url_selected = all_streams_url[seleted_item]
        else:
            return False

    if download_mode:
        return download.download_video(url_selected)

    return url_selected
