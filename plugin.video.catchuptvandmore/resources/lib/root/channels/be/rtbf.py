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
import time
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common


URL_EMISSIONS_AUVIO = 'https://www.rtbf.be/auvio/emissions'

URL_JSON_EMISSION_BY_ID = 'https://www.rtbf.be/api/media/video?' \
                          'method=getVideoListByEmissionOrdered&args[]=%s'
# emission_id

URL_CATEGORIES = 'https://www.rtbf.be/news/api/menu?site=media'

URL_VIDEO_BY_ID = 'https://www.rtbf.be/auvio/embed/media?id=%s&autoplay=1'
# Video Id

URL_ROOT_IMAGE_RTBF = 'https://ds1.static.rtbf.be'

URL_JSON_LIVE = 'https://www.rtbf.be/api/partner/generic/live/' \
                'planninglist?target_site=media&partner_key=%s'
# partener_key

URL_ROOT_LIVE = 'https://www.rtbf.be/auvio/direct#/'


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
    else:
        return None


def get_partener_key(params):
    """Get Partener Key"""
    file_path_root_live = utils.download_catalog(
        URL_ROOT_LIVE,
        '%s_root_live.html' % params.channel_name,
    )
    html_root_live = open(file_path_root_live).read()

    list_js_files = re.compile(
        r'<script type="text\/javascript" src="(.*?)">'
    ).findall(html_root_live)

    partener_key_value = ''
    i = 0

    for js_file in list_js_files:
        # Get partener key
        file_path_js = utils.download_catalog(
            js_file,
            '%s_partener_key_%s.js' % (params.channel_name, str(i)),
        )
        partener_key_js = open(file_path_js).read()

        partener_key = re.compile(
            'partner_key: \'(.+?)\'').findall(partener_key_js)
        if len(partener_key) > 0:
            partener_key_value = partener_key[0]
        i = i + 1

    return partener_key_value


def format_hours(date):
    """Format hours"""
    date_list = date.split('T')
    date_hour = date_list[1][:5]
    return date_hour


def format_day(date):
    """Format day"""
    date_list = date.split('T')
    date_dmy = date_list[0].replace('-', '/')
    return date_dmy


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.next == 'list_shows_1':

        emission_title = 'Émissions'

        shows.append({
            'label': emission_title,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                emission_title=emission_title,
                action='replay_entry',
                next='list_shows_2',
                window_title=emission_title
            )
        })

        file_path = utils.get_webcontent(URL_CATEGORIES)
        categories_json = json.loads(file_path)

        for category in categories_json["item"]:
            if category["@attributes"]["id"] == 'category':
                for category_sub in category["item"]:
                    if 'category-' in category_sub["@attributes"]["id"]:
                        category_name = category_sub["@attributes"]["name"]
                        category_url = category_sub["@attributes"]["url"]

                        shows.append({
                            'label': category_name,
                            'url': common.PLUGIN.get_url(
                                module_path=params.module_path,
                                module_name=params.module_name,
                                action='replay_entry',
                                category_url=category_url,
                                category_name=category_name,
                                next='list_videos_categorie',
                                window_title=category_name
                            )
                        })

    elif params.next == 'list_shows_2':

        file_path = utils.download_catalog(
            URL_EMISSIONS_AUVIO,
            'url_emissions_auvio.html')
        emissions_html = open(file_path).read()
        emissions_soup = bs(emissions_html, 'html.parser')
        list_emissions = emissions_soup.find_all(
            'article', class_="rtbf-media-item col-xxs-12 col-xs-6 col-md-4 col-lg-3 ")

        for emission in list_emissions:

            emission_id = emission.get('data-id')
            emission_title = emission.find('h4').get_text().encode('utf-8')

            shows.append({
                'label': emission_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    emission_title=emission_title,
                    action='replay_entry',
                    emission_id=emission_id,
                    next='list_videos_emission',
                    window_title=emission_title
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

    if params.next == 'list_videos_emission':

        file_path = utils.download_catalog(
            URL_JSON_EMISSION_BY_ID % params.emission_id,
            'url_videos_emission_%s.html' % params.emission_id)
        videos_json = open(file_path).read()
        videos_jsonparser = json.loads(videos_json)

        for video in videos_jsonparser['data']:

            if video["subtitle"]:
                title = video["title"].encode('utf-8') + \
                    ' - ' + video["subtitle"].encode('utf-8')
            else:
                title = video["title"].encode('utf-8')
            img = URL_ROOT_IMAGE_RTBF + video["thumbnail"]["full_medium"]
            url_video = video["urlHls"]
            plot = ''
            if video["description"]:
                plot = video["description"].encode('utf-8')
            duration = 0
            duration = video["durations"]

            value_date = time.strftime(
                '%d %m %Y', time.localtime(video["liveFrom"]))
            date = str(value_date).split(' ')
            day = date[0]
            mounth = date[1]
            year = date[2]

            date = '.'.join((day, mounth, year))
            aired = '-'.join((year, mounth, day))

            info = {
                'video': {
                    'title': title,
                    'plot': plot,
                    # 'episode': episode_number,
                    # 'season': season_number,
                    # 'rating': note,
                    'aired': aired,
                    'date': date,
                    'duration': duration,
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
                    url_video=url_video) + ')'
            )
            context_menu = []
            context_menu.append(download_video)

            videos.append({
                'label': title,
                'thumb': img,
                'fanart': img,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='play_r',
                    url_video=url_video
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

    elif params.next == 'list_videos_categorie':

        file_path = utils.get_webcontent(params.category_url)
        episodes_soup = bs(file_path, 'html.parser')
        list_episodes = episodes_soup.find_all('article')

        for episode in list_episodes:

            if episode.get('data-type') == 'media':
                if episode.find('h4'):
                    title = episode.find('h3').find(
                        'a').get('title') + ' - ' + \
                        episode.find('h4').get_text()
                else:
                    title = episode.find('h3').find('a').get('title')
                duration = 0
                video_id = episode.get('data-id')
                all_images = episode.find('img').get(
                    'data-srcset').split(',')
                for image in all_images:
                    img = image.split(' ')[0]

                info = {
                    'video': {
                        'title': title,
                        # 'plot': plot,
                        # 'episode': episode_number,
                        # 'season': season_number,
                        # 'rating': note,
                        # 'aired': aired,
                        # 'date': date,
                        'duration': duration,
                        # 'year': year,
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
                    'thumb': img,
                    'fanart': img,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='play_r_categorie',
                        video_id=video_id
                    ),
                    'is_playable': True,
                    'info': info,
                    'context_menu': context_menu
                })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_DATE
        ),
        content='tvshows',
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_live_item(params):
    lives = []

    title = ''
    # subtitle = ' - '
    plot = ''
    duration = 0
    img = ''
    url_live = ''

    file_path = utils.download_catalog(
        URL_JSON_LIVE % (get_partener_key(params)),
        '%s_live.json' % (params.channel_name))
    live_json = open(file_path).read()
    live_jsonparser = json.loads(live_json)

    # channel_live_in_process = False

    for live in live_jsonparser:

        if type(live["channel"]) is dict:
            live_channel = live["channel"]["label"]
        else:
            live_channel = 'Exclu Auvio'

        start_date_value = format_hours(live["start_date"])
        end_date_value = format_hours(live["end_date"])
        day_value = format_day(live["start_date"])

        title = live_channel + " - [I]" + live["title"] + \
            ' - ' + day_value + ' - ' + start_date_value + \
            '-' + end_date_value + "[/I]"

        url_live = ''
        if live["url_streaming"]:
            url_live = live["url_streaming"]["url_hls"]
        plot = live["description"].encode('utf-8')
        img = live["images"]["illustration"]["16x9"]["1248x702"]

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
            'url': common.PLUGIN.get_url(
                action='start_live_tv_stream',
                next='play_l',
                module_name=params.module_name,
                module_path=params.module_path,
                url_live=url_live,
            ),
            'is_playable': True,
            'info': info
        })

    return lives


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_l':
        return params.url_live
    elif params.next == 'play_r_categorie':
        file_path = utils.get_webcontent(
            URL_VIDEO_BY_ID % params.video_id)
        data_stream = re.compile('data-media=\"(.*?)\"').findall(
            file_path)[0]
        data_stream = data_stream.replace('&quot;', '"')
        data_stream_json = json.loads(data_stream)
        return data_stream_json["urlHls"]
    elif params.next == 'play_r':
        return params.url_video
