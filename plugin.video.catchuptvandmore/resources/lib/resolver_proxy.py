# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re
try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

import inputstreamhelper
from codequick import Script, Listitem
from kodi_six import xbmcgui
import urlquick

from resources.lib import download, web_utils
from resources.lib.addon_utils import get_quality_YTDL
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP


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

URL_FRANCETV_LIVE_PROGRAM_INFO = 'https://sivideo.webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/?idDiffusion=%s'
# VideoId

URL_FRANCETV_CATCHUP_PROGRAM_INFO = 'https://player.webservices.francetelevisions.fr/v1/videos/%s?country_code=%s&device_type=desktop&browser=chrome'
# VideoId

URL_FRANCETV_HDFAUTH_URL = 'https://hdfauthftv-a.akamaihd.net/esi/TA?format=json&url=%s'
# Url

URL_DAILYMOTION_EMBED_2 = 'https://www.dailymotion.com/player/metadata/video/%s?integration=inline&GK_PV5_NEON=1'

URL_REPLAY_ARTE = 'https://api.arte.tv/api/player/v1/config/%s/%s'
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
    resp = urlquick.get(URL_FRANCETV_CATCHUP_PROGRAM_INFO % (id_diffusion, geoip_value),
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
        return final_video_url

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
            json_parser2 = json.loads(urlquick.get(url_selected, max_age=-1).text)
            item.path = json_parser2['url']
            if download_mode:
                return download.download_video(item.path)
        return item

    # Return info the format is not known
    return False


def get_francetv_live_stream(plugin, live_id):

    # Move Live TV on the new API
    json_parser_liveId = json.loads(
        urlquick.get(URL_FRANCETV_LIVE_PROGRAM_INFO % live_id,
                     max_age=-1).text)

    final_url = ''
    geoip_value = web_utils.geoip()
    if not geoip_value:
        geoip_value = 'FR'
    for video in json_parser_liveId['videos']:
        if 'format' not in video:
            continue

        if 'hls_v' not in video['format'] and video['format'] != 'hls':
            continue

        if video['geoblocage'] is not None:
            for value_geoblocage in video['geoblocage']:
                if geoip_value == value_geoblocage:
                    final_url = video['url']
        else:
            final_url = video['url']

    if final_url == '':
        return None

    json_parser2 = json.loads(urlquick.get(URL_FRANCETV_HDFAUTH_URL % (final_url), max_age=-1).text)

    return json_parser2['url'] + '|User-Agent=%s' % web_utils.get_random_ua()


# Arte Part
def get_arte_video_stream(plugin,
                          desired_language,
                          video_id,
                          download_mode=False):

    resp = urlquick.get(URL_REPLAY_ARTE % (desired_language, video_id))
    json_parser = json.loads(resp.text)

    url_selected = ''
    stream_datas = json_parser['videoJsonPlayer']['VSR']

    if DESIRED_QUALITY == "DIALOG":
        all_datas_videos_quality = []
        all_datas_videos_path = []

        for video in stream_datas:
            if not video.find("HLS"):
                datas = json_parser['videoJsonPlayer']['VSR'][video]
                all_datas_videos_quality.append(datas['mediaType'] + " (" +
                                                datas['versionLibelle'] + ")")
                all_datas_videos_path.append(datas['url'])

        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(30709),
            all_datas_videos_quality)
        if seleted_item > -1:
            url_selected = all_datas_videos_path[seleted_item]
        else:
            return False

    elif DESIRED_QUALITY == "BEST":
        url_selected = stream_datas['HTTPS_SQ_1']['url']
    else:
        url_selected = stream_datas['HTTPS_HQ_1']['url']

    if download_mode:
        return download.download_video(url_selected)

    return url_selected
