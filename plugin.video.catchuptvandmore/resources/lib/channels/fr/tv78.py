# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.tv78.com'
URL_LIVE = URL_ROOT + '/le-live'
URL_REPLAY = URL_ROOT + '/emissions-replay/'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_REPLAY, GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for category in root.find('.//tr').iterfind('.//div[@class="float_left-bloc_replay"]'):
        picture = category.find('.//img').get('src')
        url = category.find('.//a').get('href')
        item = Listitem()
        item.label = category.find('.//img').get('alt')
        item.art['thumb'] = item.art['landscape'] = picture
        item.set_callback(list_videos, url)
        item_post_treatment(item)
        yield item

    # archives
    item = Listitem()
    item.label = root.find('.//button[@class="btn btn-link"]').text
    item.set_callback(list_archives, root)
    item_post_treatment(item)
    yield item


@Route.register
def list_archives(plugin, root, **kwargs):
    for category in root.find('.//div[@class="card-body"]').iterfind('.//div[@class="float_left-bloc_replay"]'):
        picture = category.find('.//img').get('src')
        url = category.find('.//a').get('href')
        item = Listitem()
        item.label = category.find('.//img').get('alt')
        item.art['thumb'] = item.art['landscape'] = picture
        item.set_callback(list_videos, url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, url, **kwargs):
    resp = urlquick.get(url, GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for emission in root.iterfind('.//article'):
        if emission.get('id') is not None:
            item = Listitem()
            item.art['thumb'] = item.art['landscape'] = emission.find('.//img').get('src')
            emission_ = emission.find('.//h2').find('.//a')
            url = emission_.get('href')
            item.label = emission_.text
            item.info['plot'] = emission.find('.//div[@class="post-description"]').find('.//p').text
            item.set_callback(get_video_url, url=url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin, url, download_mode=False, **kwargs):
    resp = urlquick.get(url, GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    complete_url = root.find('.//iframe[@itemprop="video"]').get('src')
    video_id = re.compile('embed\/(.*?)\?rel').findall(complete_url)[0]

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
    video_url = re.compile('source src\=\"(.*?)\"').findall(resp.text)[0]

    return resolver_proxy.get_stream_with_quality(plugin, video_url)
