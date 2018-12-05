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

# TO DO
# ....


URL_ROOT = 'http://www.j-one.com'
# ChannelName

URL_VIDEOS = URL_ROOT + '/category/videos/page/%s/'
# PageId


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
    item = Listitem()
    item.label = plugin.localize(LABELS['All videos'])
    item.set_callback(
        list_videos,
        item_id=item_id,
        page='1')
    yield item


@Route.register
def list_videos(plugin, item_id, page):

    resp = urlquick.get(URL_VIDEOS % page)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all(
        'article', class_=re.compile('item-list'))

    for video_datas in list_videos_datas:
        video_title = video_datas.find('h2').text
        video_image = video_datas.find('img').get('src')
        video_plot = ''
        if video_datas.find('p'):
            video_plot = video_datas.find('p').text
        video_url = video_datas.find('a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot

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
        page=str(int(page) + 1))


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(
        video_url,
        headers={'User-Agent': web_utils.get_random_ua},
        max_age=-1)
    video_uri = re.compile(
        r'uri\: \'(.*?)\'').findall(resp.text)[0]
    account_override = 'intl.mtvi.com'

    return resolver_proxy.get_mtvnservices_stream(
        plugin, video_uri, account_override, download_mode, video_label)
