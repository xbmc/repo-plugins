# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
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
import resources.lib.cq_utils as cqu

from bs4 import BeautifulSoup as bs

import json
import re
import urlquick


'''
Channels:
    * France TV CultureBox
'''

URL_ROOT = 'https://culturebox.francetvinfo.fr'

URL_VIDEOS = URL_ROOT + '/videos/'


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
    resp = urlquick.get(URL_VIDEOS)
    root_soup = bs(resp.text, 'html.parser')
    list_categories_datas = root_soup.find(
        'nav').find_all('a')

    for category_datas in list_categories_datas:
        if '/videos/' in category_datas.get('href'):
            category_title = category_datas.text
            category_url = URL_ROOT + category_datas.get(
                'href') + '?sort_by=field_live_published_date_value&sort_order=DESC&page=%s'

            item = Listitem()
            item.label = category_title
            item.set_callback(
                list_videos,
                item_id=item_id,
                category_url=category_url,
                page='0')
            yield item


@Route.register
def list_videos(plugin, item_id, category_url, page):

    resp = urlquick.get(category_url % page)
    root_soup = bs(resp.text, 'html.parser')
    if root_soup.find('ul', class_="live-article-list"):
        list_videos_datas = root_soup.find(
            'ul', class_="live-article-list").find_all(
                'div', class_="img")
        for video_data in list_videos_datas:
            video_title = video_data.find('img').get('alt')
            video_image = video_data.find('img').get('data-frz-src')
            video_url = URL_ROOT + video_data.find('a').get('href')

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

    yield Listitem.next_page(
        item_id=item_id,
        category_url=category_url,
        page=str(int(page) + 1))


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, item_dict=None, download_mode=False, video_label=None):

    resp = urlquick.get(video_url, max_age=-1)
    if re.compile(r'videos.francetv.fr\/video\/(.*?)\@').findall(resp.text):
        id_diffusion = re.compile(
            r'videos.francetv.fr\/video\/(.*?)\@').findall(resp.text)[0]
    else:
        plugin.notify('ERROR', plugin.localize(30716))
        return False
    return resolver_proxy.get_francetv_video_stream(
        plugin, id_diffusion, item_dict, download_mode, video_label)
