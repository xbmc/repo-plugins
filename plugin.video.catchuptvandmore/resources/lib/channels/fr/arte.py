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

# TODO
#   List emissions
#   Most recent
#   Most viewed

url_replay = 'https://www.arte.tv/papi/tvguide/videos/' \
             'ARTE_PLUS_SEVEN/%s.json?includeLongRights=true'
# Valid languages: F or D


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)


@common.plugin.cached(common.cache_time)
def list_shows(params):
    shows = []
    emissions_list = []
    categories = {}

    desired_language = common.plugin.get_setting(
        params.channel_id + '.language')

    if desired_language == 'Auto':
        if params.channel_country == 'fr':
            desired_language = 'F'
        elif params.channel_country == 'de':
            desired_language = 'D'
    elif desired_language == 'fr':
        desired_language = 'F'
    elif desired_language == 'de':
        desired_language = 'D'
    else:
        desired_language = 'F'

    file_path = utils.download_catalog(
        url_replay % desired_language,
        '%s_%s.json' % (params.channel_name, desired_language)
    )
    file_replay = open(file_path).read()
    json_parser = json.loads(file_replay)

    for emission in json_parser['paginatedCollectionWrapper']['collection']:
        emission_dict = {}
        emission_dict['duration'] = emission['videoDurationSeconds']
        emission_dict['video_url'] = emission['videoPlayerUrl'].encode('utf-8')
        emission_dict['image'] = emission['programImage'].encode('utf-8')
        try:
            emission_dict['genre'] = emission['genre'].encode('utf-8')
        except:
            emission_dict['genre'] = 'Unknown'
        try:
            emission_dict['director'] = emission['director'].encode('utf-8')
        except:
            emission_dict['director'] = ''
        emission_dict['production_year'] = emission['productionYear']
        emission_dict['program_title'] = emission['VTI'].encode('utf-8')
        try:
            emission_dict['emission_title'] = emission['VSU'].encode('utf-8')
        except:
            emission_dict['emission_title'] = ''

        emission_dict['category'] = emission['VCH'][0]['label'].encode('utf-8')
        categories[emission_dict['category']] = emission_dict['category']
        emission_dict['aired'] = emission['VDA'].encode('utf-8')
        emission_dict['playcount'] = emission['VVI']

        try:
            emission_dict['desc'] = emission['VDE'].encode('utf-8')
        except:
            emission_dict['desc'] = ''

        emissions_list.append(emission_dict)

    with common.plugin.get_storage() as storage:
        storage['emissions_list'] = emissions_list

    for category in categories.keys():

        shows.append({
            'label': category,
            'url': common.plugin.get_url(
                action='channel_entry',
                next='list_videos_cat',
                category=category,
                window_title=category
            ),
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
    with common.plugin.get_storage() as storage:
        emissions_list = storage['emissions_list']

    if params.next == 'list_videos_cat':
        for emission in emissions_list:
            if emission['category'] == params.category:
                if emission['emission_title']:
                    title = emission['program_title'] + ' - [I]' + \
                        emission['emission_title'] + '[/I]'
                else:
                    title = emission['program_title']
                aired = emission['aired'].split(' ')[0]
                aired_splited = aired.split('/')
                day = aired_splited[0]
                mounth = aired_splited[1]
                year = aired_splited[2]
                # date : string (%d.%m.%Y / 01.01.2009)
                # aired : string (2008-12-07)
                date = '.'.join((day, mounth, year))
                aired = '-'.join((year, mounth, day))
                info = {
                    'video': {
                        'title': title,
                        'plot': emission['desc'],
                        'aired': aired,
                        'date': date,
                        'duration': emission['duration'],
                        'year': emission['production_year'],
                        'genre': emission['genre'],
                        'playcount': emission['playcount'],
                        'director': emission['director'],
                        'mediatype': 'tvshow'
                    }
                }

                videos.append({
                    'label': title,
                    'thumb': emission['image'],
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        next='play',
                        url=emission['video_url'],
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
def get_video_url(params):
    file_medias = utils.get_webcontent(
        params.url)
    json_parser = json.loads(file_medias)

    url_auto = ''
    url_hd_plus = ''
    url_hd = ''
    url_sd = ''
    url_sd_minus = ''
    video_streams = json_parser['videoJsonPlayer']['VSR']

    if 'HLS_SQ_1' in video_streams:
        url_auto = video_streams['HLS_SQ_1']['url'].encode('utf-8')

    if 'HTTP_MP4_SQ_1' in video_streams:
        url_hd_plus = video_streams['HTTP_MP4_SQ_1']['url'].encode('utf-8')

    if 'HTTP_MP4_EQ_1' in video_streams:
        url_hd = video_streams['HTTP_MP4_EQ_1']['url'].encode('utf-8')

    if 'HTTP_MP4_HQ_1' in video_streams:
        url_sd = video_streams['HTTP_MP4_HQ_1']['url'].encode('utf-8')

    if 'HTTP_MP4_MQ_1' in video_streams:
        url_sd_minus = video_streams['HTTP_MP4_MQ_1']['url'].encode('utf-8')

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
