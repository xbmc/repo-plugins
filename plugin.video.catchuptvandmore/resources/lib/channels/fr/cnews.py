# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
    Copyright (C) 2016  SylvainCecchetto

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

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS

from resources.lib import web_utils
from resources.lib import resolver_proxy

from bs4 import BeautifulSoup as bs

import re
import json
import urlquick


# TO DO
# Fix some encodage (HTML not well formated)

# URL :
URL_ROOT_SITE = 'http://www.cnews.fr'

# Live :
URL_LIVE_CNEWS = URL_ROOT_SITE + '/le-direct'

# Replay CNews
URL_REPLAY_CNEWS = URL_ROOT_SITE + '/replay'
URL_EMISSIONS_CNEWS = URL_ROOT_SITE + '/service/dm_loadmore/dm_emission_index_emissions/%s/10/0'
# num Page
URL_VIDEOS_CNEWS = URL_ROOT_SITE + '/service/dm_loadmore/dm_emission_index_sujets/%s/15/0'
# num Page

# Replay/Live => VideoId
URL_INFO_CONTENT = 'https://secure-service.canal-plus.com/' \
                   'video/rest/getVideosLiees/cplus/%s?format=json'


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_REPLAY_CNEWS)
    root_soup = bs(resp.text, 'html.parser')
    menu_soup = root_soup.find('menu', class_="index-emission-menu")
    categories_soup = menu_soup.find_all('li')

    for category in categories_soup:
        category_name = category.get_text()
        if 'mission' in category_name:
            category_url = URL_EMISSIONS_CNEWS
        else:
            category_url = URL_VIDEOS_CNEWS

        if category_name != 'Les tops':
            item = Listitem()
            item.label = category_name
            item.set_callback(
                list_videos,
                item_id=item_id,
                category_url=category_url,
                page='0')
            yield item


@Route.register
def list_videos(plugin, item_id, category_url, page):

    resp = urlquick.get(category_url % page).text
    resp = resp.replace('\n\r','').replace(
        '\\"','"').replace('\\/','/').replace(
            '\\u00e9','é').replace('\\u00ea','ê').replace(
                '&#039;','\'').replace('\\u00e8','è').replace(
                    '\\u00e7','ç').replace('\\u00ab','\"').replace(
                        '\\u00bb','\"').replace('\\u00e0','à').replace(
                            '\\u00c9','É').replace('\\u00ef','ï').replace(
                                '\\u00f9','ù').replace('\\u00c0','À').replace(
                                    '\\u00c7','Ç').replace('\\u0153','œ').replace(
                                        '\\u2019', '’').replace('\\u00a0',' ').replace(
                                            '\\u2026', '...').replace('\\u00f4','ô').replace(
                                                '\\u00e2', 'â')
    root_soup = bs(resp, 'html.parser')
    programs = root_soup.find_all('a', class_='video-item-wrapper')
    programs += root_soup.find_all('a', class_='emission-item-wrapper')

    for program in programs:
        title = ''
        if program.find('span', class_='emission-title'):
            title = program.find(
                'span', class_='emission-title').get_text()
        elif program.find('span', class_='video-title'):
            title = program.find(
                'span', class_='video-title').get_text()
        description = ''
        if program.find('p'):
            description = program.find(
                'p').get_text()
        thumb = program.find('img').get('data-src')
        video_url = URL_ROOT_SITE + program.get('href')

        item = Listitem()
        item.label = title
        item.art['thumb'] = thumb
        item.info['plot'] = description

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        yield item

    # More videos...
    yield Listitem.next_page(
        item_id=item_id,
        category_url=category_url,
        page=str(int(page) + 1))


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(
        video_url,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    video_id = re.compile(
        r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(
            resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(
        plugin, video_id, download_mode, video_label)


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(
        URL_LIVE_CNEWS,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    live_id = re.compile(
        r'dailymotion.com/embed/video/(.*?)[\?\"]',
        re.DOTALL).findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
