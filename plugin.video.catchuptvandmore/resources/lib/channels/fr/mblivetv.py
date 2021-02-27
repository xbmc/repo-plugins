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
from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

import json
import urlquick
from kodi_six import xbmcgui

# TO DO
# Fix Live TV

URL_LIVES = 'https://api.dailymotion.com/user/%s/videos?fields=id,thumbnail_large_url,title,views_last_hour&live_onair=1'
URL_REPLAY = 'https://api.dailymotion.com/user/%s/videos?fields=description,duration,id,taken_time,thumbnail_large_url,title&limit=20&sort=recent&page=1'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    headers = {'User-Agent': 'Android'}
    r = urlquick.get(URL_LIVES % (item_id), headers=headers)
    j_content = json.loads(r.text)
    if j_content['list'] is not None:
        vid = j_content['list'][0]['id']
        return resolver_proxy.get_stream_dailymotion(plugin, vid, False)
    return False


@Route.register
def list_videos(plugin, item_id, url=None, **kwargs):
    if not url:
        url = URL_REPLAY % (item_id)
    headers = {'User-Agent': 'Android'}
    r = urlquick.get(url, headers=headers)
    json_parser = json.loads(r.text)
    for video in json_parser['list']:
        item = Listitem()
        item.label = video['title']
        item.info['plot'] = video['description']
        item.info['duration'] = video['duration']
        item.art['thumb'] = item.art['landscape'] = video['thumbnail_large_url']
        vid = video['id']

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=vid)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if json_parser['has_more']:
        currentPage = json_parser['page']
        nextPage = currentPage + 1
        yield Listitem.next_page(url=url.replace("page=" + str(currentPage),
                                                 "page=" + str(nextPage)),
                                 callback=list_videos,
                                 item_id=item_id)


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):
    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode)
