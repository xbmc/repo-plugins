# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

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
from resources.lib import utils
from resources.lib import common

authorization_key = 'Bearer OTE3NjJhOTYwNzQzNWY0MGE0OGI5MGQ0YmVm' \
                    'MWY2Y2JiYzc5NDQzY2IxMmYxYjQ0NDVlYmEyOTBmYjVkMDg3OQ'

headers = {'Authorization': authorization_key}

url_categories = 'https://api-cdn.arte.tv/api/opa/v2/categories?' \
                 'language=%s&limit=100&sort=order'
# Valid languages list : fr|de|en|es|pl


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_URL(params)


@common.plugin.cached(common.cache_time)
def list_shows(params):
    shows = []

    disered_language = common.plugin.get_setting(
        params.channel_id + '.language')

    if disered_language == 'Auto':
        disered_language = params.channel_country

    file_path = utils.download_catalog(
        url_categories % disered_language,
        '%s.json' % params.channel_name,
        specific_headers=headers)
    file_categories = open(file_path).read()
    json_parser = json.loads(file_categories)

    for category in json_parser['categories']:
        label = category['label'].encode('utf-8')
        desc = category['description'].encode('utf-8')
        href = category['links']['videos']['href'].encode('utf-8')
        code = category['code'].encode('utf-8')

        info = {
            'video': {
                'title': label,
                'plot': desc
            }
        }

        shows.append({
            'label': label,
            'url': common.plugin.get_url(
                action='channel_entry',
                code=code,
                href=href,
                next='list_videos',
                title=label
            ),
            'info': info
        })

    return common.plugin.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )


@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []

    params_url = {
        'geoblockingZone': 'EUR_DE_FR,ALL,SAT,DE_FR',
        'imageSize': '1920x1080,625x224,940x530,720x406,400x225',
        'kind': 'SHOW',
        'limit': '100',
        'platform': 'ARTEPLUS7',
        'sort': '-broadcastBegin',
        'videoLibrary': 'true'
    }
    file_path = utils.download_catalog(
        params.href,
        '%s.json' % (params.channel_name + params.code),
        specific_headers=headers,
        params=params_url)
    file_shows = open(file_path).read()
    json_parser = json.loads(file_shows)

    for video in json_parser['videos']:
        title = video['title'].encode('utf-8')
        subtitle = ''
        if video['subtitle'] is not None:
            subtitle = video['subtitle'].encode('utf-8')

        original_title = video['originalTitle'].encode('utf-8')
        plotoutline = ''
        if video['shortDescription'] is not None:
            plotoutline = video['shortDescription'].encode('utf-8')
        plot = ''
        if video['fullDescription'] is not None:
            plot = video['fullDescription'].encode('utf-8')
        duration = video['durationSeconds']
        year_prod = video['productionYear']
        genre = video['genrePresse'].encode('utf-8')
        season = video['season']
        episode = video['episode']
        total_episodes = video['totalEpisodes']
        href = video['links']['videoStreams']['href'].encode('utf-8')
        views = video['views']
        director = video['director']
        aired = video['arteSchedulingDay']  # year-mounth-day
        day = aired.split('-')[2]
        mounth = aired.split('-')[1]
        year = aired.split('-')[0]
        date = '.'.join((day, mounth, year))
        fanart = video['mainImage']['url'].encode('utf-8')
        thumb = video['mainImage']['alternateResolutions'][1]['url'].encode('utf-8')

        if subtitle:
            title = title + ' - [I]' + subtitle + '[/I]'

        info = {
            'video': {
                'title': title,
                'originaltitle': original_title,
                'plot': plot,
                'plotoutline': plotoutline,
                'aired': aired,
                'date': date,
                'duration': duration,
                'year': year_prod,
                'genre': genre,
                'season': season,
                'episode': episode,
                'playcount': views,
                'director': director,
                'mediatype': 'tvshow'
            }
        }

        videos.append({
            'label': title,
            'fanart': fanart,
            'thumb': thumb,
            'url': common.plugin.get_url(
                action='channel_entry',
                next='play',
                href=href,
            ),
            'is_playable': True,
            'info': info
        })

    return common.plugin.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_DURATION,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_GENRE,
            common.sp.xbmcplugin.SORT_METHOD_PLAYCOUNT,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows')


@common.plugin.cached(common.cache_time)
def get_video_URL(params):
    file_medias = utils.get_webcontent(
        params.href,
        specific_headers=headers)
    json_parser = json.loads(file_medias)

    url_auto = ''
    url_hd_plus = ''
    url_hd = ''
    url_sd = ''
    url_sd_minus = ''
    for video_stream in json_parser['videoStreams']:
        if video_stream['audioSlot'] == 1:
            if video_stream['quality'] == 'AQ' or \
                    video_stream['quality'] == 'XQ':
                url_auto = video_stream['url'].encode('utf-8')

            elif video_stream['quality'] == 'SQ' and \
                    video_stream['mediaType'] == 'mp4' and \
                    video_stream['protocol'] == 'HTTP':
                url_hd_plus = video_stream['url'].encode('utf-8')

            elif video_stream['quality'] == 'EQ' and \
                    video_stream['mediaType'] == 'mp4' and \
                    video_stream['protocol'] == 'HTTP':
                url_hd = video_stream['url'].encode('utf-8')

            elif video_stream['quality'] == 'HQ' and \
                    video_stream['mediaType'] == 'mp4' and \
                    video_stream['protocol'] == 'HTTP':
                url_sd = video_stream['url'].encode('utf-8')

            elif video_stream['quality'] == 'MQ' and \
                    video_stream['mediaType'] == 'mp4' and \
                    video_stream['protocol'] == 'HTTP':
                url_sd_minus = video_stream['url'].encode('utf-8')

    desired_quality = common.plugin.get_setting(
        params.channel_id + '.quality')

    if desired_quality == 'Auto' and url_auto:
        return url_auto

    if desired_quality == 'HD+' and url_hd_plus:
        return url_hd_plus
    elif url_hd:
        return url_hd

    if desired_quality == 'HD' and url_hd:
        return url_hd
    elif url_hd_plus:
        return url_hd_plus

    if desired_quality == 'SD' and url_sd:
        return url_sd
    elif url_sd_minus:
        return url_sd_minus

    if desired_quality == 'SD-' and url_sd_minus:
        return url_sd_minus
    elif url_sd:
        return url_sd

    return url_auto
