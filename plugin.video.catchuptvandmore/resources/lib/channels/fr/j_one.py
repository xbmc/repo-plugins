# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Fix Live TV

URL_REPLAY = 'https://api.dailymotion.com/user/%s/videos?fields=description,duration,id,taken_time,thumbnail_large_url,title&limit=20&sort=recent&page=1'


@Route.register
def list_videos(plugin, item_id, **kwargs):
    url = URL_REPLAY % (item_id.replace('_', '-'))
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
