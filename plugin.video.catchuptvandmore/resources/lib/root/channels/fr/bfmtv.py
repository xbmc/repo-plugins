# -*- coding: utf-8 -*-
'''
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
'''

import json
import ast
import time
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import resolver
from resources.lib import common


# BFMTV, RMC, ONENET, etc ...
URL_TOKEN = 'http://api.nextradiotv.com/%s-applications/'
# channel

URL_MENU = 'http://www.bfmtv.com/static/static-mobile/bfmtv/' \
           'ios-smartphone/v0/configuration.json'

URL_REPLAY = 'http://api.nextradiotv.com/%s-applications/%s/' \
             'getPage?pagename=replay'
# channel, token

URL_SHOW = 'http://api.nextradiotv.com/%s-applications/%s/' \
           'getVideosList?category=%s&count=100&page=%s'
# channel, token, category, page_number

URL_VIDEO = 'http://api.nextradiotv.com/%s-applications/%s/' \
            'getVideo?idVideo=%s'
# channel, token, video_id

# URL Live
# Channel BFMTV
URL_LIVE_BFMTV = 'http://www.bfmtv.com/mediaplayer/live-video/'

URL_LIVE_BFM_PARIS = 'http://www.bfmtv.com/mediaplayer/live-bfm-paris/'

# Channel BFM Business
URL_LIVE_BFMBUSINESS = 'http://bfmbusiness.bfmtv.com/mediaplayer/live-video/'

# Channel RMC
URL_LIVE_BFM_SPORT = 'http://rmcsport.bfmtv.com/mediaplayer/live-bfm-sport/'

# RMC Decouverte
URL_REPLAY_RMCDECOUVERTE = 'http://rmcdecouverte.bfmtv.com/mediaplayer-replay/'

URL_VIDEO_HTML_RMCDECOUVERTE = 'http://rmcdecouverte.bfmtv.com/'\
                               'mediaplayer-replay/?id=%s'
# VideoId_html

URL_LIVE_RMCDECOUVERTE = 'http://rmcdecouverte.bfmtv.com/mediaplayer-direct/'


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_token(channel_name):
    """Get session token"""
    file_token = utils.get_webcontent(URL_TOKEN % (channel_name))
    token_json = json.loads(file_token)
    return token_json['session']['token'].encode('utf-8')


def channel_entry(params):
    """Entry function of the module"""
    if 'replay_entry' == params.next:
        params.next = "list_shows_1"
        return list_shows(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.channel_name == 'rmcdecouverte':

        file_path = utils.download_catalog(
            URL_REPLAY_RMCDECOUVERTE,
            '%s_replay.html' % (params.channel_name))
        program_html = open(file_path).read()

        program_soup = bs(program_html, 'html.parser')
        videos_soup = program_soup.find_all(
            'article',
            class_='art-c modulx2-5 bg-color-rub0-1 box-shadow relative')
        for video in videos_soup:
            video_id = video.find(
                'figure').find(
                    'a')['href'].split('&', 1)[0].rsplit('=', 1)[1]
            video_img = video.find(
                'figure').find(
                    'a').find('img')['data-original']
            video_titles = video.find(
                'div', class_="art-body"
            ).find('a').find('h2').get_text().encode(
                'utf-8'
            ).replace('\n', ' ').replace('\r', ' ').split(' ')
            video_title = ''
            for i in video_titles:
                video_title = video_title + ' ' + i.strip()

            shows.append({
                'label': video_title,
                'thumb': video_img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='list_videos_1',
                    video_id=video_id,
                    title=video_title,
                    page='1',
                    window_title=video_title
                )
            })

    else:
        if params.next == 'list_shows_1':
            file_path = utils.download_catalog(
                URL_REPLAY % (
                    params.channel_name, get_token(params.channel_name)),
                '%s.json' % (params.channel_name))
            file_categories = open(file_path).read()
            json_categories = json.loads(file_categories)
            json_categories = json_categories['page']['contents'][0]
            json_categories = json_categories['elements'][0]['items']

            for categories in json_categories:
                title = categories['title'].encode('utf-8')
                image_url = categories['image_url'].encode('utf-8')
                category = categories['categories'].encode('utf-8')

                shows.append({
                    'label': title,
                    'thumb': image_url,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        category=category,
                        next='list_videos_1',
                        title=title,
                        page='1',
                        window_title=title
                    )
                })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []

    if params.channel_name == 'rmcdecouverte':
        file_path = utils.download_catalog(
            URL_VIDEO_HTML_RMCDECOUVERTE % (params.video_id),
            '%s_%s_replay.html' % (params.channel_name, params.video_id))
        video_html = open(file_path).read()

        video_soup = bs(video_html, 'html.parser')
        data_video_soup = video_soup.find('div', class_='next-player')

        data_account = data_video_soup['data-account']
        data_video_id = data_video_soup['data-video-id']
        data_player = data_video_soup['data-player']

        json_parser = resolver.get_brightcove_video_json(
            data_account,
            data_player,
            data_video_id)

        video_title = ''
        program_title = ''
        for program in json_parser["tags"]:
            program_title = program.upper() + ' - '
        video_title = program_title + \
            json_parser["name"].encode('utf-8').lower()
        video_img = ''
        for poster in json_parser["poster_sources"]:
            video_img = poster["src"]
        video_plot = json_parser["long_description"].encode('utf-8')
        video_duration = 0
        video_duration = json_parser["duration"] / 1000
        video_url = ''
        for url in json_parser["sources"]:
            if 'type' in url:
                video_url = url["src"].encode('utf-8')

        date_value_list = json_parser["published_at"].split('T')[0].split('-')

        day = date_value_list[2]
        mounth = date_value_list[1]
        year = date_value_list[0]

        date = '.'.join((day, mounth, year))
        aired = '-'.join((year, mounth, day))

        info = {
            'video': {
                'title': video_title,
                'aired': aired,
                'date': date,
                'duration': video_duration,
                'plot': video_plot,
                'year': year,
                'mediatype': 'tvshow'
            }
        }

        download_video = (
            common.GETTEXT('Download'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='download_video',
                module_path=params.module_path,
                module_name=params.module_name,
                video_id=params.video_id) + ')'
        )
        context_menu = []
        context_menu.append(download_video)

        videos.append({
            'label': video_title,
            'thumb': video_img,
            'fanart': video_img,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='play_r',
                video_url=video_url
            ),
            'is_playable': True,
            'info': info,
            'context_menu': context_menu
        })

    else:
        if 'previous_listing' in params:
            videos = ast.literal_eval(params['previous_listing'])

        if params.next == 'list_videos_1':
            file_path = utils.download_catalog(
                URL_SHOW % (
                    params.channel_name,
                    get_token(params.channel_name),
                    params.category,
                    params.page),
                '%s_%s_%s.json' % (
                    params.channel_name,
                    params.category,
                    params.page))
            file_show = open(file_path).read()
            json_show = json.loads(file_show)

            for video in json_show['videos']:
                video_id = video['video'].encode('utf-8')
                video_id_ext = video['id_ext'].encode('utf-8')
                category = video['category'].encode('utf-8')
                title = video['title'].encode('utf-8')
                description = video['description'].encode('utf-8')
                # begin_date = video['begin_date']  # 1486725600,
                image = video['image'].encode('utf-8')
                duration = video['video_duration_ms'] / 1000

                value_date = time.strftime(
                    '%d %m %Y', time.localtime(video["begin_date"]))
                date = str(value_date).split(' ')
                day = date[0]
                mounth = date[1]
                year = date[2]

                date = '.'.join((day, mounth, year))
                aired = '-'.join((year, mounth, day))

                info = {
                    'video': {
                        'title': title,
                        'plot': description,
                        'aired': aired,
                        'date': date,
                        'duration': duration,
                        'year': year,
                        'genre': category,
                        'mediatype': 'tvshow'
                    }
                }

                download_video = (
                    common.GETTEXT('Download'),
                    'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                        action='download_video',
                        module_path=params.module_path,
                        module_name=params.module_name,
                        video_id=video_id) + ')'
                )
                context_menu = []
                context_menu.append(download_video)

                videos.append({
                    'label': title,
                    'thumb': image,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='play_r',
                        video_id=video_id,
                        video_id_ext=video_id_ext
                    ),
                    'is_playable': True,
                    'info': info,
                    'context_menu': context_menu
                })

            # More videos...
            videos.append({
                'label': common.ADDON.get_localized_string(30700),
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    category=params.category,
                    next='list_videos_1',
                    title=title,
                    page=str(int(params.page) + 1),
                    window_title=params.window_title,
                    update_listing=True,
                    previous_listing=str(videos)
                )
            })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_DURATION,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_GENRE,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def start_live_tv_stream(params):
    url_live_data = ''

    if params.channel_name == 'rmcdecouverte':
        url_live_data = URL_LIVE_RMCDECOUVERTE
    elif params.channel_name == 'bfmtv':
        url_live_data = URL_LIVE_BFMTV
    elif params.channel_name == 'bfmparis':
        url_live_data = URL_LIVE_BFM_PARIS
    elif params.channel_name == 'bfmbusiness':
        url_live_data = URL_LIVE_BFMBUSINESS
    elif params.channel_name == 'rmc':
        url_live_data = URL_LIVE_BFM_SPORT

    live_html = utils.get_webcontent(
        url_live_data)

    live_soup = bs(live_html, 'html.parser')
    if params.channel_name == 'rmcdecouverte':
        data_live_soup = live_soup.find(
            'div', class_='next-player')
        data_account = data_live_soup['data-account']
        data_video_id = data_live_soup['data-video-id']
        data_player = data_live_soup['data-player']
    else:
        data_live_soup = live_soup.find(
            'div', class_='BCLvideoWrapper')
        data_account = data_live_soup.find(
            'script')['data-account']
        data_video_id = data_live_soup.find(
            'script')['data-video-id']
        data_player = data_live_soup.find(
            'script')['data-player']

    json_parser = resolver.get_brightcove_video_json(
        data_account,
        data_player,
        data_video_id)

    if json_parser["long_description"]:
        plot = json_parser["long_description"]
        plot = plot.encode('utf-8')

    for url in json_parser["sources"]:
        url_live = url["src"].encode('utf-8')

        params['next'] = 'play_l'
        params['url_live'] = url_live
        return get_video_url(params)


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_l':
        return params.url_live
    elif params.channel_name == 'rmcdecouverte' and params.next == 'play_r':
        return params.video_url
    elif params.channel_name == 'rmcdecouverte' and \
            params.next == 'download_video':
        return URL_VIDEO_HTML_RMCDECOUVERTE % (params.video_id)
    elif params.channel_name != 'rmcdecouverte' and \
            (params.next == 'play_r' or params.next == 'download_video'):
        file_medias = utils.get_webcontent(
            URL_VIDEO % (
                params.channel_name,
                get_token(params.channel_name), params.video_id))
        json_parser = json.loads(file_medias)

        if params.next == 'download_video':
            return json_parser['video']['long_url'].encode('utf-8')

        video_streams = json_parser['video']['medias']

        desired_quality = common.PLUGIN.get_setting('quality')

        if desired_quality == "DIALOG":
            all_datas_videos_quality = []
            all_datas_videos_path = []

            for datas in video_streams:
                all_datas_videos_quality.append(
                    "Video Height : " + str(datas['frame_height']) +
                    " (Encoding : " + str(datas['encoding_rate']) + ")"
                )
                all_datas_videos_path.append(datas['video_url'])

            seleted_item = common.sp.xbmcgui.Dialog().select(
                common.GETTEXT('Choose video quality'),
                all_datas_videos_quality)

            return all_datas_videos_path[seleted_item].encode('utf-8')

        elif desired_quality == 'BEST':
            # GET LAST NODE (VIDEO BEST QUALITY)
            url_best_quality = ''
            for datas in video_streams:
                url_best_quality = datas['video_url'].encode('utf-8')
            return url_best_quality
        else:
            # DEFAULT VIDEO
            return json_parser['video']['video_url'].encode('utf-8')
