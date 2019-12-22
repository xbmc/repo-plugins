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

from builtins import str
import re
from codequick import Route, Resolver, Listitem
import urlquick
import json

from resources.lib import download
from resources.lib.labels import LABELS
from resources.lib.listitem_utils import item_post_treatment, item2dict

# TO DO
# Get sub-playlist
# Add video info (date, duration)
# Add More video button

URL_ROOT = 'https://www.nytimes.com'

URL_VIDEOS = URL_ROOT + '/video'

URL_PLAYLIST = URL_ROOT + '/svc/video/api/v2/playlist/%s'
# playlistId

URL_STREAM = URL_ROOT + '/svc/video/api/v3/video/%s'
# videoId


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    categories_html = urlquick.get(URL_VIDEOS).text
    categories_datas = re.compile(r'var navData =(.*?)\;').findall(
        categories_html)[0]
    # print 'categories_datas value : ' + categories_datas
    categories_jsonparser = json.loads(categories_datas)

    for category in categories_jsonparser:
        item = Listitem()

        item.label = category["display_name"]
        category_playlist = category["knews_id"]

        item.set_callback(list_videos,
                          item_id=item_id,
                          category_playlist=category_playlist)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_playlist, **kwargs):
    """Build videos listing"""

    videos_json = urlquick.get(URL_PLAYLIST % category_playlist).text
    videos_jsonparser = json.loads(videos_json)

    for video_data in videos_jsonparser["videos"]:
        item = Listitem()
        item.label = video_data["headline"]
        video_id = str(video_data["id"])
        for image in video_data["images"]:
            item.art['thumb'] = URL_ROOT + '/' + image["url"]
        item.info['plot'] = video_data["summary"]

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  video_label=None,
                  **kwargs):
    """Get video URL and start video player"""
    video_json = urlquick.get(URL_STREAM % video_id).text
    video_jsonparser = json.loads(video_json)

    video_url = ''
    for video in video_jsonparser["renditions"]:
        if video["type"] == 'hls':
            video_url = video["url"]

    if download_mode:
        return download.download_video(video_url, video_label)

    return video_url
