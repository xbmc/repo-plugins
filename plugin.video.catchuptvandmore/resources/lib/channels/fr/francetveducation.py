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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info

import json
import re
import urlquick
'''
Channels:
    * France TV Education
'''

# Add search button

URL_ROOT_EDUCATION = 'http://education.francetv.fr'

URL_VIDEO_DATA_EDUCATION = URL_ROOT_EDUCATION + '/video/%s/sisters'
# TitleVideo

URL_SERIE_DATA_EDUCATION = URL_ROOT_EDUCATION + '/recherche?q=%s&type=video&xtmc=%s'
# TitleSerie, page

CATEGORIES_EDUCATION = {
    'Séries': URL_ROOT_EDUCATION + '/recherche?q=&type=series&page=%s',
    'Vidéos': URL_ROOT_EDUCATION + '/recherche?q=&type=video&page=%s'
}


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    for category_title, category_url in list(CATEGORIES_EDUCATION.items()):

        if category_title == 'Séries':
            next_value = 'list_programs'
        else:
            next_value = 'list_videos'

        item = Listitem()
        item.label = category_title
        item.set_callback(eval(next_value),
                          item_id=item_id,
                          next_url=category_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, next_url, page, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(next_url % page)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='ftve-thumbnail ']"):
        program_data_content = program_datas.get('data-contenu')
        program_title = program_datas.find('.//h4').find('.//a').get('title')
        program_image = program_datas.find(
            ".//div[@class='thumbnail-img lazy']").get('data-original')
        program_url = URL_SERIE_DATA_EDUCATION % (
            program_data_content, program_data_content) + '&page=%s'

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          next_url=program_url,
                          page='1')
        item_post_treatment(item)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             next_url=next_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, next_url, page, **kwargs):

    resp = urlquick.get(next_url % page)
    root = resp.parse()

    for video_data in root.iterfind(".//div[@class='ftve-thumbnail ']"):
        video_title = video_data.find('.//h4').find('.//a').get('title')
        video_image = video_data.find(
            ".//div[@class='thumbnail-img lazy']").get('data-original')
        video_data_contenu = video_data.get('data-contenu')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_data_contenu=video_data_contenu)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             next_url=next_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_data_contenu,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(URL_VIDEO_DATA_EDUCATION % video_data_contenu)
    id_diffusion = re.compile(r'videos.francetv.fr\/video\/(.*?)\@').findall(
        resp.text)[0]
    return resolver_proxy.get_francetv_video_stream(plugin, id_diffusion,
                                                    download_mode)
