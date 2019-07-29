# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

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
from resources.lib import resolver_proxy
from resources.lib.listitem_utils import item_post_treatment, item2dict

import json
import urlquick

# TO DO
# Get year from Replay

URL_REPLAY = 'http://www.numero23.fr/replay/'

URL_INFO_LIVE_JSON = 'http://www.numero23.fr/wp-content/cache/n23-direct.json'

CORRECT_MONTH = {
    'janvier': '01',
    'février': '02',
    'mars': '03',
    'avril': '04',
    'mai': '05',
    'juin': '06',
    'juillet': '07',
    'août': '08',
    'septembre': '09',
    'octobre': '10',
    'novembre': '11',
    'décembre': '12'
}


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_REPLAY)
    root = resp.parse("div", attrs={"class": "nav-programs"})

    for category in root.iterfind(".//a"):
        category_name = category.find('.//span').text.replace(
            '\n', ' ').replace('\r', ' ').rstrip('\r\n')
        category_url = category.get('href')

        item = Listitem()
        item.label = category_name
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_url=category_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, page, **kwargs):

    replay_paged_url = category_url + '&paged=' + page
    resp = urlquick.get(replay_paged_url)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='program sticky video']"):

        video_title = utils.ensure_unicode(
            video_datas.find(".//p[@class='red']").text)
        video_img = video_datas.find(".//img").get('src')
        video_id = video_datas.find(".//div[@class='player']").get(
            'data-id-video')

        video_duration = 0
        video_duration_list = video_datas.find(".//strong").text.split(':')
        if len(video_duration_list) > 2:
            video_duration = int(video_duration_list[0]) * 3600 + \
                int(video_duration_list[1]) * 60 + \
                int(video_duration_list[2])
        else:
            video_duration = int(video_duration_list[0]) * 60 + \
                int(video_duration_list[1])

        info_video = video_datas.findall(".//p")
        # get month and day on the page
        date_list = ''
        try:
            date_list = utils.strip_tags(str(info_video[2].text)).split(' ')
        except Exception:
            pass
        day = '00'
        month = '00'
        year = '2019'
        if len(date_list) > 3:
            day = date_list[2]
            try:
                month = CORRECT_MONTH[date_list[3]]
            except Exception:
                month = '00'
            # get year ?

        date_value = '-'.join((year, month, day))

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_img
        item.info['duration'] = video_duration
        try:
            item.info.date(date_value, '%Y-%m-%d')
        except Exception:
            pass

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             category_url=category_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  video_label=None,
                  **kwargs):
    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode, video_label)


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.get(URL_INFO_LIVE_JSON,
                        headers={'User-Agent': web_utils.get_random_ua},
                        max_age=-1)
    json_parser = json.loads(resp.text)
    video_id = json_parser["video"]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, False)
