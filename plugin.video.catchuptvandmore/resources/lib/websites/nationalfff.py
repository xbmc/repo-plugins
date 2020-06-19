# -*- coding: utf-8 -*-
'''
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
'''
# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

import re
import json

from codequick import Route, Resolver, Listitem
import urlquick


from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://ffftv.fff.fr'

URL_REPLAY = URL_ROOT + '/playback/loadmore/national/%s'

# TODO Add Live


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    item = Listitem()
    item.label = plugin.localize(30701)
    item.set_callback(list_videos, item_id=item_id, page='0')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):
    """Build videos listing"""

    resp = urlquick.get(URL_REPLAY % page)
    root = resp.parse()

    for video_datas in root.iterfind(".//a"):
        if video_datas.get('href') is not None:
            video_title = video_datas.find('.//h3').text
            video_image = video_datas.find('.//img').get('src')
            video_url = URL_ROOT + video_datas.get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            if 'overlayDescription' in video_datas:
                date_value = video_datas['overlayDescription'].split('|')[0]
                item.info.date(date_value, '%d/%m/%Y')

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    yield Listitem.next_page(item_id=item_id, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    root = resp.parse()
    video_datas = root.find(".//video[@class='player-fff vjs-fluid video-js margin_b16 resp_iframe']")

    data_account = video_datas.get('data-account')
    data_video_id = video_datas.get('data-video-id')
    data_player = video_datas.get('data-player')

    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id,
                                                    download_mode)
