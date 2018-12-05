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

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download


from bs4 import BeautifulSoup as bs

import json
import re
import urlquick

# TO DO
# Download Mode / QUality Mode


URL_TIVI5MONDE_ROOT = 'http://www.tivi5mondeplus.com'

URL_TV5MONDE_LIVE = 'http://live.tv5monde.com/'

LIST_LIVE_TV5MONDE = {
    'tivi5monde': 'tivi5monde'
}

CATEGORIES_VIDEOS_TIVI5MONDE = {
    '/series/decouverte': 'REPLAY PROGRAMMES JEUNESSE DÉCOUVERTE',
    '/decouverte': 'LES DERNIERS ÉPISODES DE TES ÉMISSIONS DÉCOUVERTE',
    '/series/dessins-animes': 'REPLAY DESSINS ANIMÉS',
    '/dessins-animes': 'LES DERNIERS ÉPISODES DE TES DESSINS ANIMÉS PRÉFÉRÉS'
}


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
    for category_context, category_title in CATEGORIES_VIDEOS_TIVI5MONDE.iteritems():
        category_url = URL_TIVI5MONDE_ROOT + category_context
        if 'REPLAY' in category_title:
            next_value = 'list_programs'
        else:
            next_value = 'list_videos'
        item = Listitem()
        item.label = category_title
        item.set_callback(
            eval(next_value),
            item_id=item_id,
            next_url=category_url,
            page='0')
        yield item

    # Search videos
    item = Listitem.search(
        list_videos_search,
        item_id=item_id,
        page='0')
    yield item


@Route.register
def list_programs(plugin, item_id, next_url, page):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(next_url + '?page=%s' % page)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find_all(
        'div', class_='views-field views-field-nothing')
    for program_datas in list_programs_datas:
        program_title = program_datas.find('h3').find(
            'a').get_text().strip()
        program_url = URL_TIVI5MONDE_ROOT + program_datas.find(
            'a').get('href')
        program_image = program_datas.find('img').get('src')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(
            list_videos,
            item_id=item_id,
            next_url=program_url,
            page='0')
        yield item

    yield Listitem.next_page(
        item_id=item_id,
        next_url=next_url,
        page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, next_url, page):

    resp = urlquick.get(next_url + '?page=%s' % page)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_='row-vignette')

    for video_datas in list_videos_datas:
        video_title = video_datas.find('img').get('alt')
        video_image = video_datas.find('img').get('src')
        video_url = URL_TIVI5MONDE_ROOT + video_datas.find(
            'a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

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

    yield Listitem.next_page(
        item_id=item_id,
        next_url=next_url,
        page=str(int(page) + 1))


@Route.register
def list_videos_search(plugin, search_query, item_id, page):

    resp = urlquick.get(URL_TIVI5MONDE_ROOT + '/recherche?search_api_views_fulltext=%s&page=%s' % (search_query, page))
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_='row-vignette')

    at_least_one_item = False
    for video_datas in list_videos_datas:
        at_least_one_item = True
        video_title = video_datas.find('img').get('alt')
        video_image = video_datas.find('img').get('src')
        video_url = URL_TIVI5MONDE_ROOT + video_datas.find(
            'a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

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

    if at_least_one_item:
        yield Listitem.next_page(
            item_id=item_id,
            search_query=search_query,
            page=str(int(page) + 1))
    else:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(video_url, headers={'User-Agent': web_utils.get_random_ua}, max_age=-1)
    stream_url = re.compile(
        'contentUrl\"\: \"(.*?)\"').findall(
        resp.text)[0]

    if download_mode:
        return download.download_video(stream_url, video_label)

    return stream_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    live_id = ''
    for channel_name, live_id_value in LIST_LIVE_TV5MONDE.iteritems():
        if item_id == channel_name:
            live_id = live_id_value
    resp = urlquick.get(URL_TV5MONDE_LIVE + '%s.html' % live_id, headers={'User-Agent': web_utils.get_random_ua}, max_age=-1)
    live_json = re.compile(
        r'data-broadcast=\'(.*?)\'').findall(resp.text)[0]
    json_parser = json.loads(live_json)
    return json_parser["files"][0]["url"]
