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
    * France TV Education
'''

URL_ROOT_EDUCATION = 'http://education.francetv.fr'

URL_VIDEO_DATA_EDUCATION = URL_ROOT_EDUCATION + '/video/%s/sisters'
# TitleVideo

URL_SERIE_DATA_EDUCATION = URL_ROOT_EDUCATION + '/recherche?q=%s&type=video&xtmc=%s'
# TitleSerie, page

CATEGORIES_EDUCATION = {
    'Séries': URL_ROOT_EDUCATION + '/recherche?q=&type=series&page=%s',
    'Vidéos': URL_ROOT_EDUCATION + '/recherche?q=&type=video&page=%s'
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
    for category_title, category_url in CATEGORIES_EDUCATION.iteritems():

        if category_title == 'Séries':
            next_value = 'list_programs'
        else:
            next_value = 'list_videos'

        item = Listitem()
        item.label = category_title
        item.set_callback(
            eval(next_value),
            item_id=item_id,
            next_url=category_url,
            page='1')
        yield item


@Route.register
def list_programs(plugin, item_id, next_url, page):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(next_url % page)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find(
        'div', class_='center-block bloc-thumbnails').find_all(
            'div', class_=re.compile("col-xs-3"))

    for program_datas in list_programs_datas:
        program_data_content = program_datas.find(
            'div', class_='ftve-thumbnail ').get('data-contenu')
        program_title = program_datas.find(
            'h4').find('a').get('title')
        program_image = program_datas.find(
            'div', class_='thumbnail-img lazy').get('data-original')
        program_url = URL_SERIE_DATA_EDUCATION % (
            program_data_content, program_data_content) + '&page=%s'

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(
            list_videos,
            item_id=item_id,
            next_url=program_url,
            page='1')
        yield item

    yield Listitem.next_page(
        item_id=item_id,
        next_url=next_url,
        page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, next_url, page):

    resp = urlquick.get(next_url % page)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find(
        'div', class_='center-block bloc-thumbnails').find_all(
            'div', class_=re.compile("col-xs-3"))

    for video_data in list_videos_datas:
        video_title = video_data.find('h4').find(
            'a').get('title')
        video_image = video_data.find(
            'div', class_='thumbnail-img lazy').get('data-original')
        video_data_contenu = video_data.find(
            'div', class_='ftve-thumbnail ').get('data-contenu')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_data_contenu=video_data_contenu,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_data_contenu=video_data_contenu,
            item_dict=cqu.item2dict(item))
        yield item

    yield Listitem.next_page(
        item_id=item_id,
        next_url=next_url,
        page=str(int(page) + 1))


@Resolver.register
def get_video_url(
        plugin, item_id, video_data_contenu, item_dict,
        download_mode=False, video_label=None):

    resp = urlquick.get(URL_VIDEO_DATA_EDUCATION % video_data_contenu)
    id_diffusion = re.compile(
        r'videos.francetv.fr\/video\/(.*?)\@'
        ).findall(resp.text)[0]
    return resolver_proxy.get_francetv_video_stream(
        plugin, id_diffusion, item_dict, download_mode, video_label)
