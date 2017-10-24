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
import re
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

# TO DO
# Fix Download Video

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

# Live
URL_LIVE_JSON = 'http://dbxm993i42r09.cloudfront.net/' \
                'configs/blaze.json?callback=blaze'

URL_NOW_PLAYING = 'http://www.blaze.tv/home/index/now-playing'

# Replay
URL_SHOWS = 'http://www.blaze.tv/series?page=%s'
# pageId

URL_API_KEY = 'https://dbxm993i42r09.cloudfront.net/configs/config.blaze.js'

URL_STREAM = 'https://d2q1b32gh59m9o.cloudfront.net/player/config?' \
             'callback=ssmp&client=blaze&type=vod&apiKey=%s&videoId=%s&' \
             'format=jsonp&callback=ssmp'
# apiKey, videoId

URL_ROOT = 'http://www.blaze.tv'


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
            page='0',
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
    """Build categories listing"""
    shows = []
    if 'previous_listing' in params:
        shows = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_shows_1':
        file_path = utils.download_catalog(
            URL_SHOWS % params.page,
            '%s_shows_%s.html' % (params.channel_name, params.page)
        )
        replay_shows_html = open(file_path).read()

        replay_shows_soup = bs(replay_shows_html, 'html.parser')
        replay_shows = replay_shows_soup.find_all('div', class_='item')

        for show in replay_shows:

            show_title = show.find('a').find('img').get('alt')
            show_img = show.find('a').find('img').get('src').encode('utf-8')
            show_url = URL_ROOT + show.find('a').get('href').encode('utf-8')

            shows.append({
                'label': show_title,
                'thumb': show_img,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_shows_2',
                    title=show_title,
                    show_url=show_url,
                    window_title=show_title
                )
            })

        # More programs...
        shows.append({
            'label': common.ADDON.get_localized_string(30108),
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next='list_shows_1',
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(shows)
            ),
        })

    elif params.next == 'list_shows_2':

        file_path = utils.download_catalog(
            params.show_url,
            '%s_show_%s.html' % (params.channel_name, params.title)
        )
        replay_show_html = open(file_path).read()

        replay_show_seasons_soup = bs(replay_show_html, 'html.parser')
        replay_show_seasons = replay_show_seasons_soup.find(
            'div', class_='pagination')

        get_show_seasons = replay_show_seasons.find_all('a')

        for season in get_show_seasons:

            season_title = 'Series %s' % season.get_text().strip()
            show_season_url = URL_ROOT + season.get('href').encode('utf-8')

            shows.append({
                'label': season_title,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_videos_1',
                    title=params.title + '_' + season_title,
                    show_url=show_season_url,
                    window_title=season_title
                )
            })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        ),
        update_listing='update_listing' in params,
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []

    file_path = utils.download_catalog(
        params.show_url,
        '%s_show_%s.html' % (params.channel_name, params.title)
    )
    replay_show_html = open(file_path).read()
    episodes_soup = bs(replay_show_html, 'html.parser')

    root_episodes = episodes_soup.find_all('div', class_='carousel-inner')[0]
    episodes = root_episodes.find_all(
        'div', class_='col-md-4 wrapper-item season')

    for episode in episodes:

        value_episode = episode.find(
            'span', class_='caption-description'
        ).get_text().split(' | ')[1].split(' ')[1]
        value_season = episode.find(
            'span', class_='caption-description'
        ).get_text().split(' | ')[0].split(' ')[1]
        video_title = episode.find(
            'span', class_='caption-title'
        ).get_text() + ' S%sE%s' % (value_season, value_episode)

        video_duration = 0
        video_plot = episode.find(
            'span', class_='caption-title').get_text().encode('utf-8') + ' '
        video_plot = video_plot + episode.find(
            'span', class_='caption-description').get_text().encode('utf-8')
        video_img = episode.find('a').find('img').get('src')
        video_url = URL_ROOT + episode.find('a').get('href').encode('utf-8')

        info = {
            'video': {
                'title': video_title,
                # 'aired': aired,
                # 'date': date,
                'duration': video_duration,
                'plot': video_plot,
                # 'year': year,
                'mediatype': 'tvshow'
            }
        }

        context_menu = []
        download_video = (
            _('Download'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='download_video',
                video_url=video_url) + ')'
        )
        context_menu.append(download_video)

        videos.append({
            'label': video_title,
            'thumb': video_img,
            'fanart': video_img,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next='play_r',
                video_url=video_url
            ),
            'is_playable': True,
            'info': info  # ,
            # 'context_menu': context_menu
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
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_live(params):
    """Build live listing"""
    lives = []

    title = ''
    # subtitle = ' - '
    plot = ''
    duration = 0
    img = ''
    url_live = ''

    video_html = utils.get_webcontent(URL_NOW_PLAYING)
    title_live = bs(video_html, 'html.parser')
    title = title_live.get_text()
    url_live_html = utils.get_webcontent(URL_LIVE_JSON)
    url_live = re.compile('"url": "(.*?)"').findall(url_live_html)[0]

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


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_l':
        return params.url
    elif params.next == 'play_r' or params.next == 'download_video':
        video_html = utils.get_webcontent(params.video_url)
        videoId = re.compile('data-uvid="(.*?)"').findall(video_html)[0]
        apikey_html = utils.get_webcontent(URL_API_KEY)
        apikey = re.compile('"apiKey": "(.*?)"').findall(apikey_html)[0]
        stream_html = utils.get_webcontent(URL_STREAM % (apikey, videoId))
        return re.compile('"hls":"(.*?)"').findall(stream_html)[0]
