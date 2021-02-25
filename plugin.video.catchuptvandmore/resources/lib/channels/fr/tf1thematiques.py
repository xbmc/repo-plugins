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
from builtins import range
from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib import download
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import inputstreamhelper
import json
import re
import os
import urlquick
from kodi_six import xbmcgui

# TO DO
# Move WAT to resolver.py (merge with mytf1 code)

URL_ROOT = 'https://www.%s.fr'
# ChannelName

URL_VIDEOS = 'https://www.%s.fr/videos'
# PageId


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(30701)
    if item_id == 'histoire':
        item.set_callback(list_videos, item_id=item_id, page='0')
    else:
        item.set_callback(list_videos, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):

    resp = urlquick.get(URL_VIDEOS % item_id)
    if item_id == 'tvbreizh':
        resp = urlquick.get(URL_VIDEOS % item_id)
    else:
        resp = urlquick.get(URL_VIDEOS % item_id + '?page=%s' % page)
    root = resp.parse("div", attrs={"class": "view-content"})

    for video_datas in root.iterfind("./div"):
        video_title = video_datas.find(".//span[@class='field-content']").find(
            './/a').text
        video_plot = ''
        if video_datas.find(".//div[@class='field-resume']") is not None:
            video_plot = video_datas.find(
                ".//div[@class='field-resume']").text.strip()
        video_image = URL_ROOT % item_id + \
            video_datas.find('.//img').get('src')
        video_url = URL_ROOT % item_id + '/' + \
            video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if 'tvbreizh' not in item_id:
        yield Listitem.next_page(item_id=item_id, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(r'player.vimeo.com/video/(.*?)[\?\"]').findall(
        resp.text)[0]
    return resolver_proxy.get_stream_vimeo(plugin, video_id, download_mode)
