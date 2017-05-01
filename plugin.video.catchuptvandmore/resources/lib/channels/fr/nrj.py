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

from resources.lib import utils
from resources.lib import common
from bs4 import BeautifulSoup as bs

url_replay = 'http://www.nrj-play.fr/%s/replay'
# channel_name (nrj12, ...)

url_root = 'http://www.nrj-play.fr'


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_url(params)
    else:
        return None


@common.plugin.cached(common.cache_time)
def list_shows(params):
    shows = []

    if 'list_shows_1' in params.next:
        # Build categories list (Tous les programmes, Séries, ...)
        file_path = utils.download_catalog(
            url_replay % params.channel_name,
            '%s_replay.html' % params.channel_name,
        )
        replay_html = open(file_path).read()
        replay_soup = bs(replay_html, 'html.parser')

        categories_soup = replay_soup.find_all(
            'li',
            class_='subNav-menu-item')

        for category in categories_soup:
            url_category = category.find('a')['href'].encode('utf-8')
            title_category = category.find('a').get_text().encode('utf-8')

            shows.append({
                'label': title_category,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    url_category=url_category,
                    next='list_shows_programs',
                    title_category=title_category,
                    window_title=title_category
                )
            })

    elif 'list_shows_programs' in params.next:
        # Build category's programs list
        # (Crimes, tellement vrai, Le mad mag, ...)
        file_path = utils.download_catalog(
            url_root + params.url_category,
            '%s_%s_category.html' % (
                params.channel_name,
                params.title_category),
        )
        category_html = open(file_path).read()
        category_soup = bs(category_html, 'html.parser')

        programs_soup = category_soup.find_all(
            'div',
            class_='linkProgram')

        for program in programs_soup:
            title = program.find(
                'h2',
                class_='linkProgram-title').get_text().encode('utf-8')

            title = ' '.join(title.split())

            url = program.find('a')['href'].encode('utf-8')
            img = program.find('img')['src'].encode('utf-8')

            shows.append({
                'label': title,
                'thumb': img,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='list_shows_seasons',
                    url_program=url,
                    title_program=title,
                    window_title=title
                ),
            })

    elif 'list_shows_seasons' in params.next:
        file_path = utils.download_catalog(
            url_root + params.url_program,
            '%s_%s_program.html' % (
                params.channel_name,
                params.title_program),
        )
        program_html = open(file_path).read()
        program_soup = bs(program_html, 'html.parser')
        program_url = program_soup.find(
            'a',
            class_='pushProgram-link')['href'].encode('utf-8')

        file_path = utils.download_catalog(
            url_root + program_url,
            '%s_%s_program_fiche.html' % (
                params.channel_name,
                params.title_program),
        )
        program_html = open(file_path).read()
        program_soup = bs(program_html, 'html.parser')

        seasons_soup = program_soup.find(
            'ul',
            class_='seasonsBox-list')

        if seasons_soup is not None:
            for season in seasons_soup.find_all('li'):
                title_season = season.find(
                    'a').get_text().encode('utf-8')
                season_url = season.find('a')['href'].encode('utf-8')

                shows.append({
                    'label': title_season,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        next='list_shows_season_categories',
                        season_url=season_url,
                        title_program=params.title_program,
                        title_season=title_season,
                        window_title=title_season
                    ),
                })

        else:
            params['next'] = 'list_shows_season_categories'
            params['season_url'] = program_url
            params['title_program'] = params.title_program
            params['title_season'] = 'no_season'
            params['window_title'] = params.window_title
            return list_shows(params)

    elif 'list_shows_season_categories':
        # Build program's categories
        # (Les vidéos, les actus, les bonus, ...)
        file_path = utils.download_catalog(
            url_root + params.season_url,
            '%s_%s_%s_program_season.html' % (
                params.channel_name,
                params.title_program,
                params.title_season),
        )
        program_html = open(file_path).read()
        program_soup = bs(program_html, 'html.parser')

        # We have to find all 'flag-category' tag and all title h2

        season_categories = {}
        flag_categories_soup = program_soup.find_all(
            'a',
            attrs={'class': 'flag-category'})
        for flag_category in flag_categories_soup:
            season_category_title = flag_category.get_text().encode('utf-8')
            if season_category_title == '':
                season_category_title = 'No name'
            season_categories[season_category_title] = 'flag_category'

        titles_h2 = program_soup.find_all(
            'h2',
            attrs={'class': 'title-2'})

        for title_h2 in titles_h2:
            if 'itemprop' not in title_h2.attrs:
                separator = title_h2.parent.find(
                    'div',
                    class_='separator-wrap')
                if separator:
                    url = separator.find('a')['href'].encode('utf-8')
                    season_categories[title_h2.get_text().encode(
                        'utf-8')] = url

        for season_category_title, \
                season_category_url in season_categories.iteritems():
            shows.append({
                'label': season_category_title,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='list_videos',
                    season_category_url=season_category_url,
                    season_url=params.season_url,
                    season_category_title=season_category_title,
                    page='1',
                    window_title=season_category_title
                ),
            })

    return common.plugin.create_listing(
        shows,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
    )


@common.plugin.cached(common.cache_time)
def list_videos(params):
    videos = []

    # flag_category case
    if 'flag_category' in params.season_category_url:
        program_html = utils.get_webcontent(
            url_root + params.season_url
        )
        program_soup = bs(program_html, 'html.parser')

        videos_soup = program_soup.find_all(
            'div',
            attrs={'class': 'thumbnail', 'itemprop': 'video'})
        for video in videos_soup:
            current_flag_category = video.find(
                'a',
                attrs={'class': 'flag-category'}).get_text().encode('utf-8')
            if current_flag_category == '':
                current_flag_category = 'No name'
            if current_flag_category and current_flag_category \
                    == params.season_category_title:

                title_soup = video.find(
                    'h3',
                    class_='thumbnail-title')
                url = title_soup.find('a')['href'].encode('utf-8')

                title = title_soup.get_text().encode('utf-8')
                title = ' '.join(title.split())

                img = video.find('img')['src'].encode('utf-8')
                try:
                    date = video.find('time').get_text()
                    date = date.encode('utf-8').split(' ')[1]
                    date_splited = date.split('/')
                    day = date_splited[0]
                    mounth = date_splited[1]
                    year = date_splited[2]
                    # date : string (%d.%m.%Y / 01.01.2009)
                    # aired : string (2008-12-07)
                    date = '.'.join((day, mounth, year))
                    aired = '-'.join((year, mounth, day))
                except:
                    date = ''
                    aired = ''
                    year = ''

                info = {
                    'video': {
                        'title': title,
                        'aired': aired,
                        'date': date,
                        'year': year,
                        'mediatype': 'tvshow'
                    }
                }

                videos.append({
                    'label': title,
                    'thumb': img,
                    'url': common.plugin.get_url(
                        action='channel_entry',
                        next='play',
                        url_video=url
                    ),
                    'is_playable': True,
                    'info': info
                })
    # others url case
    else:
        program_html = utils.get_webcontent(
            url_root + params.season_category_url + '?page=' + params.page
        )
        program_soup = bs(program_html, 'html.parser')

        videos_soup = program_soup.find_all(
            'div',
            attrs={'class': 'item col-xs-6 col-md-4'})
        for video in videos_soup:

            title_soup = video.find(
                'h3',
                class_='thumbnail-title')
            url = title_soup.find('a')['href'].encode('utf-8')

            title = title_soup.get_text().encode('utf-8')
            title = ' '.join(title.split())

            img = video.find('img')['src'].encode('utf-8')
            try:
                date = video.find('time').get_text()
                date = date.encode('utf-8').split(' ')[1]
            except:
                date = video.find('time').get_text().encode('utf-8')

            date_splited = date.split('/')
            day = date_splited[0]
            mounth = date_splited[1]
            year = date_splited[2]

            date = '.'.join((day, mounth, year))
            aired = '-'.join((year, mounth, day))
            # date : string (%d.%m.%Y / 01.01.2009)
            # aired : string (2008-12-07)
            info = {
                'video': {
                    'title': title,
                    'aired': aired,
                    'date': date,
                    'year': year,
                    'mediatype': 'tvshow'
                }
            }

            videos.append({
                'label': title,
                'thumb': img,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='play',
                    url_video=url
                ),
                'is_playable': True,
                'info': info
            })

        # More videos...
        videos.append({
            'label': common.addon.get_localized_string(30100),
            'url': common.plugin.get_url(
                action='channel_entry',
                next='list_videos',
                season_category_url=params.season_category_url,
                season_url=params.season_url,
                season_category_title=params.season_category_title,
                page=str(int(params.page) + 1),
                window_title=params.window_title
            )

        })

    return common.plugin.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE
        ),
        content='tvshows')


@common.plugin.cached(common.cache_time)
def get_video_url(params):
    if url_root in params.url_video:
        url_video = params.url_video
    else:
        url_video = url_root + params.url_video
    video_html = utils.get_webcontent(
        url_video)
    video_soup = bs(video_html, 'html.parser')
    return video_soup.find(
        'meta',
        attrs={'itemprop': 'contentUrl'})['content'].encode('utf-8')
