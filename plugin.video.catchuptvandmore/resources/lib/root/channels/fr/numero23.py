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
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import resolver
from resources.lib import common


URL_REPLAY = 'http://www.numero23.fr/replay/'

URL_INFO_LIVE_JSON = 'http://www.numero23.fr/wp-content/cache/n23-direct.json'
# Title, DailyMotion Id (Video)


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


CORRECT_MONTH = {
    'janvier': '01',
    'février': '02',
    'mars': '03',
    'avril': '04',
    'mai': '05',
    'juin': '06',
    'juillet': '07',
    'août': '08',
    'septembre': '09',
    'octobre': '10',
    'novembre': '11',
    'décembre': '12'
}


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build shows listing"""
    shows = []
    if params.next == 'list_shows_1':
        file_path = utils.download_catalog(
            URL_REPLAY,
            params.channel_name + '.html')
        root_html = open(file_path).read()
        root_soup = bs(root_html, 'html.parser')

        categories_soup = root_soup.find(
            'div',
            class_='nav-programs'
        )

        for category in categories_soup.find_all('a'):
            category_name = category.find(
                'span').get_text().encode('utf-8').replace(
                '\n', ' ').replace('\r', ' ').rstrip('\r\n')
            category_hash = common.sp.md5(category_name).hexdigest()

            url = category.get('href').encode('utf-8')

            shows.append({
                'label': category_name,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    category_hash=category_hash,
                    next='list_videos_cat',
                    url=url,
                    window_title=category_name,
                    category_name=category_name,
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

    paged = 1
    url_replay_paged = params.url + '&paged=' + str(paged)

    file_path = utils.download_catalog(
        url_replay_paged,
        '%s_%s_%s.html' % (
            params.channel_name, params.category_name, str(paged))
    )
    program_html = open(file_path).read()
    program_soup = bs(program_html, 'html.parser')

    videos_soup = program_soup.find_all('div', class_='program sticky video')

    while len(videos_soup) != 0:
        for video in videos_soup:

            info_video = video.find_all('p')

            video_title = video.find('h3').find(
                'a').get_text().encode('utf-8').replace(
                '\n', ' ').replace('\r', ' ').rstrip(
                '\r\n') + ' - ' + video.find(
                'p', class_="red").get_text().encode(
                'utf-8').replace('\n', ' ').replace('\r', ' ').rstrip('\r\n')
            video_img = video.find(
                'img')['src'].encode('utf-8')
            video_id = video.find(
                'div', class_="player")['data-id-video'].encode('utf-8')
            video_duration = 0
            video_duration_list = str(info_video[3]).replace(
                "<p><strong>", '').replace("</strong></p>", '').split(':')
            if len(video_duration_list) > 2:
                video_duration = int(video_duration_list[0]) * 3600 + \
                    int(video_duration_list[1]) * 60 + \
                    int(video_duration_list[2])
            else:
                video_duration = int(video_duration_list[0]) * 60 + \
                    int(video_duration_list[1])

            # get month and day on the page
            date_list = str(info_video[2]).replace(
                "<p>", '').replace("</p>", '').split(' ')
            day = '00'
            mounth = '00'
            year = '2017'
            if len(date_list) > 3:
                day = date_list[2]
                try:
                    mounth = CORRECT_MONTH[date_list[3]]
                except Exception:
                    mounth = '00'
                # get year ?

            date = '.'.join((day, mounth, year))
            aired = '-'.join((year, mounth, day))

            info = {
                'video': {
                    'title': video_title,
                    'aired': aired,
                    'date': date,
                    'duration': video_duration,
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
                    video_id=video_id) + ')'
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
                    video_id=video_id
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })
        paged = paged + 1

        url_replay_paged = params.url + '&paged=' + str(paged)

        file_path = utils.download_catalog(
            url_replay_paged,
            '%s_%s_%s.html' % (
                params.channel_name, params.category_name, str(paged))
        )
        program_html = open(file_path).read()
        program_soup = bs(program_html, 'html.parser')

        videos_soup = program_soup.find_all(
            'div', class_='program sticky video')

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
        content='tvshows',
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def start_live_tv_stream(params):
    file_path = utils.download_catalog(
        URL_INFO_LIVE_JSON,
        '%s_info_live.json' % (params.channel_name)
    )
    file_info_live = open(file_path).read()
    json_parser = json.loads(file_info_live)

    video_id = json_parser["video"].encode('utf-8')

    # url_live = url_dailymotion_embed % video_id

    params['next'] = 'play_l'
    params['video_id'] = video_id
    return get_video_url(params)


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r':
        return resolver.get_stream_dailymotion(params.video_id, False)
    elif params.next == 'play_l':
        return resolver.get_stream_dailymotion(params.video_id, False)
    elif params.next == 'download_video':
        return resolver.get_stream_dailymotion(params.video_id, True)
