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


from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import re
import urlquick

# TODO
# Add more button

URL_ROOT = 'https://www.bfmtv.com'

URL_ROOT_REGION = 'https://www.bfmtv.com/%s'

URL_LIVE_BFM_REGION = URL_ROOT_REGION + '/en-direct/'

URL_REPLAY_BFM_REGION = URL_ROOT_REGION + '/videos/?page=%s'


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
    item.label = plugin.localize(30701)
    item.set_callback(list_videos, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):

    if 'paris' in item_id:
        resp = urlquick.get(URL_ROOT + '/mediaplayer/videos-bfm-paris/?page=%s' % page,
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)
    else:
        resp = urlquick.get(URL_REPLAY_BFM_REGION % (item_id.replace('bfm', ''), page),
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//article[@class='duo_liste content_item content_type content_type_video']"
    ):
        if 'https' not in video_datas.find('.//a').get('href'):
            video_url = URL_ROOT + video_datas.find('.//a').get('href')
        else:
            video_url = video_datas.find('.//a').get('href')
        video_image = ''  # TODO image
        video_title = video_datas.find('.//img').get('alt')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)

    data_account = re.compile(r'accountid="(.*?)"').findall(resp.text)[0]
    data_video_id = re.compile(r'videoid="(.*?)"').findall(resp.text)[0]
    data_player = re.compile(r'playerid="(.*?)"').findall(resp.text)[0]

    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id,
                                                    download_mode)


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    if 'paris' in item_id:
        resp = urlquick.get(URL_ROOT + '/mediaplayer/live-bfm-paris/',
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)
    else:
        resp = urlquick.get(URL_LIVE_BFM_REGION % item_id.replace('bfm', ''),
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)

    root = resp.parse()
    live_datas = root.find(".//div[@class='video_block']")
    data_account = live_datas.get('accountid')
    data_video_id = live_datas.get('videoid')
    data_player = live_datas.get('playerid')
    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id)
