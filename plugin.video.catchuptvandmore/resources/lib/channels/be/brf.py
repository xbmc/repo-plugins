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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import re
import urlquick

# TO DO
# ...

URL_ROOT_BRF = 'https://m.brf.be/'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_ROOT_BRF)
    root = resp.parse("ul", attrs={"class": "off-canvas-list"})

    for category_data in root.iterfind(".//a"):

        if 'http' in category_data.get('href'):
            category_title = category_data.text
            category_url = category_data.get('href')

            item = Listitem()
            item.label = category_title
            item.set_callback(list_videos,
                              item_id=item_id,
                              category_url=category_url,
                              page='1')
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url + 'page/%s' % page)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//article[@class='post column small-12 medium-6 large-4 left']"):
        video_title = video_datas.find('.//a').get('title')
        video_image = video_datas.find('.//a').find('.//img').get('src')
        duration_list_value = video_datas.find('.//time').text.split(
            '-')[1].strip().split(':')
        video_duration = int(duration_list_value[0]) * 60 + int(
            duration_list_value[1])
        date_list_value = video_datas.find('.//time').text.split(
            '-')[0].strip().split('.')
        if len(date_list_value[0]) == 1:
            day = "0" + date_list_value[0]
        else:
            day = date_list_value[0]
        if len(date_list_value[1]) == 1:
            month = "0" + date_list_value[1]
        else:
            month = date_list_value[1]
        year = date_list_value[2]
        date_value = year + '-' + month + '-' + day
        video_url = video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['duration'] = video_duration
        item.info.date(date_value, '%Y-%m-%d')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)
    stream_datas_url = re.compile(r'jQuery.get\("(.*?)"').findall(resp.text)[0]
    resp2 = urlquick.get(stream_datas_url)
    final_video_url = re.compile(r'src="(.*?)"').findall(resp2.text)[0]

    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url
