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

from builtins import str
from resources.lib.codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import re
from resources.lib import urlquick

# TO DO

URL_ROOT = 'http://www.afriquemedia.tv'

URL_LIVE = URL_ROOT + '/live'

URL_REPLAY = URL_ROOT + '/replay?jut1=%s'
# page


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
    item = Listitem()
    item.label = plugin.localize(LABELS['All videos'])
    item.set_callback(list_videos, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):

    resp = urlquick.get(URL_REPLAY % page)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='yt-fp-outer outerwidthlarge3 outerwidthsmall1 rounding7']"
    ):
        video_title = video_datas.find('.//img').get('alt')
        video_image = video_datas.find('.//img').get('src')
        video_id = video_datas.find('.//a').get('href').split('?v=')[1]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
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

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    live_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(
        resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
