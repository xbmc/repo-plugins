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
import resources.lib.cq_utils as cqu

from bs4 import BeautifulSoup as bs

import json
import re
import urlquick

'''
Channels:
    * IRL
    * Studio 4
'''

URL_ROOT_NOUVELLES_ECRITURES = 'http://%s.nouvelles-ecritures.francetv.fr'
# channel name


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
    resp = urlquick.get(URL_ROOT_NOUVELLES_ECRITURES % item_id)
    root_soup = bs(resp.text, 'html.parser')
    list_categories_datas = root_soup.find_all(
        'li', class_='genre-item')
    for category_datas in list_categories_datas:

        category_title = category_datas.find('a').get_text().strip()
        category_data_panel = category_datas.get('data-panel')

        item = Listitem()
        item.label = category_title
        item.set_callback(
            list_programs,
            item_id=item_id,
            category_data_panel=category_data_panel)
        yield item


@Route.register
def list_programs(plugin, item_id, category_data_panel):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_ROOT_NOUVELLES_ECRITURES % item_id)
    root_soup = bs(resp.text, 'html.parser')
    class_panel_value = 'panel %s' % category_data_panel
    list_programs_datas = root_soup.find(
        'div', class_=class_panel_value).find_all('li')

    for program_datas in list_programs_datas:
        program_title = program_datas.find('a').text
        program_image = program_datas.find('a').get('data-img')
        program_url = URL_ROOT_NOUVELLES_ECRITURES % item_id + \
            program_datas.find('a').get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(
            list_videos,
            item_id=item_id,
            program_url=program_url)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url):

    resp = urlquick.get(program_url)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        "li", class_=re.compile("push type-episode"))

    for video_datas in list_videos_datas:
        if video_datas.find('div', class_='description'):
            video_title = video_datas.find(
                'div', class_='title').get_text().strip() + ' - ' + \
                video_datas.find(
                    'div', class_='description').get_text().strip()
        else:
            video_title = video_datas.find(
                'div', class_='title').get_text().strip()
        video_url = URL_ROOT_NOUVELLES_ECRITURES % item_id + \
            video_datas.find('a').get('href')
        video_image = ''
        if video_datas.find('img'):
            video_image = video_datas.find('img').get('src')

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
            video_url=video_url,
            item_dict=cqu.item2dict(item))
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, item_dict=None, download_mode=False, video_label=None):

    resp = urlquick.get(video_url)
    root_soup = bs(resp.text, 'html.parser')
    player_datas = root_soup.find(
        'div', class_='player-wrapper')

    if player_datas.find('a', class_='video_link'):
        id_diffusion = player_datas.find(
            'a', class_='video_link').get(
                'href').split('video/')[1].split('@')[0]
        return resolver_proxy.get_francetv_video_stream(
            plugin, id_diffusion, item_dict, download_mode, video_label)
    else:
        url_video_resolver = player_datas.find('iframe').get('src')
        # Case Youtube
        if 'youtube' in url_video_resolver:
            video_id = url_video_resolver.split(
                'youtube.com/embed/')[1]
            return resolver_proxy.get_stream_youtube(
                plugin, video_id, download_mode, video_label)

        # Case DailyMotion
        elif 'dailymotion' in url_video_resolver:
            video_id = url_video_resolver.split(
                'dailymotion.com/embed/video/')[1]
            return resolver_proxy.get_stream_dailymotion(
                plugin, video_id, download_mode, video_label)

        else:
            plugin.notify('ERROR', plugin.localize(30716))
            return False
