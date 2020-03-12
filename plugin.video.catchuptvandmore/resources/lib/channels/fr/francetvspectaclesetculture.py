# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2019  SylvainCecchetto

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

import re
import urlquick
'''
Channels:
    * France TV Spectacles Et Culture
'''

# TODO
# Add duration, date of the video

URL_ROOT = 'https://www.france.tv'

URL_VIDEOS = URL_ROOT + '/spectacles-et-culture/'


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
    resp = urlquick.get(URL_VIDEOS)
    root = resp.parse(
        "div", attrs={
            "class": "c-section-sub-categories__contents h-flex"
        })

    for category_datas in root.iterfind(".//a"):
        category_title = category_datas.text
        category_url = URL_ROOT + category_datas.get('href')

        item = Listitem()
        item.label = category_title
        item.set_callback(
            list_videos, item_id=item_id, category_url=category_url, page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url + '?page=%s' % page)
    root = resp.parse()

    for video_data in root.iterfind(
            ".//div[@class='c-card-video js-card h-flex c-wall__item']"):
        video_title = video_data.get('title')
        video_image = ''
        if video_data.find('.//img') is not None:
            video_image = 'https:' + video_data.find('.//img').get('data-src')
        video_url = URL_ROOT + video_data.find('.//a').get('href')
        video_duration = 0  # TODO

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['duration'] = video_duration

        item.set_callback(
            get_video_url,
            item_id=item_id,
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
                  **kwargs):

    resp = urlquick.get(video_url, max_age=-1)
    if re.compile(r'videoId\"\:\"(.*?)\"').findall(resp.text):
        id_diffusion = re.compile(r'videoId\"\:\"(.*?)\"').findall(
            resp.text)[0]
    else:
        plugin.notify('ERROR', plugin.localize(30716))
        return False
    return resolver_proxy.get_francetv_video_stream(
        plugin, id_diffusion, download_mode)
