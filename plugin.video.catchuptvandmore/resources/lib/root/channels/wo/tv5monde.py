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
import json
import re
from bs4 import BeautifulSoup as bs
from resources.lib import utils
from resources.lib import common


URL_TV5MAF_ROOT = 'https://afrique.tv5monde.com'

URL_TV5MONDE_LIVE = 'http://live.tv5monde.com/'

URL_TV5MONDE_ROOT = 'http://www.tv5mondeplus.com'

URL_TIVI5MONDE_ROOT = 'http://www.tivi5mondeplus.com'


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


LIST_LIVE_TV5MONDE = {
    common.GETTEXT('Live TV') + ' France Belgique Suisse': 'fbs',
    common.GETTEXT('Live TV') + ' Info Plus': 'infoplus'
}

LIST_LIVE_TIVI5MONDE = {
    common.GETTEXT('Live TV') + ' TIVI 5Monde': 'tivi5monde'
}

CATEGORIES_VIDEOS_TV5MONDE = {
    'Information': '1',
    'Série & Fiction': '2',
    'Sport': '3',
    'Documentaire': '4',
    'Jeunesse': '5',
    'Musique': '6',
    'Bonus': '7',
    'Magazine': '9',
    'Divertissement': '8'
}

CATEGORIES_VIDEOS_TIVI5MONDE = {
    '/series/decouverte': 'REPLAY PROGRAMMES JEUNESSE DÉCOUVERTE',
    '/decouverte': 'LES DERNIERS ÉPISODES DE TES ÉMISSIONS DÉCOUVERTE',
    '/series/dessins-animes': 'REPLAY DESSINS ANIMÉS',
    '/dessins-animes': 'LES DERNIERS ÉPISODES DE TES DESSINS ANIMÉS PRÉFÉRÉS'
}


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []

    if params.next == 'list_shows_1':
        if params.channel_name == 'tv5mondeafrique':
            list_categories_html = utils.get_webcontent(
                URL_TV5MAF_ROOT + '/videos')
            list_categories_soup = bs(
                list_categories_html, 'html.parser')
            list_categories = list_categories_soup.find_all(
                'h2', class_='tv5-title tv5-title--beta u-color--goblin')

            for category in list_categories:

                category_title = category.find(
                    'a').get_text().encode('utf-8')
                category_url = URL_TV5MAF_ROOT + category.find(
                    'a').get('href').encode('utf-8')

                shows.append({
                    'label': category_title,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='list_shows_2',
                        title=category_title,
                        category_url=category_url,
                        window_title=category_title
                    )
                })

        elif params.channel_name == 'tv5monde':

            list_categories_html = utils.get_webcontent(
                URL_TV5MONDE_ROOT + '/toutes-les-videos')
            list_categories_soup = bs(
                list_categories_html, 'html.parser')
            category_title = list_categories_soup.find(
                'nav', class_='footer__emissions').find(
                'div', class_='footer__title').get_text().strip()

            shows.append({
                'label': category_title,
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next='list_shows_2',
                    title=category_title,
                    window_title=category_title
                )
            })

            for category_title, category_type in \
                    CATEGORIES_VIDEOS_TV5MONDE.iteritems():

                shows.append({
                    'label': category_title,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='list_videos_2',
                        page='1',
                        title=category_title,
                        category_type=category_type,
                        window_title=category_title
                    )
                })

        elif params.channel_name == 'tivi5monde':

            for category_context, category_title in \
                    CATEGORIES_VIDEOS_TIVI5MONDE.iteritems():

                category_url = URL_TIVI5MONDE_ROOT + category_context

                if 'REPLAY' in category_title:
                    value_next = 'list_shows_2'
                else:
                    value_next = 'list_videos_1'

                shows.append({
                    'label': category_title,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next=value_next,
                        page='0',
                        title=category_title,
                        category_url=category_url,
                        window_title=category_title
                    )
                })

    elif params.next == 'list_shows_2':
        if params.channel_name == 'tv5mondeafrique':

            list_shows_html = utils.get_webcontent(
                params.category_url)
            list_shows_soup = bs(list_shows_html, 'html.parser')
            list_shows = list_shows_soup.find_all(
                'div', class_='grid-col-12 grid-col-m-4')

            for show in list_shows:

                show_title = show.find('h2').get_text().strip().encode('utf-8')
                show_url = URL_TV5MAF_ROOT + show.find(
                    'a').get('href').encode('utf-8')
                if 'http' in show.find('img').get('src'):
                    show_image = show.find('img').get(
                        'src').encode('utf-8')
                else:
                    show_image = URL_TV5MAF_ROOT + show.find('img').get(
                        'src').encode('utf-8')

                shows.append({
                    'label': show_title,
                    'thumb': show_image,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='list_videos_1',
                        title=show_title,
                        category_url=show_url,
                        window_title=show_title
                    )
                })

        elif params.channel_name == 'tv5monde':

            list_categories_html = utils.get_webcontent(
                URL_TV5MONDE_ROOT)
            list_categories_soup = bs(
                list_categories_html, 'html.parser')
            list_categories = list_categories_soup.find(
                'nav', class_='footer__emissions').find_all('li')

            for category in list_categories:

                category_title = category.find('a').get_text().strip()
                category_url = URL_TV5MONDE_ROOT + category.find(
                    'a').get('href')

                shows.append({
                    'label': category_title,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='list_videos_1',
                        page='1',
                        title=category_title,
                        category_url=category_url,
                        window_title=category_title
                    )
                })

        elif params.channel_name == 'tivi5monde':

            list_categories_html = utils.get_webcontent(
                params.category_url)
            list_categories_soup = bs(
                list_categories_html, 'html.parser')
            list_categories = list_categories_soup.find_all(
                'div', class_='views-field views-field-nothing')

            for category in list_categories:

                category_title = category.find('h3').find(
                    'a').get_text().strip()
                category_url = URL_TIVI5MONDE_ROOT + category.find(
                    'a').get('href')
                category_image = category.find('img').get('src')

                shows.append({
                    'label': category_title,
                    'thumb': category_image,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='list_videos_1',
                        page='0',
                        title=category_title,
                        category_url=category_url,
                        window_title=category_title
                    )
                })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        category=common.get_window_title()
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_videos_1':
        if params.channel_name == 'tv5mondeafrique':

            replay_videos_html = utils.get_webcontent(
                params.category_url)
            replay_videos_soup = bs(replay_videos_html, 'html.parser')
            if replay_videos_soup.find(
                    'div', class_='u-bg--concrete u-pad-t--xl u-pad-b--l') \
                    is None:

                data_video = replay_videos_soup.find(
                    'div', class_='tv5-player')

                video_title = data_video.find(
                    'h1').get_text().strip().encode('utf-8')
                video_img = re.compile(
                    r'image\" content=\"(.*?)\"').findall(
                    replay_videos_html)[0]
                video_plot = data_video.find(
                    'div',
                    class_='tv5-desc to-expand u-mg-t--m u-mg-b--s'
                ).get_text().strip().encode('utf-8')

                info = {
                    'video': {
                        'title': video_title,
                        # 'aired': aired,
                        # 'date': date,
                        # 'duration': video_duration,
                        'plot': video_plot,
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
                        video_url=params.category_url) + ')'
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
                        video_url=params.category_url
                    ),
                    'is_playable': True,
                    'info': info,
                    'context_menu': context_menu
                })
            else:
                seasons = replay_videos_soup.find(
                    'div',
                    class_='tv5-pagerTop tv5-pagerTop--green'
                ).find_all('a')
                if len(seasons) > 1:

                    for season in seasons:

                        video_title = 'Saison ' + season.get_text()
                        video_url = URL_TV5MAF_ROOT + season.get(
                            'href').encode('utf-8')

                        info = {
                            'video': {
                                'title': video_title
                            }
                        }

                        videos.append({
                            'label': video_title,
                            'url': common.PLUGIN.get_url(
                                module_path=params.module_path,
                                module_name=params.module_name,
                                action='replay_entry',
                                next='list_videos_2',
                                category_url=video_url
                            ),
                            'is_playable': False,
                            'info': info
                        })
                else:
                    all_videos = replay_videos_soup.find(
                        'div',
                        class_='u-bg--concrete u-pad-t--xl u-pad-b--l'
                    ).find_all(
                        'div',
                        'grid-col-12 grid-col-m-4')

                    for video in all_videos:

                        video_title = video.find(
                            'h2').get_text().strip().encode('utf-8')
                        video_img = video.find('img').get('src')
                        video_url = URL_TV5MAF_ROOT + video.find(
                            'a').get('href').encode('utf-8')

                        info = {
                            'video': {
                                'title': video_title,
                                # 'aired': aired,
                                # 'date': date,
                                # 'duration': video_duration,
                                # 'plot': video_plot,
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
                                video_url=video_url) + ')'
                        )
                        context_menu = []
                        context_menu.append(download_video)

                        videos.append({
                            'label': video_title,
                            'thumb': video_img,
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

        elif params.channel_name == 'tv5monde':

            replay_videos_html = utils.get_webcontent(
                params.category_url + '?page=%s' % params.page)
            replay_videos_soup = bs(replay_videos_html, 'html.parser')

            all_videos = replay_videos_soup.find_all('article')

            for video in all_videos:

                if video.find('p', class_='video-item__subtitle'):
                    video_title = video.find('h3').get_text(
                    ).strip() + ' - ' + video.find(
                        'p',
                        class_='video-item__subtitle').get_text(
                    ).strip()
                else:
                    video_title = video.find('h3').get_text(
                    ).strip()
                if 'http' in video.find('img').get('src'):
                    video_img = video.find('img').get('src')
                else:
                    video_img = URL_TV5MONDE_ROOT + video.find(
                        'img').get('src')
                video_url = URL_TV5MONDE_ROOT + video.find(
                    'a').get('href')

                info = {
                    'video': {
                        'title': video_title,
                        # 'aired': aired,
                        # 'date': date,
                        # 'duration': video_duration,
                        # 'plot': video_plot,
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
                        video_url=video_url) + ')'
                )
                context_menu = []
                context_menu.append(download_video)

                videos.append({
                    'label': video_title,
                    'thumb': video_img,
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

            # More videos...
            videos.append({
                'label': common.ADDON.get_localized_string(30700),
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    category_url=params.category_url,
                    next=params.next,
                    page=str(int(params.page) + 1),
                    title=params.title,
                    window_title=params.window_title,
                    update_listing=True,
                    previous_listing=str(videos)
                )
            })

        elif params.channel_name == 'tivi5monde':

            replay_videos_html = utils.get_webcontent(
                params.category_url + '?page=%s' % params.page)
            replay_videos_soup = bs(replay_videos_html, 'html.parser')

            all_videos = replay_videos_soup.find_all(
                'div', class_='row-vignette')

            for video in all_videos:

                video_title = video.find('img').get('alt')
                video_img = video.find('img').get('src')
                video_url = URL_TIVI5MONDE_ROOT + video.find(
                    'a').get('href')

                info = {
                    'video': {
                        'title': video_title,
                        # 'aired': aired,
                        # 'date': date,
                        # 'duration': video_duration,
                        # 'plot': video_plot,
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
                        video_url=video_url) + ')'
                )
                context_menu = []
                context_menu.append(download_video)

                videos.append({
                    'label': video_title,
                    'thumb': video_img,
                    'url': common.PLUGIN.get_url(
                        module_path=params.module_path,
                        module_name=params.module_name,
                        action='replay_entry',
                        next='play_r_tivi5monde',
                        video_url=video_url
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
                    category_url=params.category_url,
                    next=params.next,
                    page=str(int(params.page) + 1),
                    title=params.title,
                    window_title=params.window_title,
                    update_listing=True,
                    previous_listing=str(videos)
                )
            })

    elif params.next == 'list_videos_2':
        if params.channel_name == 'tv5mondeafrique':
            replay_videos_html = utils.get_webcontent(
                params.category_url)
            replay_videos_soup = bs(replay_videos_html, 'html.parser')

            all_videos = replay_videos_soup.find(
                'div',
                class_='u-bg--concrete u-pad-t--xl u-pad-b--l').find_all(
                'div', 'grid-col-12 grid-col-m-4')

            for video in all_videos:

                video_title = video.find(
                    'h2').get_text().strip().encode('utf-8')
                video_img = video.find('img').get('src')
                video_url = URL_TV5MAF_ROOT + video.find(
                    'a').get('href').encode('utf-8')

                info = {
                    'video': {
                        'title': video_title,
                        # 'aired': aired,
                        # 'date': date,
                        # 'duration': video_duration,
                        # 'plot': video_plot,
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
                        video_url=video_url) + ')'
                )
                context_menu = []
                context_menu.append(download_video)

                videos.append({
                    'label': video_title,
                    'thumb': video_img,
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

        elif params.channel_name == 'tv5monde':

            replay_videos_html = utils.get_webcontent(
                URL_TV5MONDE_ROOT +
                '/toutes-les-videos?order=1&type=%s&page=%s' % (
                    params.category_type, params.page)
            )
            replay_videos_soup = bs(replay_videos_html, 'html.parser')

            all_videos = replay_videos_soup.find_all('article')

            for video in all_videos:

                if video.find(
                    'a',
                    class_='video-item__link'
                ).get('href') != '':

                    if video.find('p', class_='video-item__subtitle'):
                        video_title = video.find('h3').get_text(
                        ).strip() + ' - ' + video.find(
                            'p',
                            class_='video-item__subtitle'
                        ).get_text(
                        ).strip()
                    else:
                        video_title = video.find('h3').get_text(
                        ).strip()
                    if 'http' in video.find('img').get('src'):
                        video_img = video.find('img').get('src')
                    else:
                        video_img = URL_TV5MONDE_ROOT + video.find(
                            'img').get('src')
                    video_url = URL_TV5MONDE_ROOT + video.find(
                        'a').get('href')

                    info = {
                        'video': {
                            'title': video_title,
                            # 'aired': aired,
                            # 'date': date,
                            # 'duration': video_duration,
                            # 'plot': video_plot,
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
                            video_url=video_url) + ')'
                    )
                    context_menu = []
                    context_menu.append(download_video)

                    videos.append({
                        'label': video_title,
                        'thumb': video_img,
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

            # More videos...
            videos.append({
                'label': common.ADDON.get_localized_string(30700),
                'url': common.PLUGIN.get_url(
                    module_path=params.module_path,
                    module_name=params.module_name,
                    action='replay_entry',
                    next=params.next,
                    page=str(int(params.page) + 1),
                    category_type=params.category_type,
                    title=params.title,
                    window_title=params.window_title,
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
    lives = []

    if params.channel_name == 'tv5monde':
        for live_name, live_id in LIST_LIVE_TV5MONDE.iteritems():

            live_title = live_name
            live_html = utils.get_webcontent(
                URL_TV5MONDE_LIVE + '%s.html' % live_id)
            live_json = re.compile(
                r'data-broadcast=\'(.*?)\'').findall(live_html)[0]
            live_json_parser = json.loads(live_json)
            live_url = live_json_parser["files"][0]["url"]
            live_img = URL_TV5MONDE_LIVE + re.compile(
                r'data-image=\"(.*?)\"').findall(live_html)[0]

            info = {
                'video': {
                    'title': live_title
                }
            }

            lives.append({
                'label': live_title,
                'thumb': live_img,
                'url': common.PLUGIN.get_url(
                    action='start_live_tv_stream',
                    next='play_l',
                    module_name=params.module_name,
                    module_path=params.module_path,
                    live_url=live_url,
                ),
                'is_playable': True,
                'info': info
            })

    elif params.channel_name == 'tivi5monde':

        for live_name, live_id in LIST_LIVE_TIVI5MONDE.iteritems():

            live_title = live_name
            live_html = utils.get_webcontent(
                URL_TV5MONDE_LIVE + '%s.html' % live_id)
            live_json = re.compile(
                r'data-broadcast=\'(.*?)\'').findall(live_html)[0]
            live_json_parser = json.loads(live_json)
            live_url = live_json_parser["files"][0]["url"]
            live_img = URL_TV5MONDE_LIVE + re.compile(
                r'data-image=\"(.*?)\"').findall(live_html)[0]

            info = {
                'video': {
                    'title': live_title
                }
            }

            lives.append({
                'label': live_title,
                'thumb': live_img,
                'url': common.PLUGIN.get_url(
                    action='start_live_tv_stream',
                    next='play_l',
                    module_name=params.module_name,
                    module_path=params.module_path,
                    live_url=live_url,
                ),
                'is_playable': True,
                'info': info
            })

    return lives


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    if params.next == 'play_r':
        info_video_html = utils.get_webcontent(params.video_url)
        video_json = re.compile(
            'data-broadcast=\'(.*?)\'').findall(
            info_video_html)[0]
        video_json = json.loads(video_json)
        return video_json["files"][0]["url"]
    elif params.next == 'play_r_tivi5monde':
        info_video_html = utils.get_webcontent(params.video_url)
        video_url = re.compile(
            'contentUrl\"\: \"(.*?)\"').findall(
            info_video_html)[0]
        return video_url
    elif params.next == 'play_l':
        return params.live_url
