# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Add Replay

URL_ROOT = "https://www.tvvendee.fr"

URL_LIVE = URL_ROOT + '/direct'

URL_MYVIDEOPLACE_API = 'https://player.myvideoplace.tv/ajax_actions.php'

URL_REPLAY = 'https://api.dailymotion.com/user/%s/videos?fields=description,duration,id,taken_time,thumbnail_large_url,title&limit=20&sort=recent&page=1'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


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

        item.set_callback(get_video_url, item_id=item_id, video_id=vid)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if json_parser['has_more']:
        currentPage = json_parser['page']
        nextPage = currentPage + 1
        url = url.replace("page=" + str(currentPage), "page=" + str(nextPage))
        yield Listitem.next_page(url=url, callback=list_videos, item_id=item_id)


@Resolver.register
def get_video_url(plugin, item_id, video_id, download_mode=False, **kwargs):
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    url_player = resp.parse().find('.//iframe').get('src')
    live_id = re.compile('v=(.*?)\&').findall(url_player)[0]

    datas = {
        'action': 'video_info',
        'refvideo': live_id
    }
    headers = {
        "User-Agent": web_utils.get_random_ua(),
        'referer': url_player
    }

    stream_json = urlquick.post(URL_MYVIDEOPLACE_API, data=datas, headers=headers, max_age=-1)
    video_url = json.loads(stream_json.text)["data"]["bitrates"]["hls"]

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url)
