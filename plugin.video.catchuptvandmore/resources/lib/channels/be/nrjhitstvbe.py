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

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import re
import urlquick

# TO DO

URL_ROOT = 'http://www.nrj.be'

URL_LIVE = URL_ROOT + '/nrjhitstv'

URL_VIDEOS = URL_ROOT + '/videos'

URL_STREAM = URL_ROOT + '/utils/videos/embed/internal/%s'
# videoId


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_VIDEOS)
    root = resp.parse("div", attrs={"id": "top_menu"})

    for category_datas in root.iterfind(".//div"):

        if category_datas.text is not None:
            category_title = category_datas.text.strip()
        else:
            category_title = category_datas.find('.//a').text.strip()
        if category_datas.find('.//a'):
            category_url = URL_ROOT + category_datas.find('.//a').get('href')

            item = Listitem()
            item.label = category_title
            item.set_callback(list_videos_categories,
                              item_id=item_id,
                              category_url=category_url,
                              page='1')
            item_post_treatment(item)
            yield item
        else:
            category_url = URL_VIDEOS

            item = Listitem()
            item.label = category_title
            item.set_callback(list_videos_last_videos,
                              item_id=item_id,
                              category_url=category_url)
            item_post_treatment(item)
            yield item


@Route.register
def list_videos_categories(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url + '/%s' % page)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='col-xs-6 col-md-4 col-lg-3 col-centered']"):
        video_title = video_datas.find('.//img').get('alt')
        video_image = video_datas.find('.//img').get('src')
        video_id = re.compile(r'changeVideoBrid\((.*?)\,').findall(
            video_datas.find(".//div[@class='play_hover']").get('onclick'))[0]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos_last_videos(plugin, item_id, category_url, **kwargs):

    resp = urlquick.get(category_url)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='col-xs-6 col-md-4 col-lg-3 col-centered']"):
        video_title = video_datas.find('.//img').get('alt')
        video_image = video_datas.find('.//img').get('src')
        video_id = re.compile(r'changeVideoBrid\((.*?)\,').findall(
            video_datas.find(".//div[@class='play_hover']").get('onclick'))[0]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

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

    resp = urlquick.get(URL_STREAM % video_id)
    root = resp.parse()
    final_video_url = root.find(".//input[@id='VideoPlayerDatas']").get(
        'data-filehd')

    if download_mode:
        return download.download_video(final_video_url, video_label)
    return final_video_url


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.get(URL_LIVE)
    root = resp.parse("div", attrs={"class": "col-md-12"})

    stream_url = ''
    for stream_datas in root.iterfind(".//a"):
        stream_url = stream_datas.get('href')
    return stream_url
