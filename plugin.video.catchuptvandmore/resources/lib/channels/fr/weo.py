# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
import urlquick
from kodi_six import xbmcgui

from resources.lib import resolver_proxy, web_utils

from resources.lib.addon_utils import Quality
from resources.lib.menu_utils import item_post_treatment
from datetime import datetime

import json

# TODO
# Add Replay

URL_ROOT = "https://www.weo.fr"

URL_CATEGORIES = URL_ROOT + '/emission'

URL_LIVE = URL_ROOT + "/direct/"

BASIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}

URL_VIDEO = 'https://www.ultimedia.com/deliver/video?video=%s&topic=generic'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_CATEGORIES, headers=BASIC_HEADERS)
    root = resp.parse("div", attrs={"class": "row"})

    for category in root.iterfind(".//div[@class='col-12 col-sm-4 col-lg-3 text-center mb-5']"):
        item = Listitem()
        item.art['thumb'] = item.art['landscape'] = category.find(".//img").get('src')
        item.label = category.find(".//a").text
        program_page = URL_ROOT + category.find(".//a").get('href')
        if category.find(".//p") is not None:
            item.info['plot'] = category.find(".//p").text
        item.set_callback(list_videos, item_id=item_id, program_page=program_page)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_page, **kwargs):
    resp = urlquick.get(program_page, headers=BASIC_HEADERS)
    root = resp.parse("div", attrs={"class": "row mt-5"})

    for program in root.iterfind(".//div[@class='col-12 col-sm-4 col-lg-3 text-left mb-3']"):
        item = Listitem()
        item.art['thumb'] = item.art['landscape'] = program.find(".//img").get('src')
        item.label = program.find(".//a").text
        emission_page = URL_ROOT + program.find(".//a").get('href')
        if program.find(".//span") is not None:
            full_date = re.compile(r"^.*\r?\n.*\r?\n(.*)").findall(program.find(".//span").text)[0].replace(' ', '')
            date_time = datetime.strptime(full_date, "%d/%m/%Yà%Hh%M")
            item.info.date(full_date, "%d/%m/%Yà%Hh%M")
            item.info['plot'] = "Emission de %s" % (date_time.strftime("%HH%M"))
        item.set_callback(get_video_url, item_id=item_id, emission_page=emission_page)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin, item_id, emission_page, **kwargs):
    print("emission = %s" % emission_page)
    resp = urlquick.get(emission_page, headers=BASIC_HEADERS)
    for possibility in resp.parse().findall('.//iframe'):
        if possibility.get('allowfullscreen'):
            final_page = possibility.get('src')

    resp2 = urlquick.get(final_page, headers=BASIC_HEADERS)
    video_id = re.compile(r'video\":{\"id\":\"(.*?)\"').findall(resp2.text)

    resp3 = urlquick.get(URL_VIDEO % video_id, headers=BASIC_HEADERS)
    json_parser = json.loads(resp3.text)

    urls = []
    definition = []
    for source in json_parser['jwconf']['playlist'][0]['sources']:
        urls.append(source['file'])
        definition.append(source.get('label').replace('mp4_', '') + 'p')

    quality = Script.setting.get_string('quality')
    if quality == Quality['WORST']:
        video_url = urls[len(urls) - 1]
    elif quality == Quality['BEST'] or quality == Quality['DEFAULT']:
        video_url = urls[0]
    else:
        video_url = urls[xbmcgui.Dialog().select(Script.localize(30180), definition)]

    return video_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    video_page = None
    resp = urlquick.get(URL_LIVE, headers=BASIC_HEADERS, max_age=-1)
    for possibility in resp.parse().findall('.//iframe'):
        if possibility.get('allowfullscreen'):
            video_page = 'https:' + possibility.get('src')

    if video_page is None:
        return False

    # In a perfect world, digiteka extractor would not be broken in youtube-dl
    resp2 = urlquick.get(video_page, headers=BASIC_HEADERS, max_age=-1)
    found_files = re.compile(r'live\":{\"src\":\"(.*?)\"').findall(resp2.text)
    if len(found_files) == 0:
        return False

    video_url = found_files[0].replace("\\", "")
    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="hls")
