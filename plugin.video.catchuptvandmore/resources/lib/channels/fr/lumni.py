# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment


# Channels:
#     * France TV Education


# Add search button

URL_ROOT_EDUCATION = 'https://www.lumni.fr'

URL_CONTENUS = URL_ROOT_EDUCATION + '/%s/tous-les-contenus'
# TitleVideo

CATEGORIES_EDUCATION = {
    'Primaire': URL_CONTENUS % 'primaire',
    'Collège': URL_CONTENUS % 'college',
    'Lycée': URL_CONTENUS % 'lycee'
}


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

    for program_datas in root.iterfind(".//div[@class='card card--media   ']"):

        program_title = program_datas.find(".//p").text.strip()
        program_image = program_datas.findall(".//img")[1].get('data-src')
        program_url = URL_ROOT_EDUCATION + program_datas.find(".//a").get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(get_video_url, item_id=item_id, next_url=program_url)
        item_post_treatment(item)
        yield item

    for program_datas in root.iterfind(".//div[@class='card card--collection   ']"):

        program_title = program_datas.find(".//p").text.strip()
        program_image = program_datas.find(".//img").get('data-src')
        program_url = URL_ROOT_EDUCATION + program_datas.find(".//a").get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos, item_id=item_id, next_url=program_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id, category_url=category_url, page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, next_url, **kwargs):

    resp = urlquick.get(next_url)
    root = resp.parse()

    for video_data in root.iterfind(".//div[@class='card card--media   ']"):
        video_title = video_data.find(".//p").text.strip()
        video_image = video_data.find(".//img").get('data-src')
        video_url = URL_ROOT_EDUCATION + video_data.find(".//a").get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url, item_id=item_id, next_url=video_url)
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
