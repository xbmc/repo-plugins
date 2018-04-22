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

import ast
import base64
import json
import re
import urllib
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import resolver
from resources.lib import common


URL_LIVE_SKYNEWS = 'http://news.sky.com/watch-live'

URL_IMG_YOUTUBE = 'https://i.ytimg.com/vi/%s/hqdefault.jpg'
# video_id

URL_VIDEOS_CHANNEL_YT = 'https://www.youtube.com/channel/%s/videos'
# Channel_name

URL_VIDEOS_SKYSPORTS = 'http://www.skysports.com/watch/video'

URL_ROOT_SKYSPORTS = 'http://www.skysports.com'

URL_OOYALA_VOD = 'https://player.ooyala.com/sas/player_api/v2/authorization/' \
    'embed_code/%s/%s?embedToken=%s&device=html5&domain=www.skysports.com'
# pcode, Videoid, embed_token

URL_PCODE_EMBED_TOKEN = 'http://www.skysports.com/watch/video/auth/v4/23'


def channel_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    elif 'replay_entry' == params.next:
        return root(params)
    elif 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def root(params):
    modes = []

    if params.channel_name == 'skynews':
        next_value = 'list_videos_youtube'
    elif params.channel_name == 'skysports':
        next_value = 'list_shows_sports'

    if params.next == "replay_entry":
        params['next'] = next_value
        params['page'] = '1'
        return channel_entry(params)

    # Add Replay
    modes.append({
        'label': 'Replay',
        'url': common.PLUGIN.get_url(
            module_path=params.module_path,
            module_name=params.module_name,
            action='replay_entry',
            next=next_value,
            page='1',
            category='%s Replay' % params.channel_name.upper(),
            window_title='%s Replay' % params.channel_name.upper()
        ),
    })

    # Add Live
    if params.channel_name == 'skynews':
        modes.append({
            'label': common.GETTEXT('Live TV'),
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
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
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.next == 'list_shows_sports':

        title = 'Soccer AM (youtube)'
        shows.append({
            'label': title,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='list_videos_youtube',
                page='1',
                channel_youtube='UCE97AW7eR8VVbVPBy4cCLKg',
                title=title,
                window_title=title
            )
        })

        title = 'Sky Sports (youtube)'
        shows.append({
            'label': title,
            'url': common.PLUGIN.get_url(
                module_path=params.module_path,
                module_name=params.module_name,
                action='replay_entry',
                next='list_videos_youtube',
                page='1',
                channel_youtube='UCTU_wC79Dgi9rh4e9-baTqA',
                title=title,
                window_title=title
            )
        })

        list_catergories_html = utils.get_webcontent(
            URL_VIDEOS_SKYSPORTS)
        list_catergories_soup = bs(list_catergories_html, 'html.parser')
        list_catergories = list_catergories_soup.find_all(
            'a', class_='page-nav__link')

        for category in list_catergories:

            category_title = category.get_text()
            category_url = URL_ROOT_SKYSPORTS + \
                category.get('href').encode('utf-8')

            shows.append({
                'label': category_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='list_videos_sports',
                    page='1',
                    title=category_title,
                    category_url=category_url,
                    window_title=category_title
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
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_videos_youtube':

        if params.channel_name == 'skysports':
            c_name = params.channel_youtube
        elif params.channel_name == 'skynews':
            c_name = 'UCoMdktPbSTixAyNGwb-UYkQ'

        list_videos = utils.get_webcontent(
            URL_VIDEOS_CHANNEL_YT % c_name)

        json_value = re.compile(
            'window\["ytInitialData"\] = (.*?);').findall(list_videos)[0]
        json_parser = json.loads(json_value)

        get_tab_contents = json_parser["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][1]
        get_contents = get_tab_contents["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0]
        get_contents_2 = get_contents["itemSectionRenderer"]["contents"][0]
        get_items = get_contents_2["gridRenderer"]["items"]

        for video_data in get_items:

            video_id = video_data["gridVideoRenderer"]["videoId"]
            title = video_data["gridVideoRenderer"]["title"]["simpleText"].encode('utf-8')
            plot = ''
            duration = 0
            img = URL_IMG_YOUTUBE % video_id

            info = {
                'video': {
                    'title': title,
                    'plot': plot,
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
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='play_r_news',
                    video_id=video_id,
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

    elif params.next == 'list_videos_sports':

        list_videos_html = utils.get_webcontent(
            params.category_url + '/more/%s' % params.page)
        list_videos_soup = bs(list_videos_html, 'html.parser')
        list_videos = list_videos_soup.find_all(
            'div', class_='polaris-tile__inner')

        for video in list_videos:

            video_id = re.compile(r'216\/(.*?)\.jpg').findall(
                video.find('img').get('data-src'))[0]
            title = video.find('h2').find('a').get_text().strip()
            plot = ''
            duration = 0
            img = video.find('img').get('data-src')

            info = {
                'video': {
                    'title': title,
                    'plot': plot,
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
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='play_r_sports',
                    video_id=video_id,
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
                next='list_videos_sports',
                category_url=params.category_url,
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(videos)
            )
        })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        update_listing='update_listing' in params,
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_live_item(params):
    plot = ''
    duration = 0
    img = ''
    video_id = ''

    # Get URL Live
    file_path = utils.download_catalog(
        URL_LIVE_SKYNEWS,
        '%s_live.html' % params.channel_name,
    )
    live_html = open(file_path).read()

    video_id = re.compile(
        r'www.youtube.com/embed/(.*?)\?').findall(live_html)[0]

    img = URL_IMG_YOUTUBE % video_id

    info = {
        'video': {
            'title': params.channel_label,
            'plot': plot,
            'duration': duration
        }
    }

    return {
        'label': params.channel_label,
        'fanart': img,
        'thumb': img,
        'url': common.PLUGIN.get_url(
            module_path=params.module_path,
            module_name=params.module_name,
            action='start_live_tv_stream',
            next='play_l',
            video_id=video_id
        ),
        'is_playable': True,
        'info': info
    }


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_l':
        return resolver.get_stream_youtube(params.video_id, False)
    elif params.next == 'play_r_news':
        return resolver.get_stream_youtube(params.video_id, False)
    elif params.next == 'play_r_sports':
        data_embed_token = utils.get_webcontent(
            URL_PCODE_EMBED_TOKEN)
        pcode = re.compile(
            'sas/embed_token/(.*?)/all').findall(data_embed_token)[0]
        data_embed_token = urllib.quote_plus(
            data_embed_token.replace('"',''))
        video_vod = utils.get_webcontent(
            URL_OOYALA_VOD % (pcode, params.video_id, data_embed_token))
        json_parser = json.loads(video_vod)

        # Get Value url encodebase64
        if 'streams' in json_parser["authorization_data"][params.video_id]:
            for stream in json_parser["authorization_data"][params.video_id]["streams"]:
                url_base64 = stream["url"]["data"]
            return base64.standard_b64decode(url_base64)
        else:
            return None
    elif params.next == 'download_video':
        return resolver.get_stream_youtube(params.video_id, True)
