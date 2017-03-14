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
from resources.lib import utils
from resources.lib import common


def channel_entry(params):
    if 'list_shows' in params.next:
        return list_shows(params)
    elif 'list_videos' in params.next:
        return list_videos(params)
    elif 'play' in params.next:
        return get_video_URL(params)


url_category_query = 'http://service.itele.fr/iphone/categorie_news?query='


categories = {
    'http://service.itele.fr/iphone/topnews': 'La Une',
    url_category_query + 'FRANCE': 'France',
    url_category_query + 'MONDE': 'Monde',
    url_category_query + 'POLITIQUE': 'Politique',
    url_category_query + 'JUSTICE': 'Justice',
    url_category_query + 'ECONOMIE': 'Économie',
    url_category_query + 'SPORT': 'Sport',
    url_category_query + 'CULTURE': 'Culture',
    url_category_query + 'INSOLITE': 'Insolite'
}

#@common.plugin.cached(common.cache_time)
def list_shows(params):
    # Create categories list
    shows = []

    if params.next == 'list_shows_1':
        for category_url, category_title in categories.iteritems():
            shows.append({
                'label': category_title,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    category_url=category_url,
                    next='list_videos_cat',
                    title=category_title
                )
            })

        shows.append({
            'label': 'Les Émissions',
            'url': common.plugin.get_url(
                action='channel_entry',
                category_url='emissions',
                next='list_shows_emissions',
                title='Les Émissions'
            )
        })

        return common.plugin.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )

    elif params.next == 'list_shows_emissions':
        shows.append({
            'label': 'À la Une',
            'url': common.plugin.get_url(
                action='channel_entry',
                category_url='http://service.itele.fr/iphone/dernieres_emissions?query=',
                next='list_videos_cat',
                title='À la Une'
            )
        })

        shows.append({
            'label': 'Magazines',
            'url': common.plugin.get_url(
                action='channel_entry',
                category_url='http://service.itele.fr/iphone/emissions?query=magazines',
                next='list_videos_cat',
                title='Magazines'
            )
        })

        shows.append({
            'label': 'Chroniques',
            'url': common.plugin.get_url(
                action='channel_entry',
                category_url='http://service.itele.fr/iphone/emissions?query=chroniques',
                next='list_videos_cat',
                title='Chroniques'
            )
        })

        return common.plugin.create_listing(
            shows,
            sort_methods=(
                common.sp.xbmcplugin.SORT_METHOD_UNSORTED,
                common.sp.xbmcplugin.SORT_METHOD_LABEL
            )
        )


def list_videos(params):
    videos = []
    if params.next == 'list_videos_cat':
        file_path = utils.download_catalog(
            params.category_url,
            '%s_%s.json' % (params.channel_name, params.title))
        file = open(file_path).read()
        json_category = json.loads(file)

        if 'news' in json_category:
            json_category = json_category['news']
        elif 'videos' in json_category:
            json_category = json_category['videos']
        elif 'topnews' in json_category:
            json_category = json_category['topnews']
        for video in json_category:
            video_id = video['id_pfv'].encode('utf-8')
            category = video['category'].encode('utf-8')
            date_time = video['date'].encode('utf-8')  # 2017-02-10 22:05:02
            title = video['title'].encode('utf-8')
            description = video['description'].encode('utf-8')
            thumb = video['preview169'].encode('utf-8')
            video_url = video['video_urlhd'].encode('utf-8')
            if not video_url:
                video_url = 'no_video'

            info = {
                'video': {
                    'title': title,
                    'plot': description,
                    # 'aired': aired,
                    # 'date': date,
                    #'duration': duration,
                    #'year': year,
                    'genre': category
                }
            }

            videos.append({
                'label': title,
                'thumb': thumb,
                'url': common.plugin.get_url(
                    action='channel_entry',
                    next='play',
                    video_id=video_id,
                    video_urlhd=video_url
                ),
                'is_playable': True,
                'info': info
            })

    return common.plugin.create_listing(
        videos,
        sort_methods=(
            common.sp.xbmcplugin.SORT_METHOD_DATE,
            common.sp.xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            common.sp.xbmcplugin.SORT_METHOD_GENRE,
            common.sp.xbmcplugin.SORT_METHOD_UNSORTED
        ),
        content='tvshows')


def get_video_URL(params):
    return params.video_urlhd

