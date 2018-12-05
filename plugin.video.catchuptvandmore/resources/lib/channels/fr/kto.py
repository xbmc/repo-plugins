# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2018  SylvainCecchetto

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
import urlquick

'''
TODO Info replays (date, duration, ...)
'''

URL_ROOT = 'http://www.ktotv.com'

URL_SHOWS = URL_ROOT + '/emissions'


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
    resp = urlquick.get(URL_SHOWS)
    root_soup = bs(resp.text, 'html.parser')

    list_categories_datas = root_soup.find_all(
        'span', class_="programTitle")
    for category_datas in list_categories_datas:
        category_title = category_datas.text

        item = Listitem()
        item.label = category_title
        item.set_callback(
            list_programs,
            item_id=item_id,
            category_title=category_title)
        yield item


@Route.register
def list_programs(plugin, item_id, category_title):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_SHOWS)
    start = '%s</span>' % category_title.replace("'", "&#039;")
    end = '<span class="'
    sub_category_datas=(resp.text.split(start))[1].split(end)[0]
    sub_programs_datas_soup = bs(sub_category_datas, 'html.parser')
    list_programs_datas = sub_programs_datas_soup.find_all('a')
    for program_datas in list_programs_datas:
        if 'emissions' in program_datas.get('href'):
            program_title = program_datas.text
            program_url = URL_ROOT + program_datas.get('href')

            item = Listitem()
            item.label = program_title
            item.set_callback(
                list_videos,
                item_id=item_id,
                program_url=program_url,
                page='1')
            yield item


@Route.register
def list_videos(plugin, item_id, program_url, page):

    resp = urlquick.get(program_url + '?page=%s' % page)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'div', class_='media-by-category-container')

    if page == '1':
        video_title = root_soup.find(
            'div', class_="container content").find('a').text
        video_image = root_soup.find(
            'div', class_="container content").find('img').get('src')
        video_url = root_soup.find(
            'div', class_="container content").find('a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.art['fanart'] = video_image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            video_url=video_url)
        yield item

    for video_datas in list_videos_datas:
        video_title = video_datas.find('img').get('title')
        video_image = video_datas.find('img').get('src')
        video_url = URL_ROOT + video_datas.find('a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.art['fanart'] = video_image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            video_url=video_url)
        yield item

    yield Listitem.next_page(
        item_id=item_id,
        program_url=program_url,
        page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(
        video_url,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    video_id = re.compile(
        r'www.youtube.com/embed/(.*?)[\?\"]').findall(resp.text)[0]

    return resolver_proxy.get_stream_youtube(
        plugin, video_id, download_mode, video_label)


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(
        URL_ROOT, headers={'User-Agent': web_utils.get_random_ua}, max_age=-1)
    list_url_stream = re.compile(
        r'videoUrl = \'(.*?)\'').findall(resp.text)
    url_live = ''
    for url_stream_data in list_url_stream:
        if 'm3u8' in url_stream_data:
            url_live = url_stream_data
    return url_live
