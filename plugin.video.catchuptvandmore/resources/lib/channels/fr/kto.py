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
from resources.lib.listitem_utils import item_post_treatment, item2dict

import re
import urlquick
'''
TODO Info replays (date, duration, ...)
'''

URL_ROOT = 'http://www.ktotv.com'

URL_SHOWS = URL_ROOT + '/emissions'


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
    resp = urlquick.get(URL_SHOWS)
    root = resp.parse()

    for category_datas in root.iterfind(".//div[@class='col-md-4 ProgramList-sub']"):
        category_title = category_datas.find(".//img").get('alt')
        category_image = category_datas.find(".//img").get('src')

        item = Listitem()
        item.label = category_title
        item.art['thumb'] = category_image
        item.set_callback(list_programs,
                          item_id=item_id,
                          category_title=category_title)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_title, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_SHOWS)
    root = resp.parse()

    for category_datas in root.iterfind(".//div[@class='col-md-4 ProgramList-sub']"):
        if category_title in category_datas.find(".//img").get('alt'):
            for program_datas in category_datas.findall(".//a"):
                if 'emissions' in program_datas.get('href'):
                    program_title = program_datas.text
                    program_url = URL_ROOT + program_datas.get('href')

                    item = Listitem()
                    item.label = program_title
                    item.set_callback(list_videos,
                                      item_id=item_id,
                                      program_url=program_url,
                                      page='1')
                    item_post_treatment(item)
                    yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    resp = urlquick.get(program_url + '?page=%s' % page)
    root = resp.parse()

    if page == '1':
        video_title = root.find(".//div[@class='container content']").find(
            './/h3').find('.//a').text
        video_image = root.find(".//div[@class='container content']").find(
            './/img').get('src')
        video_url = root.find(".//div[@class='container content']").find(
            './/a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          item_id=item_id,
                          video_url=video_url)
        yield item

    for video_datas in root.iterfind(
            ".//div[@class='media-by-category-container']"):
        video_title = video_datas.find('.//img').get('title')
        video_image = video_datas.find('.//img').get('src')
        video_url = URL_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             program_url=program_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua},
                        max_age=-1)
    video_id = re.compile(r'www.youtube.com/embed/(.*?)[\?\"]').findall(
        resp.text)[0]

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode,
                                             video_label)


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua},
                        max_age=-1)
    list_url_stream = re.compile(r'videoUrl = \'(.*?)\'').findall(resp.text)
    url_live = ''
    for url_stream_data in list_url_stream:
        if 'm3u8' in url_stream_data:
            url_live = url_stream_data
    return url_live
