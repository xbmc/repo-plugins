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

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

# TO DO
#   List emissions
#   Most recent
#   Most viewed

URL_REPLAY = 'https://www.arte.tv/papi/tvguide/videos/' \
             'ARTE_PLUS_SEVEN/%s.json?includeLongRights=true'
# Langue, ...

URL_LIVE_ARTE = 'https://api.arte.tv/api/player/v1/livestream/%s'
# Langue, ...

def channel_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'live' in params.next:
        return list_live(params)
    elif 'play' in params.next:
        return get_video_url(params)
    return None

@common.PLUGIN.cached(common.CACHE_TIME)
def root(params):
    """Add Replay and Live in the listing"""
    modes = []

    # Add Replay
    modes.append({
        'label' : 'Replay',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='list_shows_1',
            category='%s Replay' % params.channel_name.upper(),
            window_title='%s Replay' % params.channel_name.upper()
        ),
    })

    modes.append({
        'label' : 'Live TV',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='live_cat',
            category='%s Live TV' % params.channel_name.upper(),
            window_title='%s Live TV' % params.channel_name.upper()
        ),
    })

    return common.PLUGIN.create_listing(
        modes,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
    )

@common.PLUGIN.cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []
    emissions_list = []
    categories = {}

    desired_language = common.PLUGIN.get_setting(
        params.channel_id + '.language')

    if desired_language == 'DE':
        desired_language = 'D'
    else:
        desired_language = 'F'

    file_path = utils.download_catalog(
        URL_REPLAY % desired_language,
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

    with common.PLUGIN.get_storage() as storage:
        storage['emissions_list'] = emissions_list

    for category in categories.keys():

        shows.append({
            'label': category,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next='list_videos_cat',
                category=category,
                window_title=category
            ),
        })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )


@common.PLUGIN.cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []
    with common.PLUGIN.get_storage() as storage:
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

                # Nouveau pour ajouter le menu pour télécharger la vidéo
                context_menu = []
                download_video = (
                    _('Download'),
                    'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                        action='download_video',
                        url=emission['video_url']) + ')'
                )
                context_menu.append(download_video)
                # Fin

                videos.append({
                    'label': title,
                    'thumb': emission['image'],
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        next='play_r',
                        url=emission['video_url'],
                    ),
                    'is_playable': True,
                    'info': info,
                    'context_menu': context_menu  #  A ne pas oublier pour ajouter le bouton "Download" à chaque vidéo
                })

        return common.PLUGIN.create_listing(
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

@common.PLUGIN.cached(common.CACHE_TIME)
def list_live(params):
    """Build live listing"""
    lives = []

    desired_language = common.PLUGIN.get_setting(
        params.channel_id + '.language')

    if desired_language == 'DE':
        desired_language = 'de'
    else:
        desired_language = 'fr'

    url_live = ''

    file_path = utils.download_catalog(
        URL_LIVE_ARTE % desired_language,
        '%s_%s_live.json' % (params.channel_name, desired_language)
    )
    file_live = open(file_path).read()
    json_parser = json.loads(file_live)

    title = json_parser["videoJsonPlayer"]["VTI"].encode('utf-8')
    img = json_parser["videoJsonPlayer"]["VTU"]["IUR"].encode('utf-8')
    plot = ''
    if 'V7T' in json_parser["videoJsonPlayer"]:
        plot = json_parser["videoJsonPlayer"]["V7T"].encode('utf-8')
    elif 'VDE' in json_parser["videoJsonPlayer"]:
        plot = json_parser["videoJsonPlayer"]["VDE"].encode('utf-8')
    duration = 0
    duration = json_parser["videoJsonPlayer"]["videoDurationSeconds"]
    url_live = json_parser["videoJsonPlayer"]["VSR"]["HLS_SQ_1"]["url"]

    info = {
        'video': {
            'title': title,
            'plot': plot,
            'duration': duration
        }
    }

    lives.append({
        'label': title,
        'fanart': img,
        'thumb': img,
        'url' : common.PLUGIN.get_url(
            action='channel_entry',
            next='play_l',
            url=url_live,
        ),
        'is_playable': True,
        'info': info
    })

    return common.PLUGIN.create_listing(
        lives,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )

@common.PLUGIN.cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':
        file_medias = utils.get_webcontent(
            params.url)
        json_parser = json.loads(file_medias)

        url_selected = ''
        video_streams = json_parser['videoJsonPlayer']['VSR']

        desired_quality = common.PLUGIN.get_setting('quality')

        if desired_quality == "DIALOG":
            all_datas_videos = []

            for video in video_streams:
                if not video.find("HLS"):
                        datas = json_parser['videoJsonPlayer']['VSR'][video]
                        new_list_item = common.sp.xbmcgui.ListItem()
                        new_list_item.setLabel(datas['mediaType'] + " (" + datas['versionLibelle'] + ")")
                        new_list_item.setPath(datas['url'])
                        all_datas_videos.append(new_list_item)

            seleted_item = common.sp.xbmcgui.Dialog().select("Choose Stream", all_datas_videos)

            url_selected = all_datas_videos[seleted_item].getPath().encode('utf-8')

        elif desired_quality == "BEST":
            url_selected = video_streams['HTTP_MP4_SQ_1']['url'].encode('utf-8')
        else:
            url_selected = video_streams['HLS_SQ_1']['url'].encode('utf-8')

        return url_selected
    elif params.next == 'play_l':
        return params.url

