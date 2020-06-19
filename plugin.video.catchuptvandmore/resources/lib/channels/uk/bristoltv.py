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

# TO DO

URL_ROOT = 'https://www.bristollocal.tv'


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    - ...
    """
    resp = urlquick.get(URL_ROOT)
    root = resp.parse("section", attrs={"class": "grid-container grid-40"})

    for category_datas in root.iterfind(".//a"):
        if 'Live' not in category_datas.find('.//img').get('title'):
            category_title = category_datas.find('.//img').get('title')
            category_image = URL_ROOT + category_datas.find('.//img').get('src')
            category_url = URL_ROOT + '/' + category_datas.get('href')

            item = Listitem()
            item.label = category_title
            item.art['thumb'] = item.art['landscape'] = category_image
            item.set_callback(list_sub_categories,
                              item_id=item_id,
                              category_url=category_url)
            item_post_treatment(item)
            yield item


@Route.register
def list_sub_categories(plugin, item_id, category_url, **kwargs):
    """
    - ...
    """
    resp = urlquick.get(category_url)
    root = resp.parse()

    for sub_category_datas in root.iterfind(".//section[@class='grid-container section-video']"):
        if sub_category_datas.find(".//header[@class='grid-100']") is not None:
            if sub_category_datas.find('.//h2').text is not None:
                sub_category_title = sub_category_datas.find('.//h2').text
                if 'Weather' in sub_category_datas.find('.//h2').text:
                    sub_category_url = URL_ROOT + '/video-category/weather/'
                else:
                    sub_category_url = URL_ROOT + sub_category_datas.find('.//p/a').get('href')

                item = Listitem()
                item.label = sub_category_title
                item.set_callback(list_videos,
                                  item_id=item_id,
                                  sub_category_url=sub_category_url,
                                  page='1')
                item_post_treatment(item)
                yield item


@Route.register
def list_videos(plugin, item_id, sub_category_url, page, **kwargs):

    resp = urlquick.get(sub_category_url + 'page/%s/' % page)
    root = resp.parse("section", attrs={"class": "grid-container section-video"})

    for video_datas in root.iterfind(".//div"):

        if 'single-video' in video_datas.get('class'):
            video_title = video_datas.find('.//img').get('title')
            video_image = URL_ROOT + video_datas.find('.//img').get('src')
            video_url = video_datas.find('.//a').get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    root_change_pages = resp.parse()
    if root_change_pages.find(".//a[@class='next page-numbers']") is not None:
        yield Listitem.next_page(
            item_id=item_id, sub_category_url=sub_category_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]',
                          re.DOTALL).findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, download_mode)


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):
    """Get video URL and start video player"""

    resp = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    live_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]',
                         re.DOTALL).findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
