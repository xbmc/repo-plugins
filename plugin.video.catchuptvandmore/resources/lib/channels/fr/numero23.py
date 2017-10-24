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

import re
import json
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

# TO DO
# Get more info Live TV (picture, plot)
# Get year from Replay

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

URL_REPLAY = 'http://www.numero23.fr/replay/'

URL_INFO_LIVE_JSON = 'http://www.numero23.fr/wp-content/cache/n23-direct.json'
# Title, DailyMotion Id (Video)

URL_DAILYMOTION_EMBED = 'http://www.dailymotion.com/embed/video/%s'
# Video_id


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
def root(params):
    """Add Replay and Live in the listing"""
    modes = []

    # Add Replay
    modes.append({
        'label': 'Replay',
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            next='list_shows_1',
            category='%s Replay' % params.channel_name.upper(),
            window_title='%s Replay' % params.channel_name.upper()
        ),
    })

    # Add Live
    modes.append({
        'label': 'Live TV',
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
                    action='channel_entry',
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

            context_menu = []
            download_video = (
                _('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    video_id=video_id) + ')'
            )
            context_menu.append(download_video)

            videos.append({
                'label': video_title,
                'thumb': video_img,
                'fanart': video_img,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
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
        content='tvshows')


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_live(params):
    """Build live listing"""
    lives = []

    title = ''
    plot = ''
    duration = 0
    img = ''

    file_path = utils.download_catalog(
        URL_INFO_LIVE_JSON,
        '%s_info_live.json' % (params.channel_name)
    )
    file_info_live = open(file_path).read()
    json_parser = json.loads(file_info_live)

    title = json_parser["titre"].encode('utf-8')

    video_id = json_parser["video"].encode('utf-8')

    # url_live = url_dailymotion_embed % video_id

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
            action='channel_entry',
            next='play_l',
            video_id=video_id,
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


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    url_video = URL_DAILYMOTION_EMBED % params.video_id

    desired_quality = common.PLUGIN.get_setting('quality')

    if params.next == 'download_video':
        return url_video
    else:
        html_video = utils.get_webcontent(url_video)
        html_video = html_video.replace('\\', '')

        if params.next == 'play_l':
            all_url_video = re.compile(
                r'{"type":"application/x-mpegURL","url":"(.*?)"'
            ).findall(html_video)
            # Just One Quality
            return all_url_video[0]
        elif params.next == 'play_r':
            all_url_video = re.compile(
                r'{"type":"video/mp4","url":"(.*?)"').findall(html_video)
            if desired_quality == "DIALOG":
                all_datas_videos = []
                for datas in all_url_video:
                    new_list_item = common.sp.xbmcgui.ListItem()
                    datas_quality = re.search('H264-(.+?)/', datas).group(1)
                    new_list_item.setLabel('H264-' + datas_quality)
                    new_list_item.setPath(datas)
                    all_datas_videos.append(new_list_item)

                seleted_item = common.sp.xbmcgui.Dialog().select(
                    "Choose Stream", all_datas_videos)

                return all_datas_videos[seleted_item].getPath().encode('utf-8')
            elif desired_quality == 'BEST':
                # Last video in the Best
                for datas in all_url_video:
                    url = datas
                return url
            else:
                return all_url_video[0]
