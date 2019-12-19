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
from resources.lib.listitem_utils import item_post_treatment, item2dict

import htmlement
import re
import urlquick

# TO DO

# URL :
URL_ROOT_SITE = 'https://www.cnews.fr'

# Live :
URL_LIVE_CNEWS = URL_ROOT_SITE + '/le-direct'

# Replay CNews
URL_REPLAY_CNEWS = URL_ROOT_SITE + '/replay'
URL_EMISSIONS_CNEWS = URL_ROOT_SITE + '/service/dm_loadmore/dm_emission_index_emissions/%s/0'
# num Page
URL_VIDEOS_CNEWS = URL_ROOT_SITE + '/service/dm_loadmore/dm_emission_index_sujets/%s/0'
# num Page


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
    resp = urlquick.get(URL_REPLAY_CNEWS)
    root = resp.parse("menu", attrs={"class": "index-emission-menu"})

    for category in root.iterfind("ul/li"):
        if category.find('a') is not None:
            category_name = category.find('a').text
        else:
            category_name = category.text
        if 'mission' in category_name:
            category_url = URL_EMISSIONS_CNEWS
        else:
            category_url = URL_VIDEOS_CNEWS

        if category_name != 'Les tops':
            item = Listitem()
            item.label = category_name
            item.set_callback(list_videos,
                              item_id=item_id,
                              category_url=category_url,
                              page='0')
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url % page)
    parser = htmlement.HTMLement()
    parser.feed(resp.json())
    data = parser.close()

    for video_datas in data.iterfind(".//a"):
        video_title = video_datas.find('.//img').get('title')
        video_image = video_datas.find('.//img').get('data-echo')
        video_url = URL_ROOT_SITE + video_datas.get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(
        resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode, video_label)


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.get(URL_LIVE_CNEWS,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    live_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]',
                         re.DOTALL).findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
