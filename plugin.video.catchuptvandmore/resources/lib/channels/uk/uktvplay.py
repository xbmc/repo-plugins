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
import requests
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common

# TO DO
# Live TV ?
# Get IMG from each SHOW (How ? Working on the browser not by wget)

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()

URL_ROOT = 'https://uktvplay.uktv.co.uk'

URL_SHOWS = 'https://uktvplay.uktv.co.uk/shows/channel/%s/'
# channel_name

URL_AUTHENTICATE = 'https://live.mppglobal.com/api/accounts/authenticate'
# POST Payload {email: "********@*******", password: "*********"}

URL_BRIGHTCOVE_API = 'https://edge.api.brightcove.com/playback/v1/' \
                     'accounts/%s/videos/%s'
# data-account, data-vidid

URL_JS_POLICY_KEY = 'https://players.brightcove.net/%s/%s_default/index.min.js'
# data-account, data-player


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


CORRECT_MOUNTH = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12'
}


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_policy_key(data_account, data_player):
    """Get policy key"""
    file_js = utils.get_webcontent(
        URL_JS_POLICY_KEY % (data_account, data_player))
    return re.compile('policyKey:"(.+?)"').findall(file_js)[0]


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

    if params.next == 'list_shows_1':

        file_path = utils.download_catalog(
            URL_SHOWS % (params.channel_name),
            '%s_show.html' % (params.channel_name)
        )
        replay_shows_html = open(file_path).read()

        replay_shows_soup = bs(replay_shows_html, 'html.parser')
        replay_shows = replay_shows_soup.find_all('div', class_='span2')

        for show in replay_shows:

            show_title = show.find('a').find('img').get('alt').encode('utf-8')
            show_img = show.find('a').find('img').get('src')
            show_url = URL_ROOT + show.find('a').get('href')

            if 'episodes' in show.find('p', class_='series-ep').get_text():
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
            else:
                shows.append({
                    'label': show_title,
                    'thumb': show_img,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        next='list_videos_1',
                        title=show_title,
                        show_url=show_url,
                        window_title=show_title
                    )
                })

    elif params.next == 'list_shows_2':

        file_path = utils.download_catalog(
            params.show_url,
            '%s_show_%s.html' % (params.channel_name, params.title)
        )
        replay_show_html = open(file_path).read()

        replay_show_seasons_soup = bs(replay_show_html, 'html.parser')
        replay_show_seasons = replay_show_seasons_soup.find(
            'ul', class_='clearfix tag-nav')

        get_show_seasons = replay_show_seasons.find_all('li')

        for season in get_show_seasons:

            season_title = 'Series %s' % season.get(
                'id').encode('utf-8').split('nav-series-')[1]

            shows.append({
                'label': season_title,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_videos_1',
                    title=params.title + '_' + season_title,
                    show_url=params.show_url,
                    window_title=season_title
                )
            })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL
        )
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []

    file_path = utils.download_catalog(
        params.show_url,
        '%s_show_%s.html' % (
            params.channel_name, params.title)
    )
    replay_show_season_html = open(file_path).read()
    seasons_episodes_soup = bs(replay_show_season_html, 'html.parser')

    # Get data-account
    data_account = re.compile(
        r'data-account="(.*?)"').findall(replay_show_season_html)[0]
    data_player = re.compile(
        r'data-player="(.*?)"').findall(replay_show_season_html)[0]

    if "Series" in params.title:
        # GET VideoId for each episode of season selected
        seasons_episodes = seasons_episodes_soup.find_all(
            'div', class_='spanOneThird vod-episode clearfix ')
        for episode in seasons_episodes:
            if episode.get('data-series') == \
                    params.title.split('Series')[1].strip():

                data_vidid = episode.get('data-vidid')

                video_title = episode.get('data-title')
                video_title = video_title + ' S%sE%s' % (
                    episode.get('data-series'), episode.get('data-episode'))
                video_duration = 0

                video_plot = 'Expire '
                video_plot = video_plot + episode.get(
                    'data-publishend').split('T')[0]
                video_plot = video_plot + '\n' + episode.get(
                    'data-teaser').encode('utf-8')

                video_img = episode.find('img').get('src')

                date_value = episode.get("data-publishstart")
                date_value_list = date_value.split('T')[0].split('-')
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

                context_menu = []
                download_video = (
                    _('Download'),
                    'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                        action='download_video',
                        data_vidid=data_vidid,
                        data_account=data_account,
                        data_player=data_player) + ')'
                )
                context_menu.append(download_video)

                videos.append({
                    'label': video_title,
                    'thumb': video_img,
                    'fanart': video_img,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        next='play_r',
                        data_vidid=data_vidid,
                        data_account=data_account,
                        data_player=data_player
                    ),
                    'is_playable': True,
                    'info': info,
                    'context_menu': context_menu
                })

        play_episode = seasons_episodes_soup.find(
            'div', class_='spanOneThird vod-episode clearfix playing in')
        if play_episode.get('data-series') == \
                params.title.split('Series')[1].strip():

            data_vidid = play_episode.get('data-vidid')

            video_title = play_episode.get('data-title')
            video_title = video_title + ' S%sE%s' % (
                play_episode.get('data-series'),
                play_episode.get('data-episode')
            )
            video_duration = 0
            video_plot = 'Expire '
            video_plot = video_plot + play_episode.get(
                'data-publishend').split('T')[0] + '\n '
            video_plot = video_plot + play_episode.get(
                'data-teaser').encode('utf-8')
            video_img = play_episode.find('img').get('src')

            date_value = play_episode.get("data-publishstart")
            date_value_list = date_value.split('T')[0].split('-')
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

            context_menu = []
            download_video = (
                _('Download'),
                'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                    action='download_video',
                    data_vidid=data_vidid,
                    data_account=data_account,
                    data_player=data_player) + ')'
            )
            context_menu.append(download_video)

            videos.append({
                'label': video_title,
                'thumb': video_img,
                'fanart': video_img,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='play_r',
                    data_vidid=data_vidid,
                    data_account=data_account,
                    data_player=data_player
                ),
                'is_playable': True,
                'info': info,
                'context_menu': context_menu
            })

    else:
        play_episode = seasons_episodes_soup.find(
            'div', class_='vod-video-container')

        data_vidid = play_episode.find('a').get('data-vidid')

        video_title = play_episode.find('img').get('alt')
        video_duration = 0
        video_plot = seasons_episodes_soup.find(
            'p', class_='teaser').get_text().encode('utf-8')
        video_img = re.compile(
            'itemprop="image" content="(.*?)"'
        ).findall(replay_show_season_html)[0]

        date_value = re.compile(
            'itemprop="uploadDate" content="(.*?)"'
        ).findall(replay_show_season_html)[0]
        date_value_list = date_value.split(',')[0].split(' ')
        if len(date_value_list[0]) == 1:
            day = '0' + date_value_list[0]
        else:
            day = date_value_list[0]
        try:
            mounth = CORRECT_MOUNTH[date_value_list[1]]
        except Exception:
            mounth = '00'
        year = date_value_list[2]

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

        context_menu = []
        download_video = (
            _('Download'),
            'XBMC.RunPlugin(' + common.PLUGIN.get_url(
                action='download_video',
                data_vidid=data_vidid,
                data_account=data_account,
                data_player=data_player) + ')'
        )
        context_menu.append(download_video)

        videos.append({
            'label': video_title,
            'thumb': video_img,
            'fanart': video_img,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next='play_r',
                data_vidid=data_vidid,
                data_account=data_account,
                data_player=data_player
            ),
            'is_playable': True,
            'info': info,
            'context_menu': context_menu
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
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_live(params):
    """Build live listing"""
    return None


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r' or params.next == 'download_video':

        session_requests = requests.session()

        # Build PAYLOAD
        """
        payload = {
            'email': common.PLUGIN.get_setting(
                params.channel_id.rsplit('.', 1)[0] + '.login'),
            'password': common.PLUGIN.get_setting(
                params.channel_id.rsplit('.', 1)[0] + '.password')
        }
        result = session_requests.post(URL_AUTHENTICATE,payload)
        """
        result_2 = session_requests.get(
            URL_BRIGHTCOVE_API % (params.data_account, params.data_vidid),
            headers={'Accept': 'application/json;pk=%s' % get_policy_key(
                params.data_account, params.data_player)}
        )
        return re.compile(
            '"application/x-mpegURL","src":"(.+?)"').findall(result_2.text)[0]
