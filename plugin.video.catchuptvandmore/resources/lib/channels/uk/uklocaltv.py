# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re
import urlquick

from codequick import Listitem, Resolver, Route

from resources.lib import resolver_proxy, web_utils
from resources.lib.addon_utils import get_item_media_path
from resources.lib.menu_utils import item_post_treatment


# TO DO

URL_ROOT = 'https://www.%s.tv'


@Route.register
def channels(plugin, **kwargs):
    """
    List all france.tv channels
    """
    # (item_id, label, thumb, fanart)
    channels = [
        ('birminghamlocal', 'Birmingham Local TV', 'birminghamlocal.png', 'birminghamlocal_fanart.jpg'),
        ('bristollocal', 'Bristol Local TV', 'bristollocal.png', 'bristollocal_fanart.jpg'),
        ('cardifflocal', 'Cardiff Local TV', 'cardifflocal.png', 'cardifflocal_fanart.jpg'),
        ('leedslocal', 'Leeds Local TV', 'leedslocal.png', 'leedslocal_fanart.jpg'),
        ('liverpoollocal', 'Liverpool Local TV', 'liverpoollocal.png', 'liverpoollocal_fanart.jpg'),
        ('northwaleslocal', 'North Whales Local TV', 'northwaleslocal.png', 'northwaleslocal_fanart.jpg'),
        ('teessidelocal', 'Teesside Local TV', 'teessidelocal.png', 'teessidelocal_fanart.jpg'),
        ('twlocal', 'Tyne & Wear Local TV', 'twlocal.png', 'twlocal_fanart.jpg')
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/uk/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/uk/' + channel_infos[3])
        item.set_callback(list_categories, channel_infos[0])
        item_post_treatment(item)
        yield item


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    - ...
    """
    resp = urlquick.get(URL_ROOT % item_id)
    root = resp.parse("section", attrs={"class": "grid-container grid-40"})

    for category_datas in root.iterfind(".//a"):
        if 'Live' not in category_datas.find('.//img').get('title'):
            category_title = category_datas.find('.//img').get('title')
            category_image = URL_ROOT % item_id + category_datas.find('.//img').get('src')
            category_url = URL_ROOT % item_id + '/' + category_datas.get('href')

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
                    sub_category_url = URL_ROOT % item_id + '/video-category/weather/'
                else:
                    sub_category_url = URL_ROOT % item_id + sub_category_datas.find('.//p/a').get('href')

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
            video_image = URL_ROOT % item_id + video_datas.find('.//img').get('src')
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


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    """Get video URL and start video player"""

    resp = urlquick.get(URL_ROOT % item_id,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    live_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]',
                         re.DOTALL).findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
