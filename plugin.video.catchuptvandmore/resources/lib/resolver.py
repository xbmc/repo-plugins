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

import json
import re
from resources.lib import utils
from resources.lib import common


DESIRED_QUALITY = common.PLUGIN.get_setting('quality')

URL_DAILYMOTION_EMBED = 'http://www.dailymotion.com/embed/video/%s'
# Video_id

URL_VIMEO_BY_ID = 'https://player.vimeo.com/video/%s?autoplay=1'
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

# DailyMotion Part
def get_stream_dailymotion(video_id, isDownloadVideo):

    # Sous Jarvis nous avons ces éléments qui ne fonctionnent pas :
    # * KO for playing m3u8 but MP4 work
    # * Les vidéos au format dailymotion proposé par Allociné
    # * Les directs TV  de PublicSenat, LCP, L"Equipe TV et Numero 23 herbergés par dailymotion.

    url_dmotion = URL_DAILYMOTION_EMBED % (video_id)

    if isDownloadVideo == True:
        return url_dmotion

    html_video = utils.get_webcontent(url_dmotion)
    html_video = html_video.replace('\\', '')

    # Case Jarvis
    if common.sp.xbmc.__version__ == '2.24.0':
        all_url_video = re.compile(
            r'{"type":"video/mp4","url":"(.*?)"').findall(html_video)
        if len(all_url_video) > 0:
            if DESIRED_QUALITY == "DIALOG":
                all_datas_videos_quality = []
                all_datas_videos_path = []
                for datas in all_url_video:
                    datas_quality = re.search(
                        'H264-(.+?)/', datas).group(1)
                    all_datas_videos_quality.append(
                        'H264-' + datas_quality)
                    all_datas_videos_path.append(datas)

                seleted_item = common.sp.xbmcgui.Dialog().select(
                    common.GETTEXT('Choose video quality'), all_datas_videos_quality)

                return all_datas_videos_path[seleted_item].encode('utf-8')
            elif DESIRED_QUALITY == 'BEST':
                # Last video in the Best
                for datas in all_url_video:
                    url = datas
                return url
            else:
                return all_url_video[0]
        # In case some M3U8 work in Jarvis
        else:
            url_video_auto = re.compile(
                r'{"type":"application/x-mpegURL","url":"(.*?)"'
                ).findall(html_video)[0]
            return url_video_auto
    # Case Krypton and newer version
    else:
        url_video_auto = re.compile(
            r'{"type":"application/x-mpegURL","url":"(.*?)"'
            ).findall(html_video)[0]
        m3u8_video_auto = utils.get_webcontent(url_video_auto)
        # Case no absolute path in the m3u8
        # (TO DO how to build the absolute path ?) add quality after
        if 'http' not in  m3u8_video_auto:
            return url_video_auto
        # Case absolute path in the m3u8
        else:
            url = ''
            lines = m3u8_video_auto.splitlines()
            if DESIRED_QUALITY == "DIALOG":
                all_datas_videos_quality = []
                all_datas_videos_path = []
                for k in range(0, len(lines) - 1):
                    if 'RESOLUTION=' in lines[k]:
                        all_datas_videos_quality.append(
                            re.compile(
                            r'RESOLUTION=(.*?),').findall(
                            lines[k])[0])
                        all_datas_videos_path.append(
                            lines[k + 1])
                seleted_item = common.sp.xbmcgui.Dialog().select(
                    common.GETTEXT('Choose video quality'),
                    all_datas_videos_quality)
                return all_datas_videos_path[seleted_item].encode(
                    'utf-8')
            elif DESIRED_QUALITY == 'BEST':
                # Last video in the Best
                for k in range(0, len(lines) - 1):
                    if 'RESOLUTION=' in lines[k]:
                        url = lines[k + 1]
                return url
            else:
                for k in range(0, len(lines) - 1):
                    if 'RESOLUTION=' in lines[k]:
                        url = lines[k + 1]
                    break
                return url

# Vimeo Part
def get_stream_vimeo(video_id, isDownloadVideo):

    url_vimeo = URL_VIMEO_BY_ID % (video_id)

    if isDownloadVideo == True:
        return url_vimeo

    html_vimeo = utils.get_webcontent(url_vimeo)
    json_vimeo = json.loads(re.compile('var t=(.*?);').findall(
        html_vimeo)[0])
    hls_json = json_vimeo["request"]["files"]["hls"]
    default_cdn = hls_json["default_cdn"]
    return hls_json["cdns"][default_cdn]["url"]

# Facebook Part
def get_stream_facebook(video_id, isDownloadVideo):

    url_facebook = URL_FACEBOOK_BY_ID % (video_id)

    if isDownloadVideo == True:
        return url_facebook

    html_facebook = utils.get_webcontent(url_facebook)

    if len(re.compile(
        r'hd_src_no_ratelimit:"(.*?)"').findall(
        html_facebook)) > 0:
        if DESIRED_QUALITY == "DIALOG":
            all_datas_videos_quality = []
            all_datas_videos_path = []
            all_datas_videos_quality.append('SD')
            all_datas_videos_path.append(re.compile(
                r'sd_src_no_ratelimit:"(.*?)"').findall(
                html_facebook)[0])
            all_datas_videos_quality.append('HD')
            all_datas_videos_path.append(re.compile(
                r'hd_src_no_ratelimit:"(.*?)"').findall(
                html_facebook)[0])
            seleted_item = common.sp.xbmcgui.Dialog().select(
                common.GETTEXT('Choose video quality'),
                all_datas_videos_quality)
            return all_datas_videos_path[seleted_item].encode(
                'utf-8')
        elif DESIRED_QUALITY == 'BEST':
            return re.compile(
                r'hd_src_no_ratelimit:"(.*?)"').findall(
                html_facebook)[0]
        else:
            return re.compile(
                r'sd_src_no_ratelimit:"(.*?)"').findall(
                html_facebook)[0]
    else:
        return re.compile(
            r'sd_src_no_ratelimit:"(.*?)"').findall(
            html_facebook)[0]


# Youtube Part
def get_stream_youtube(video_id, isDownloadVideo):
    url_youtube = URL_YOUTUBE % video_id

    if isDownloadVideo is True:
        return url_youtube

    YDStreamExtractor = __import__('YDStreamExtractor')

    quality = 3
    desired_quality = common.PLUGIN.get_setting('quality')
    if desired_quality == "DIALOG":
        all_quality = ['SD', '720p', '1080p', 'Highest available']
        seleted_item = common.sp.xbmcgui.Dialog().select(
            common.GETTEXT('Choose video quality'),
            all_quality)

        if seleted_item == -1:
            quality = 3
        selected_quality_string = all_quality[seleted_item]
        quality_string = {
            'SD': 0,
            '720p': 1,
            '1080p': 2,
            'Highest available': 3
        }
        quality = quality_string[selected_quality_string]

    vid = YDStreamExtractor.getVideoInfo(
        url_youtube,
        quality=quality,
        resolve_redirects=True
    )
    return vid.streamURL()


# BRIGHTCOVE Part
def get_brightcove_policy_key(data_account, data_player):
    """Get policy key"""
    file_js = utils.get_webcontent(
        URL_BRIGHTCOVE_POLICY_KEY % (data_account, data_player))
    return re.compile('policyKey:"(.+?)"').findall(file_js)[0]


def get_brightcove_video_json(data_account, data_player, data_video_id):

    # Method to get JSON from 'edge.api.brightcove.com'
    file_json = utils.download_catalog(
        URL_BRIGHTCOVE_VIDEO_JSON % (data_account, data_video_id),
        '%s_%s_replay.json' % (data_account, data_video_id),
        force_dl=False,
        request_type='get',
        post_dic={},
        random_ua=False,
        specific_headers={'Accept': 'application/json;pk=%s' % (
            get_brightcove_policy_key(data_account, data_player))},
        params={})
    video_json = open(file_json).read()
    json_parser = json.loads(video_json)
    return json_parser
