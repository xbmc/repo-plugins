# -*- coding: utf-8 -*-
'''
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
'''
# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from builtins import str
import json
import re

from codequick import Route, Resolver, Listitem
import htmlement
import requests
import urlquick

from resources.lib.labels import LABELS
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://live.philharmoniedeparis.fr'

URL_REPLAYS = URL_ROOT + '/misc/AjaxListVideo.ashx?/Concerts/%s'

URL_STREAM = URL_ROOT + '/otoPlayer/config.ashx?id=%s'


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(LABELS['All videos'])
    item.set_callback(list_videos, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):
    """Add modes in the listing"""

    resp = requests.get(URL_REPLAYS % page)
    parser = htmlement.HTMLement()
    parser.feed(resp.text)
    root = parser.close()

    for video_datas in root.iterfind(".//li"):
        if 'concert' in video_datas.get('class'):
            video_title = video_datas.find('.//a').get('title')
            video_image = URL_ROOT + re.compile(r'url\((.*?)\)').findall(
                video_datas.find(".//div[@class='imgContainer']").get('style'))[0]
            video_id = re.compile(r'concert\/(.*?)\/').findall(
                video_datas.find('.//a').get('href'))[0]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(
                get_video_url,
                item_id=item_id,
                video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    yield Listitem.next_page(item_id=item_id, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""

    resp = requests.get(URL_STREAM % video_id)
    json_parser = json.loads(resp.text)
    final_url = URL_ROOT + json_parser["files"]["desktop"]["file"]

    if download_mode:
        return download.download_video(final_url)
    return final_url
