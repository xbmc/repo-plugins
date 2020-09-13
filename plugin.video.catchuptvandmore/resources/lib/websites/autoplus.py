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

from codequick import Route, Resolver, Listitem, Script
import urlquick


from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

# TO DO

URL_ROOT = 'https://www.autoplus.fr/video/'


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    item = Listitem()
    item.label = plugin.localize(30701)

    item.set_callback(list_videos, item_id=item_id, page=1)
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):
    """Build videos listing"""
    resp = urlquick.get(URL_ROOT + '/?page=%s' % page)

    # Get Video First Page
    if page == 1:
        item = Listitem()

        video_id = re.compile(r'video: \"(.*?)\"').findall(resp.text)[0]
        url_first_video = 'https://www.dailymotion.com/embed/video/%s' % video_id
        info_first_video = urlquick.get(url_first_video).text
        info_first_video_json = re.compile('config = (.*?)};').findall(
            info_first_video)[0]
        # print 'info_first_video_json : ' + info_first_video_json + '}'
        info_first_video_jsonparser = json.loads(info_first_video_json + '}')

        item.label = info_first_video_jsonparser["metadata"]["title"]
        item.art['thumb'] = item.art['landscape'] = info_first_video_jsonparser["metadata"][
            "posters"]["1080"]

        item.set_callback(get_video_url_first_video,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    root = resp.parse()
    for episode in root.iterfind(".//div[@class='col-xs-6 col-sm-12']"):
        item = Listitem()

        item.label = episode.find('.//img').get('alt')
        video_url = URL_ROOT + episode.find('.//a').get('href')
        item.art['thumb'] = item.art['landscape'] = episode.find('.//img').get('src').replace(
            '|', '%7C')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id, page=page + 1)


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""

    video_html = urlquick.get(video_url).text
    # Get DailyMotion Id Video
    video_id = re.compile(r'video: \"(.*?)\"').findall(video_html)[0]

    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode)


@Resolver.register
def get_video_url_first_video(plugin,
                              item_id,
                              video_id,
                              download_mode=False,
                              **kwargs):
    """Get video URL and start video player"""

    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode)
