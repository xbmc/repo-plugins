# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
from builtins import str

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
import urlquick

import json
import htmlement

from resources.lib import resolver_proxy, web_utils

from resources.lib.addon_utils import Quality
from resources.lib.menu_utils import item_post_treatment
from datetime import datetime


# TODO
# Add Replay

URL_ROOT = "https://www.tvtours.fr"
API_URL = URL_ROOT + '/ajaxEmissions.php?id_emission=%s&iterations=%s&ajax=true'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)
    duplicate = []
    root = resp.parse()

    for category in root.iterfind(".//li"):
        for type_emission in category.iterfind(".//a"):
            item = Listitem()
            partial_url = type_emission.get('href')
            if partial_url is not None:
                href_url = re.compile(r'\/(.*?)\/').findall(partial_url)
                if len(href_url) > 0:
                    if href_url[0] == 'type-emission' and partial_url not in duplicate:
                        program_page = URL_ROOT + partial_url
                        duplicate.append(partial_url)
                        item.label = type_emission.text
                        item.set_callback(list_emissions, item_id=item_id, program_page=program_page)
                        item_post_treatment(item)
                        yield item


@Route.register
def list_emissions(plugin, item_id, program_page, **kwargs):
    resp = urlquick.get(program_page, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for program in root.iterfind(".//li[@class='video-bleu']"):
        item = Listitem()
        item.art['thumb'] = item.art['landscape'] = URL_ROOT + program.find(".//img").get('data-src')
        item.label = program.find(".//img").get('alt')
        partial_url = program.findall(".//a")[0].get('href')
        if partial_url == '/le-journal':
            emission_id = '1'
        else:
            emission_id = re.compile(r'emission\/(.*?)\/').findall(partial_url)[0]
        item.set_callback(list_videos, item_id=item_id, emission_id=emission_id, page='0')
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos(plugin, item_id, emission_id, page, **kwargs):
    resp = urlquick.get(API_URL % (emission_id, page), headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)
    root = htmlement.fromstring(json_parser['videos'])

    for video in root.iterfind(".//li[@class='video video-bleu']"):
        item = Listitem()
        video_id = video.findall(".//a[@class='play-video']")[0].get('data-id')
        item.art['thumb'] = item.art['landscape'] = video.findall(".//img")[0].get('data-src')
        item.label = video.findall(".//a")[0].get('data-url')
        item.set_callback(get_video_url, item_id=item_id, video_id=video_id)
        yield item

    if json_parser['has_more'] is True:
        yield Listitem.next_page(item_id=item_id, emission_id=emission_id, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin, item_id, video_id, **kwargs):
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, False)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)
    live_id = re.compile(r'data-video\=\"(.*?)\"').findall(resp.text)[0]

    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
