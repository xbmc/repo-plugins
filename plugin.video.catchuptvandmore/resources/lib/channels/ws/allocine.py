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

import ast
import json
import re
import requests
from bs4 import BeautifulSoup as bs
from youtube_dl import YoutubeDL
from resources.lib import utils
from resources.lib import common

# TO DO
# Vimeo HTTP 503
# Get Last_Page (for Programs, Videos)
# Get Partner Id ?
# Todo get Aired, Year, Date of the Video

URL_ROOT = 'http://www.allocine.fr'

URL_API_MEDIA = 'http://api.allocine.fr/rest/v3/' \
                'media?code=%s&partner=%s&format=json'
# videoId, PARTENER

PARTNER = 'YW5kcm9pZC12Mg'

# Initialize GNU gettext emulation in addon
# This allows to use UI strings from addon’s English
# strings.po file instead of numeric codes
_ = common.ADDON.initialize_gettext()


def channel_entry(params):
    """Entry function of the module"""
    if 'root' in params.next:
        return root(params)
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)
    return None


CATEGORIES = {
    'Les émissions': URL_ROOT + '/video/',
    'Videos Films (Bandes-Annonces, Extraits, ...)':
        URL_ROOT + '/video/films/',
    'Videos Séries TV  (Bandes-Annonces, Extraits, ...)':
        URL_ROOT + '/series/video/'
}

CATEGORIES_LANGUAGE = {
    'VF': 'version-0/',
    'VO': 'version-1/'
}


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def root(params):
    """Add modes in the listing"""
    modes = []

    for category_name, category_url in CATEGORIES.iteritems():

        if 'series' in category_url or 'films' in category_url:
            next_value = 'list_shows_films_series_1'
        else:
            next_value = 'list_shows_emissions_1'

        modes.append({
            'label': category_name,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                category_url=category_url,
                category_name=category_name,
                next=next_value,
                window_title=category_name
            )
        })

    return common.PLUGIN.create_listing(
        modes,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_LABEL,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_shows(params):
    """Build categories listing"""
    shows = []
    if 'previous_listing' in params:
        shows = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_shows_emissions_1':

        # Build Categories Emissions
        replay_categories_programs_html = utils.get_webcontent(
            params.category_url)
        replay_categories_programs_soup = bs(
            replay_categories_programs_html, 'html.parser')
        root_categories_programs = replay_categories_programs_soup.find(
            'li', class_='item_4 is_active ')
        replay_categories_programs = root_categories_programs.find_all('a')

        for category_programs in replay_categories_programs:
            categorie_programs_title = category_programs.get_text()
            categorie_programs_title = categorie_programs_title.strip()
            categorie_programs_title = categorie_programs_title.encode('utf-8')

            categorie_programs_url = URL_ROOT + category_programs.get('href')
            shows.append({
                'label': categorie_programs_title,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_shows_emissions_2',
                    title=categorie_programs_title,
                    categorie_programs_url=categorie_programs_url,
                    window_title=categorie_programs_title
                )
            })

    elif params.next == 'list_shows_emissions_2':

        # Build sub categories if exists / add 'Les Programmes', 'Les Vidéos'
        replay_subcategories_programs_html = utils.get_webcontent(
            params.categorie_programs_url)
        replay_subcategories_programs_soup = bs(
            replay_subcategories_programs_html, 'html.parser')

        # Les vidéos
        show_title = '# Les videos'
        next_value = 'list_videos_emissions_1'
        show_url = params.categorie_programs_url
        shows.append({
            'label': show_title,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next=next_value,
                title=show_title,
                page='1',
                show_url=show_url,
                window_title=show_title
            )
        })

        # Les programmes
        programs_title = '# Les programmes'
        next_value = 'list_shows_emissions_4'
        programs_url = params.categorie_programs_url.replace(
            '/cat-', '/prgcat-')

        shows.append({
            'label': programs_title,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next=next_value,
                title=programs_title,
                page='1',
                programs_url=programs_url,
                window_title=programs_title
            )
        })

        # Subcategories
        subcategories = replay_subcategories_programs_soup.find(
            'div', class_='nav-button-filter').find_all('a')

        for subcategory in subcategories:
            subcategorie_programs_title = subcategory.find(
                'span', class_='label').get_text().encode('utf-8')
            subcategorie_programs_url = URL_ROOT + subcategory.get('href')

            shows.append({
                'label': subcategorie_programs_title,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_shows_emissions_3',
                    title=subcategorie_programs_title,
                    subcategorie_programs_url=subcategorie_programs_url,
                    window_title=subcategorie_programs_title
                )
            })

    elif params.next == 'list_shows_emissions_3':

        # Les vidéos
        show_title = '# Les videos'
        next_value = 'list_videos_emissions_1'
        show_url = params.subcategorie_programs_url
        shows.append({
            'label': show_title,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next=next_value,
                title=show_title,
                page='1',
                show_url=show_url,
                window_title=show_title
            )
        })

        # Les programmes
        programs_title = '# Les programmes'
        next_value = 'list_shows_emissions_4'
        programs_url = params.subcategorie_programs_url.replace(
            '/cat-', '/prgcat-')

        shows.append({
            'label': programs_title,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next=next_value,
                title=programs_title,
                page='1',
                programs_url=programs_url,
                window_title=programs_title
            )
        })

    elif params.next == 'list_shows_emissions_4':

        replay_programs_html = utils.get_webcontent(
            params.programs_url + '?page=%s' % params.page)
        replay_programs_soup = bs(replay_programs_html, 'html.parser')
        replay_programs = replay_programs_soup.find_all(
            'figure', class_='media-meta-fig')

        for program in replay_programs:

            program_title = program.find(
                'h2', class_='title '
            ).find('span').find('a').get_text().strip().encode('utf-8')
            program_img = program.find('img').get('src')
            program_url = URL_ROOT + program.find(
                'h2', class_='title '
            ).find('span').find('a').get('href').encode('utf-8')

            shows.append({
                'label': program_title,
                'thumb': program_img,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_shows_emissions_5',
                    program_title=program_title,
                    program_url=program_url,
                    window_title=program_title
                )
            })

        if replay_programs_soup.find('div', class_='pager pager margin_40t') \
                is not None:
            # More programs...
            shows.append({
                'label': '# ' + common.ADDON.get_localized_string(30108),
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_shows_emissions_4',
                    programs_url=params.programs_url,
                    page=str(int(params.page) + 1),
                    update_listing=True,
                    previous_listing=str(shows)
                ),
            })

    elif params.next == 'list_shows_emissions_5':

        replay_seasons_html = utils.get_webcontent(
            params.program_url + 'saisons/')
        replay_seasons_soup = bs(replay_seasons_html, 'html.parser')
        replay_seasons = replay_seasons_soup.find_all(
            'h2', class_='fs18 d_inline_block margin_10r')

        if len(replay_seasons) > 0:

            for season in replay_seasons:
                season_title = season.find('a').find('span').get_text().strip()
                show_season_url = URL_ROOT + season.find(
                    'a', class_='no_underline').get('href').encode('utf-8')

                # Get Last Page
                last_page = '0'
                info_show_season = utils.get_webcontent(show_season_url)
                info_show_season_pages = re.compile(
                    '<a href="(.*?)"').findall(info_show_season)
                for info_show_season_page in info_show_season_pages:
                    if '?page=' in info_show_season_page:
                        last_page = info_show_season_page.split('=')[1]

                shows.append({
                    'label': season_title,
                    'url': common.PLUGIN.get_url(
                        action='channel_entry',
                        next='list_videos_emissions_1',
                        title=season_title,
                        page='1',
                        last_page=last_page,
                        show_url=show_season_url,
                        window_title=season_title
                    )
                })

        else:
            season_title = replay_seasons_soup.find(
                'div', class_='margin_20t margin_40b'
            ).find('a').get_text().strip().encode('utf-8')
            show_season_url = URL_ROOT + replay_seasons_soup.find(
                'div', class_='margin_20t margin_40b'
            ).find('a').get('href').encode('utf-8')

            # Get Last Page
            last_page = '0'
            info_show_season = utils.get_webcontent(show_season_url)
            info_show_season_pages = re.compile(
                '<a href="(.*?)"').findall(info_show_season)
            for info_show_season_page in info_show_season_pages:
                if '?page=' in info_show_season_page:
                    last_page = info_show_season_page.split('=')[1]

            shows.append({
                'label': season_title,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='list_videos_emissions_1',
                    title=season_title,
                    page='1',
                    last_page=last_page,
                    show_url=show_season_url,
                    window_title=season_title
                )
            })

    elif params.next == 'list_shows_films_series_1':

        # Build All Types
        replay_types_films_series_html = utils.get_webcontent(
            params.category_url)
        replay_types_films_series_soup = bs(
            replay_types_films_series_html, 'html.parser')
        replay_types_films_series = replay_types_films_series_soup.find_all(
            'div', class_='left_col_menu_item')[0]

        show_title = '# Toutes les videos'
        next_value = 'list_videos_films_series_1'
        show_url = params.category_url
        shows.append({
            'label': show_title,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next=next_value,
                title=show_title,
                page='1',
                show_url=show_url,
                window_title=show_title
            )
        })

        for all_types in replay_types_films_series.find_all('a'):

            show_title = all_types.get_text()
            next_value = 'list_shows_films_series_2'
            show_url = URL_ROOT + all_types.get('href')

            shows.append({
                'label': show_title,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next=next_value,
                    title=show_title,
                    show_url=show_url,
                    window_title=show_title
                )
            })

    elif params.next == 'list_shows_films_series_2':

        # Build All Languages
        show_title = '# Toutes les videos'
        next_value = 'list_videos_films_series_1'
        show_url = params.show_url
        shows.append({
            'label': show_title,
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                next=next_value,
                title=show_title,
                show_url=show_url,
                page='1',
                window_title=show_title
            )
        })

        for language, language_url in CATEGORIES_LANGUAGE.iteritems():

            show_title = language
            next_value = 'list_videos_films_series_1'
            show_url = params.show_url + language_url

            shows.append({
                'label': show_title,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next=next_value,
                    title=show_title,
                    show_url=show_url,
                    page='1',
                    window_title=show_title
                )
            })

    return common.PLUGIN.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_LABEL,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        update_listing='update_listing' in params,
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def list_videos(params):
    """Build videos listing"""
    videos = []
    if 'previous_listing' in params:
        videos = ast.literal_eval(params['previous_listing'])

    if params.next == 'list_videos_films_series_1':

        replay_episodes_html = utils.get_webcontent(
            params.show_url + '?page=%s' % params.page)
        replay_episodes_soup = bs(replay_episodes_html, 'html.parser')
        episodes = replay_episodes_soup.find_all(
            'article', class_="media-meta sidecontent small")

        for episode in episodes:
            video_title = episode.find('h2').find(
                'span').find('a').get_text().strip().encode('utf-8')
            video_id = re.compile(
                'cmedia=(.*?)&').findall(episode.find('a').get('href'))[0]
            video_img = episode.find('img').get('src').encode('utf-8')
            video_duration = 0

            info = {
                'video': {
                    'title': video_title,
                    # 'aired': aired,
                    # 'date': date,
                    'duration': video_duration,
                    # 'plot': video_plot,
                    # 'year': year,
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
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='play_r',
                    video_id=video_id
                ),
                'is_playable': True,
                'info': info  # ,
                # 'context_menu': context_menu
            })

        # More videos...
        videos.append({
            'label': '# ' + common.ADDON.get_localized_string(30100),
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                show_url=params.show_url,
                next='list_videos_films_series_1',
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(videos)
            ),
        })

    elif params.next == 'list_videos_emissions_1':
        replay_episodes_html = utils.get_webcontent(
            params.show_url + '?page=%s' % params.page)
        replay_episodes_soup = bs(replay_episodes_html, 'html.parser')

        if replay_episodes_soup.find(
                'section', class_='media-meta-list by2 j_w') is not None:
            root_episodes_soup = replay_episodes_soup.find(
                'section', class_='media-meta-list by2 j_w')
            episodes = root_episodes_soup.find_all(
                'figure', class_='media-meta-fig')
        else:
            episodes = replay_episodes_soup.find_all(
                'figure', class_='media-meta-fig')

        for episode in episodes:
            if episode.find('h3') is not None:
                video_title = episode.find(
                    'h3').find('span').find('a').get_text().strip()
            else:
                video_title = episode.find(
                    'h2').find('span').find('a').get_text().strip()
            if '?cmedia=' in episode.find('a').get('href'):
                video_id = episode.find('a').get('href').split('?cmedia=')[1]
            elif 'cfilm=' in episode.find('a').get('href') or \
                    'cserie=' in episode.find('a').get('href'):
                video_id = episode.find(
                    'h2').find('span').find(
                        'a').get('href').split('_cmedia=')[1].split('&')[0]
            else:
                video_id = episode.find(
                    'a').get('href').split('-')[1].replace('/', '')
            video_plot = ''
            for plot_value in episode.find(
                    'div', class_='media-meta-figcaption-inner').find_all('p'):
                video_plot = plot_value.get_text().strip()
            if episode.find('meta') is not None:
                video_img = episode.find('meta').get('content').encode('utf-8')
            else:
                video_img = episode.find('img').get('src').encode('utf-8')
            video_duration = 0

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
                    video_id=video_id) + ')'
            )
            context_menu.append(download_video)

            videos.append({
                'label': video_title,
                'thumb': video_img,
                'url': common.PLUGIN.get_url(
                    action='channel_entry',
                    next='play_r',
                    video_id=video_id
                ),
                'is_playable': True,
                'info': info  # ,
                # 'context_menu': context_menu
            })

        # More videos...
        videos.append({
            'label': '# ' + common.ADDON.get_localized_string(30100),
            'url': common.PLUGIN.get_url(
                action='channel_entry',
                show_url=params.show_url,
                # last_page=params.last_page,
                next='list_videos_1',
                page=str(int(params.page) + 1),
                update_listing=True,
                previous_listing=str(videos)
            ),
        })

    return common.PLUGIN.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows',
        update_listing='update_listing' in params,
    )


@common.PLUGIN.mem_cached(common.CACHE_TIME)
def get_video_url(params):
    """Get video URL and start video player"""
    video_json = utils.get_webcontent(
        URL_API_MEDIA % (params.video_id, PARTNER))
    video_json_parser = json.loads(video_json)

    url = ''
    if 'rendition' in video_json_parser["media"]:
        # (Video Hosted By Allocine)
        for media in video_json_parser["media"]["rendition"]:
            url = media["href"]
        if requests.get(url, stream=True).status_code == 404:
            utils.send_notification(common.ADDON.get_localized_string(30111))
            return ''
        return url
    else:
        # (Video Not Hosted By Allocine)
        url_video_embeded = re.compile(
            'src=\'(.*?)\''
        ).findall(video_json_parser["media"]["trailerEmbed"])[0]
        url_video_embeded_html = utils.get_webcontent(url_video_embeded)
        url_video_json = re.compile(
            'data-model="(.*?)"'
        ).findall(url_video_embeded_html)[0].replace('&quot;', '"')
        url_video_json_parser = json.loads(url_video_json)
        # Case Facebook, Youtube and Vimeo (Not Working HTTP 503)
        if 'facebook' in url_video_json or \
                'youtube' in url_video_json or 'vimeo' in url_video_json:
            url_ytdl = url_video_json_parser["videos"][0]["sources"]["code"]
            url_ytdl = re.compile('src=(.*?) ').findall(
                url_ytdl
            )[0].replace('\\', '').replace('&amp;', '&').replace('"', '')
        # Case DailyMotion
        else:
            url_ytdl = url_video_json_parser["videos"]
            url_ytdl = url_ytdl[0]["sources"]["url_provider"]
            url_ytdl = 'https:' + url_ytdl.split(
                ':')[1].replace(
                    '\\', '').replace('&amp;', '&').replace('"', '')
        ydl = YoutubeDL()
        ydl.add_default_info_extractors()
        with ydl:
            result = ydl.extract_info(url_ytdl, download=False)
            for format_video in result['formats']:
                url = format_video['url']
        return url
