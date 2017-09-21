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
import ast
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

# TO DO
# Lot Code DailyMotion are present in some channel
# (create function to pass video_id from each channel using DailyMotion)
# Get Info Live

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

URL_ROOT = 'https://www.lequipe.fr'

URL_ROOT_VIDEO_LEQUIPE = 'https://www.lequipe.fr/lachainelequipe/'

URL_REPLAY_VIDEO_LEQUIPE = 'https://www.lequipe.fr/lachainelequipe/morevideos/%s'
# Category_id

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

    # Add Live
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
    """Build shows listing"""
    shows = []

    # Get categories :
    file_path = utils.download_catalog(
        URL_ROOT_VIDEO_LEQUIPE,
        '%s_video.html' % (
            params.channel_name))
    root_html = open(file_path).read()
    root_soup = bs(root_html, 'html.parser')

    categories_soup = root_soup.find_all('a', class_="navtab__item js-tabs-item")

    for category in categories_soup:

        category_name = category.get_text().encode('utf-8')
        category_url = URL_REPLAY_VIDEO_LEQUIPE % category.get('data-program-id')

        shows.append({
            'label': category_name,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                category_url=category_url,
                page='1',
                category_name=category_name,
                next='list_videos',
                window_title=category_name
            )
        })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL))


@common.PLUGIN.cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])


    url = params.category_url + '/' + params.page
    file_path = utils.download_catalog(
        url,
        '%s_%s_%s.html' % (
            params.channel_name,
            params.category_name,
            params.page))
    root_html = open(file_path).read()
    root_soup = bs(root_html, 'html.parser')

    category_soup = root_soup.find_all(
        'a',
        class_='colead')

    for program in category_soup:

        # Get Video_ID
        url = URL_ROOT + program['href'].encode('utf-8')
        html_video_equipe = utils.get_webcontent(url)
        video_id = re.compile(
            r'<iframe src="//www.dailymotion.com/embed/video/(.*?)\?', re.DOTALL).findall(html_video_equipe)[0]

        title = program.find(
            'h2').get_text().encode('utf-8')
        colead__image = program.find(
            'div',
            class_='colead__image')
        img = colead__image.find(
            'img')['data-src'].encode('utf-8')

        date = colead__image.find(
            'span',
            class_='colead__layerText colead__layerText--bottomleft'
        ).get_text().strip().encode('utf-8')  # 07/09/17 | 01 min
        date = date.split('/')
        day = date[0]
        mounth = date[1]
        year = '20' + date[2].split(' ')[0]

        date = '.'.join((day, mounth, year))
        aired = '-'.join((year, mounth, day))

        duration_string = colead__image.find(
            'span',
            class_='colead__layerText colead__layerText--bottomleft'
        ).get_text().strip().encode('utf-8')
        duration_list = duration_string.split(' ')
        duration = int(duration_list[2]) * 60

        info = {
            'video': {
                'title': title,
                'aired': aired,
                'date': date,
                'duration': duration,
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
            'label': title,
            'thumb': img,
            'fanart': img,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next='play_r',
                video_id=video_id
            ),
            'is_playable': True,
            'info': info,
            'context_menu': context_menu
        })

    # More videos...
    videos.append({
        'label': common.ADDON.get_localized_string(30100),
        'url': common.PLUGIN.get_url(
            action='channel_entry',
            category_url=params.category_url,
            category_name=params.category_name,
            next='list_videos',
            page=str(int(params.page) + 1),
            update_listing=True,
            previous_listing=str(videos)
        ),
    })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_PLAYCOUNT,
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_DURATION,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
        content='tvshows',
        update_listing='update_listing' in params,
    )

@common.PLUGIN.cached(common.CACHE_TIME)
def list_live(params):
    """Build live listing"""
    lives = []

    title = ''
    plot = ''
    duration = 0
    img = ''
    url_live = ''
    video_id = ''
    url_live = ''

    html_live_equipe = utils.get_webcontent(URL_ROOT_VIDEO_LEQUIPE)
    video_id = re.compile(
        r'<iframe src="//www.dailymotion.com/embed/video/(.*?)\?', re.DOTALL).findall(html_live_equipe)[0]

    title = '%s Live' % params.channel_name.upper()

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



@common.PLUGIN.cached(common.CACHE_TIME)
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
            all_url_video = re.compile(r'{"type":"application/x-mpegURL","url":"(.*?)"').findall(html_video)
            # Just One Quality
            return all_url_video[0]
        elif  params.next == 'play_r':
            all_url_video = re.compile(r'{"type":"video/mp4","url":"(.*?)"').findall(html_video)
            if desired_quality == "DIALOG":
                all_datas_videos = []
                for datas in all_url_video:
                    new_list_item = common.sp.xbmcgui.ListItem()
                    datas_quality = re.search('H264-(.+?)/', datas).group(1)
                    new_list_item.setLabel('H264-' + datas_quality)
                    new_list_item.setPath(datas)
                    all_datas_videos.append(new_list_item)

                seleted_item = common.sp.xbmcgui.Dialog().select("Choose Stream", all_datas_videos)

                return all_datas_videos[seleted_item].getPath().encode('utf-8')
            elif desired_quality == 'BEST':
                # Last video in the Best
                for datas in all_url_video:
                    url = datas
                return url
            else:
                return all_url_video[0]
