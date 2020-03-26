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

URL_ROOT_EDUCATION = 'https://www.lumni.fr'

URL_CONTENUS = URL_ROOT_EDUCATION + '/%s/tous-les-contenus'
# TitleVideo

CATEGORIES_EDUCATION = {
    'Primaire': URL_CONTENUS % 'primaire',
    'Collège': URL_CONTENUS % 'college',
    'Lycée': URL_CONTENUS % 'lycee'
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

        item = Listitem()
        item.label = category_title
        item.set_callback(list_contents,
                          item_id=item_id,
                          category_url=category_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_contents(plugin, item_id, category_url, page, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(category_url + '?page=%s' % page)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='serie']"):

        program_title = program_datas.find(".//a").get('title')
        program_image = program_datas.findall(".//img")[1].get('data-src')
        program_url = URL_ROOT_EDUCATION + program_datas.find(".//a").get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          next_url=program_url)
        item_post_treatment(item)
        yield item

    for program_datas in root.iterfind(".//div[@class='video']"):

        program_title = program_datas.find(".//div[@class='video-txt']/p").text.strip()
        program_image = program_datas.find(".//img").get('data-src')
        program_url = URL_ROOT_EDUCATION + program_datas.find(".//a").get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(get_video_url,
                          item_id=item_id,
                          next_url=program_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, next_url, **kwargs):

    resp = urlquick.get(next_url)
    root = resp.parse("div",
                      attrs={"class": "contenu-capsule"})

    for video_data in root.iterfind(".//a"):
        video_title = video_data.find(".//div[@class='capsule-text']/p").text.strip()
        video_image = video_data.find(".//img").get('data-src')
        video_url = URL_ROOT_EDUCATION + video_data.get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          next_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  next_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(next_url)
    id_diffusion = re.compile(r'data-factoryid\=\"(.*?)\"').findall(
        resp.text)[0]
    return resolver_proxy.get_francetv_video_stream(plugin, id_diffusion,
                                                    download_mode)
