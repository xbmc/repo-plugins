# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Jeff2900
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://t18.fr'
URL_REPLAY = URL_ROOT + '/replay'
EMBEDER_URL = 'https://www.dailymotion.com/video/%s'

GENERIC_HEADERS = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36'}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Nos documentaires et magazines
    - Nos films
    - ...
    """
    resp = urlquick.get(URL_REPLAY, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for categories_datas in root.iterfind(".//h2[@class='carousel__title']"):
        category_title = categories_datas.find(".//a").text.strip()
        category_url = categories_datas.find('.//a').get('href')
        if 'http' not in category_url:
            category_url = URL_ROOT + category_url

        item = Listitem()
        item.label = category_title
        item.set_callback(list_programs,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register(autosort=False)
def list_programs(plugin, category_url, **kwargs):
    """
    Build programs listing
    - Journal de 20H
    - Cash investigation
    """
    resp = urlquick.get(category_url, headers=GENERIC_HEADERS, max_age=-1)

    data_pagination_url = re.compile(r'data-pagination-url=\"(.*?)\"').findall(resp.text)[0]
    data_pagination_pages_count = re.compile(r'data-pagination-pages-count=\"(.*?)\"').findall(resp.text)[0]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
    }

    i = 0
    while i < int(data_pagination_pages_count):
        i += 1
        params = {
            'p': i,
        }
        resp = urlquick.get(URL_ROOT + data_pagination_url, params=params, headers=headers, max_age=-1)
        json_parser = json.loads(resp.text)

        for video_datas in json_parser:
            program_label = video_datas.get('title')
            program_url = video_datas.get('url')
            program_desc = video_datas.get('summary')
            program_image = video_datas.get('imageUrl')
            program_date = video_datas.get('broadcastedAt')
            if program_date is not None:
                program_date = program_date.split('T')[0]

            program_duration = video_datas.get('duration')
            Hrs_h = Hrs_m = None
            if program_duration is not None:
                if 'H' in program_duration:
                    Hrs_h = re.compile(r'(\d+)H').findall(program_duration)
                if 'M' in program_duration:
                    Hrs_m = re.compile(r'(\d+)M').findall(program_duration)

                if Hrs_h:
                    if Hrs_m:
                        duration = int(Hrs_m[0]) + int(60) * int(Hrs_h[0])
                    else:
                        duration = int(60) * int(Hrs_h[0])
                elif Hrs_m:
                    duration = int(Hrs_m[0])
                else:
                    duration = None

            item = Listitem()
            item.label = program_label
            item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = program_image
            if program_desc:
                item.info['plot'] = program_desc
            if program_date:
                item.info.date(program_date, '%Y-%m-%d')
            if duration:
                item.info['duration'] = duration
            item.set_callback(get_video_url,
                              video_url=program_url)
            item_post_treatment(item)
            yield item


@Resolver.register
def get_video_url(plugin, video_url):
    resp = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)

    video_id = re.compile(r'data-dailymotion-video-id=\"(.*?)\"').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, download_mode=False, embeder=video_url)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    try:
        resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)
        live_id = re.compile(r'"https://geo.dailymotion.com/player.html\?video=(.*?)[\?\"]').findall(resp.text)[0]
        return resolver_proxy.get_stream_dailymotion(plugin, live_id, download_mode=False, embeder=EMBEDER_URL % live_id)

    except Exception:
        return resolver_proxy.get_stream_dailymotion(plugin, 'x9jhhyc', False, embeder=EMBEDER_URL % 'x9jhhyc')
