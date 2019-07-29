# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Script, Listitem

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import cq_utils
from resources.lib import download

import json
import re
import urlquick
import xbmcgui

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

URL_FRANCETV_LIVE_PROGRAM_INFO = 'http://sivideo.webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/?idDiffusion=%s'
# VideoId

URL_FRANCETV_HDFAUTH_URL = 'http://hdfauth.francetv.fr/esi/TA?format=json&url=%s'
# Url


def get_stream_default(plugin,
                       video_url,
                       download_mode=False,
                       video_label=None):
    if download_mode:
        return download.download_video(video_url, video_label)

    quality = cq_utils.get_quality_YTDL(download_mode=download_mode)
    return plugin.extract_source(video_url, quality)


# Kaltura Part
def get_stream_kaltura(plugin,
                       video_url,
                       download_mode=False,
                       video_label=None):
    return get_stream_default(plugin, video_url, download_mode, video_label)


# DailyMotion Part
def get_stream_dailymotion(plugin,
                           video_id,
                           download_mode=False,
                           video_label=None):
    url_dailymotion = URL_DAILYMOTION_EMBED % video_id
    return get_stream_default(plugin, url_dailymotion, download_mode,
                              video_label)


# Vimeo Part
def get_stream_vimeo(plugin,
                     video_id,
                     download_mode=False,
                     video_label=None,
                     referer=None):

    url_vimeo = URL_VIMEO_BY_ID % (video_id)

    if referer is not None:
        html_vimeo = urlquick.get(url_vimeo,
                                  headers={
                                      'User-Agent': web_utils.get_random_ua,
                                      'Referer': referer
                                  },
                                  max_age=-1)
    else:
        html_vimeo = urlquick.get(
            url_vimeo,
            headers={'User-Agent': web_utils.get_random_ua},
            max_age=-1)
    json_vimeo = json.loads(
        '{' +
        re.compile('var config \= \{(.*?)\}\;').findall(html_vimeo.text)[0] +
        '}')
    hls_json = json_vimeo["request"]["files"]["hls"]
    default_cdn = hls_json["default_cdn"]
    final_video_url = hls_json["cdns"][default_cdn]["url"]

    if download_mode:
        return download.download_video(final_video_url, video_label)
    return final_video_url


# Facebook Part
def get_stream_facebook(plugin,
                        video_id,
                        download_mode=False,
                        video_label=None):
    url_facebook = URL_FACEBOOK_BY_ID % (video_id)
    return get_stream_default(plugin, url_facebook, download_mode, video_label)


# Youtube Part
def get_stream_youtube(plugin, video_id, download_mode=False,
                       video_label=None):
    url_youtube = URL_YOUTUBE % video_id
    return get_stream_default(plugin, url_youtube, download_mode, video_label)


# BRIGHTCOVE Part
def get_brightcove_policy_key(data_account, data_player):
    """Get policy key"""
    file_js = urlquick.get(URL_BRIGHTCOVE_POLICY_KEY %
                           (data_account, data_player))
    return re.compile('policyKey:"(.+?)"').findall(file_js.text)[0]


def get_brightcove_video_json(plugin,
                              data_account,
                              data_player,
                              data_video_id,
                              download_mode=False,
                              video_label=None):

    # Method to get JSON from 'edge.api.brightcove.com'
    resp = urlquick.get(
        URL_BRIGHTCOVE_VIDEO_JSON % (data_account, data_video_id),
        headers={
            'User-Agent':
            web_utils.get_random_ua,
            'Accept':
            'application/json;pk=%s' %
            (get_brightcove_policy_key(data_account, data_player))
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
        return download.download_video(video_url, video_label)
    return video_url


# MTVN Services Part
def get_mtvnservices_stream(plugin,
                            video_uri,
                            download_mode=False,
                            video_label=None,
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
        return download.download_video(video_url, video_label)
    return video_url


# FranceTV Part
# FranceTV, FranceTV Sport, France Info, ...
def get_francetv_video_stream(plugin,
                              id_diffusion,
                              item_dict=None,
                              download_mode=False,
                              video_label=None):

    resp = urlquick.get(URL_FRANCETV_LIVE_PROGRAM_INFO % id_diffusion,
                        max_age=-1)
    json_parser = json.loads(resp.text)

    if 'videos' not in json_parser:
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    subtitles = []
    if plugin.setting.get_boolean('active_subtitle'):
        if json_parser['subtitles']:
            subtitles_list = json_parser['subtitles']
            for subtitle in subtitles_list:
                if subtitle['format'] == 'vtt':
                    subtitles.append(subtitle['url'])

    url_selected = ''

    if DESIRED_QUALITY == "DIALOG":
        all_datas_videos_quality = []
        all_datas_videos_path = []

        for video in json_parser['videos']:
            if 'hds' not in video['format']:
                if video['format'] == 'hls_v5_os':
                    all_datas_videos_quality.append("HD")
                else:
                    all_datas_videos_quality.append("SD")
                all_datas_videos_path.append((video['url'], video['drm']))

        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(LABELS['choose_video_quality']),
            all_datas_videos_quality)

        if seleted_item == -1:
            return False

        url_selected = all_datas_videos_path[seleted_item][0]
        drm = all_datas_videos_path[seleted_item][1]

    elif DESIRED_QUALITY == "BEST":
        for video in json_parser['videos']:
            if 'hds' not in video['format']:
                if video['format'] == 'hls_v5_os':
                    url_selected = video['url']
                    drm = video['drm']
                    break
                else:
                    url_selected = video['url']
                    drm = video['drm']
    else:
        for video in json_parser['videos']:
            if 'hds' not in video['format']:
                if video['format'] == 'm3u8-download':
                    url_selected = video['url']
                    drm = video['drm']
                    break
                else:
                    url_selected = video['url']
                    drm = video['drm']

    if drm:
        file_prgm2 = urlquick.get(
            URL_FRANCETV_HDFAUTH_URL % (url_selected),
            headers={'User-Agent': web_utils.get_random_ua},
            max_age=-1)
        json_parser3 = json.loads(file_prgm2.text)
        url_selected = json_parser3['url']
        url_selected = url_selected.replace('.m3u8:', '.m4u9:')

    if url_selected is None:
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    if 'cloudreplayfrancetv' in url_selected:
        file_prgm2 = urlquick.get(
            URL_FRANCETV_HDFAUTH_URL % (url_selected),
            headers={'User-Agent': web_utils.get_random_ua},
            max_age=-1)
        json_parser3 = json.loads(file_prgm2.text)
        url_selected = json_parser3['url']
        if drm:
            url_selected = url_selected.replace('.m3u8:', '.m4u9:')

    final_video_url = url_selected

    if download_mode:
        return download.download_video(final_video_url, video_label)

    if len(subtitles) > 0:
        item = Listitem()
        item.path = final_video_url
        for subtitle in subtitles:
            item.subtitles.append(subtitle)
        item.label = item_dict['label']
        item.info.update(item_dict['info'])
        item.art.update(item_dict['art'])
        return item
    else:
        return final_video_url


def get_francetv_live_stream(plugin, live_id):

    json_parser_liveId = json.loads(
        urlquick.get(URL_FRANCETV_LIVE_PROGRAM_INFO % live_id,
                     max_age=-1).text)
    url_hls_v1 = ''
    url_hls_v5 = ''
    url_hls = ''

    for video in json_parser_liveId['videos']:
        if 'format' in video:
            if 'hls_v1_os' in video['format']:
                url_hls_v1 = video['url']
            if 'hls_v5_os' in video['format']:
                url_hls_v5 = video['url']
            if 'hls' in video['format']:
                url_hls = video['url']

    final_url = ''

    # Case France 3 Région
    if url_hls_v1 == '' and url_hls_v5 == '':
        final_url = url_hls

    if final_url == '' and url_hls_v5 != '':
        final_url = url_hls_v5
    elif final_url == '':
        final_url = url_hls_v1

    json_parser2 = json.loads(
        urlquick.get(URL_FRANCETV_HDFAUTH_URL % (final_url), max_age=-1).text)

    return json_parser2['url']
