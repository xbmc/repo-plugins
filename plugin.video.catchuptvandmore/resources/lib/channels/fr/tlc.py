# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Listitem, Resolver, Route, Script
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}

URL_ROOT = 'http://www.tlc-cholet.fr'
URL_REPLAY = URL_ROOT + '/les-emissions'
URL_LIVE = URL_ROOT + '/le-direct'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_REPLAY, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse().find('.//div[@class="container"]')

    for category in root.iterfind('.//div[@class="emissions_panel_blanc_contain"]'):
        item = Listitem()
        url_category = URL_ROOT + category.find('.//a').get('href')
        item.art['thumb'] = item.art['landscape'] = category.find('.//img').get('src')
        item.label = category.find(".//h1").text
        item.info['plot'] = category.find('.//p').text
        item.set_callback(list_episodes, item_id=item_id, url_category=url_category)
        item_post_treatment(item)
        yield item


@Route.register
def list_episodes(plugin, item_id, url_category, **kwargs):
    resp = urlquick.get(url_category, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for element in root.iterfind('.//div[@class="container"]'):
        if element.find('.//div[@class="col-lg-3 col-md-3 col-sm-3"]') is not None:
            partial_root = element
            break

    for episode in partial_root.iterfind('.//div[@class="col-lg-3 col-md-3 col-sm-3"]'):
        item = Listitem()
        item.label = episode.find('.//h3').text
        detail = episode.find('.//div[@class="emission_preview_container"]')
        picture = re.compile(r'\'(.*?)\'').findall(detail.get('style'))[0]
        item.art['thumb'] = item.art['landscape'] = picture

        video_url = re.compile(r'openVideo\(\'([0-9]+)\'\,').findall(detail.get('onclick'))[0]
        item.set_callback(get_video_url, item_id=item_id, video_url=video_url)
        item_post_treatment(item)
        yield item


@Resolver.register
def get_video_url(plugin, item_id, video_url, **kwargs):
    return resolver_proxy.get_stream_vimeo(plugin, video_id=video_url)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(
        URL_LIVE, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    live_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
