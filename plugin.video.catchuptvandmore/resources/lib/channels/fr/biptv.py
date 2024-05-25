# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import os
import re

from codequick import Listitem, Route, Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = "https://www.biptv.tv"
URL_LIVE = URL_ROOT + "/direct.html"

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse().find('.//div[@class="col-md-3 footh"]')

    for category in root.iterfind('.//a'):
        item = Listitem()
        url_category = URL_ROOT + '/%s' % category.get('href')
        item.label = category.text
        item.set_callback(list_emissions, item_id=item_id, url_category=url_category, page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_emissions(plugin, item_id, url_category, page, **kwargs):
    resp = urlquick.get(url_category.replace('.html', '.page.%s.html' % page), headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for emission in root.find('.//div[@id="trie-1"]').iterfind('.//div[@class="emission"]'):
        item = Listitem()
        item.label = emission.findall('.//a')[1].text
        item.art['thumb'] = item.art['landscape'] = emission.find('.//img').get('src')
        item.info['plot'] = emission.find('.//span').text

        video_url = URL_ROOT + emission.findall('.//a')[0].get('href')
        item.set_callback(get_video_url, item_id=item_id, video_url=video_url)
        item_post_treatment(item)
        yield item

    pagination = root.findall('.//div[@class="trie-emissions2"]')
    if len(pagination) > 0:
        if len(pagination[0].findall('.//a')) > 1 or (len(pagination[0].findall('.//a')) == 1 and 'suivante' in pagination[0].findall('.//a')[0].text):
            page = str(int(page) + 1)
            yield Listitem.next_page(callback=list_emissions, url_category=url_category, item_id=item_id, page=page)


@Resolver.register
def get_video_url(plugin, item_id, video_url, **kwargs):
    resp = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    video_page = root.find('.//iframe[@class="embed-responsive-item player"]').get('src')
    resp = urlquick.get(video_page, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.text
    video_url = 'https' + re.compile(r'src\\\"\:\\\"https(.*?)master\.m3u8').findall(root)[0].replace('\\', '') + 'master.m3u8'
    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    video_url = resp.parse().find(".//source").get("src")
    return resolver_proxy.get_stream_with_quality(plugin, video_url)
