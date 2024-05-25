# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Add Replays/Serie TV (required account)

# Live
URL_ROOT = 'https://www.nessma.tv'

URL_LIVE = URL_ROOT + '/ar/live'

URL_REPLAY = URL_ROOT + '/ar/replays'

URL_VIDEOS = URL_ROOT + '/ar/videos'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    """
    item = Listitem()
    item.label = 'الفيديوهات'
    item.set_callback(list_videos, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item

    item = Listitem()
    item.label = 'مشاهدة الحلقات'
    item.set_callback(list_programs, item_id=item_id)
    item_post_treatment(item)
    yield item


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build progams listing
    - Le JT
    - ...
    """
    resp = urlquick.get(URL_REPLAY, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='col-sm-3']"):
        if program_datas.find('.//img').get('alt') is not None:
            program_title = program_datas.find('.//img').get('alt')
            program_image = program_datas.find('.//img').get('src')
            program_url = program_datas.find('.//a').get('href')

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image

            item.set_callback(list_videos_replays, item_id=item_id, program_url=program_url, page='1')
            item_post_treatment(item)
            yield item


@Route.register
def list_videos_replays(plugin, item_id, program_url, page, **kwargs):

    params = {'page': page}
    resp = urlquick.get(program_url, params=params, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    if root.find(".//div[@class='row replaynessma-cats row-eq-height ']") is not None:
        root2 = resp.parse("div", attrs={"class": "row replaynessma-cats row-eq-height "})
        for video_datas in root2.iterfind(".//article"):
            video_title = video_datas.find('.//h3/a').text
            video_image = video_datas.find('.//img').get('src')
            video_url = video_datas.find('.//a').get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url, item_id=item_id, video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item
    else:
        for video_datas in root.iterfind(".//div[@class='col-sm-3']"):
            video_title = video_datas.find('.//img').get('alt')
            video_image = video_datas.find('.//img').get('src')
            video_url = video_datas.find('.//a').get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url, item_id=item_id, video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

        yield Listitem.next_page(item_id=item_id, program_url=program_url, page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, page, **kwargs):

    params = {'page': page}
    resp = urlquick.get(URL_VIDEOS, params=params, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='col-sm-4']"):
        if video_datas.find('.//img') is not None:
            video_title = video_datas.find('.//img').get('alt')
            video_image = video_datas.find('.//img').get('src')
            video_url = video_datas.find('.//a').get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url, item_id=item_id, video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    yield Listitem.next_page(item_id=item_id, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin, item_id, video_url, download_mode=False, **kwargs):

    resp = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)
    video_id = re.compile(r'youtube\.com\/embed\/(.*.)\?').findall(resp.text)[0]

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    live_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
