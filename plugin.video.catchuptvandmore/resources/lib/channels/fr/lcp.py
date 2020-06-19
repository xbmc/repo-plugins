# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Original work (C) JUL1EN094, SPM, SylvainCecchetto
    Copyright (C) 2016  SylvainCecchetto

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
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import json
import re
import urlquick

# TO DO

# Info
# LCP contient deux sources de video pour les replays
# Old : play1.qbrick.com
# New : www.dailymotion.com

URL_ROOT = 'http://www.lcp.fr'

URL_LIVE_SITE = URL_ROOT + '/le-direct'

URL_CATEGORIES = URL_ROOT + '/revoir'

URL_VIDEO_REPLAY = 'http://play1.qbrick.com/config/avp/v1/player/' \
                   'media/%s/darkmatter/%s/'
# VideoID, AccountId


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
    resp = urlquick.get(URL_CATEGORIES)
    root = resp.parse()

    for category_datas in root.iterfind(".//div[@class='title-word']"):
        category_title = category_datas.find(".//span").text

        item = Listitem()
        item.label = category_title
        item.set_callback(list_programs,
                          item_id=item_id,
                          next_url=URL_CATEGORIES,
                          category_title=category_title)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, next_url, category_title, **kwargs):
    """
    Build programs listing
    - Journal de 20H
    - Cash investigation
    """
    resp = urlquick.get(next_url)
    root = resp.parse()

    for program_datas in root.iterfind(".//section[@class='block block-views clearfix']"):
        if program_datas.find(".//div[@class='title-word']") is not None:
            if category_title == program_datas.find(".//span").text:
                for video_datas in program_datas.findall(".//div[@class='node node-lcp-tv-episode node-teaser clearfix']"):
                    if video_datas.find(".//h4/a") is not None:
                        video_label = video_datas.find(".//h2/a").text + \
                            ' - ' + video_datas.find(".//h4/a").text
                    else:
                        video_label = video_datas.find(".//h2/a").text
                    video_image = video_datas.find(".//img").get('src')
                    video_url = URL_ROOT + video_datas.find(".//a").get('href')
                    date_value = video_datas.find(".//span[@class='date']").text
                    date = date_value.split(' ')
                    day = date[0]
                    try:
                        month = CORRECT_MONTH[date[1]]
                    except Exception:
                        month = '00'
                    year = date[2]
                    date_value = year + '-' + month + '-' + day

                    item = Listitem()
                    item.label = video_label
                    item.art['thumb'] = item.art['landscape'] = video_image
                    item.info.date(date_value, '%Y-%m-%d')
                    item.set_callback(get_video_url,
                                      item_id=item_id,
                                      video_url=video_url)
                    item_post_treatment(item, is_playable=True, is_downloadable=True)
                    yield item

                for real_program_datas in program_datas.findall(".//div[@class='node node-lcp-tv-series node-teaser clearfix']"):
                    program_label = real_program_datas.find(".//h2").text
                    program_image = real_program_datas.find(".//img").get('src')
                    program_url = URL_ROOT + real_program_datas.find(".//a").get('href')

                    item = Listitem()
                    item.label = program_label
                    item.art['thumb'] = item.art['landscape'] = program_image
                    item.set_callback(list_videos_program,
                                      item_id=item_id,
                                      program_url=program_url,
                                      page='0')
                    item_post_treatment(item)
                    yield item


@Route.register
def list_videos_program(plugin, item_id, program_url, page, **kwargs):

    resp = urlquick.get(program_url + '?page=%s' % page, timeout=120)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='node node-lcp-tv-episode node-teaser clearfix']"):
        if video_datas.find(".//h4/a") is not None:
            video_label = video_datas.find(".//h2/a").text + \
                ' - ' + video_datas.find(".//h4/a").text
        else:
            video_label = video_datas.find(".//h2/a").text
        if video_datas.find(".//img") is not None:
            video_image = video_datas.find(".//img").get('src')
        else:
            video_image = ''
        video_url = URL_ROOT + video_datas.find(".//a").get('href')
        date_value = video_datas.find(".//span[@class='date']").text
        date = date_value.split(' ')
        day = date[0]
        try:
            month = CORRECT_MONTH[date[1]]
        except Exception:
            month = '00'
        year = date[2]
        date_value = year + '-' + month + '-' + day

        item = Listitem()
        item.label = video_label
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info.date(date_value, '%Y-%m-%d')
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             program_url=program_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1,
                        timeout=120)

    if 'dailymotion' in resp.text:
        video_id = re.compile(
            r'www.dailymotion.com/embed/video/(.*?)[\?\"]').findall(
                resp.text)[0]
        return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                     download_mode)
    else:
        # get videoId and accountId
        videoId, accountId = re.compile(r'embed/(.*?)/(.*?)/').findall(
            resp.text)[0]

        resp2 = urlquick.get(URL_VIDEO_REPLAY % (videoId, accountId),
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)
        json_parser = json.loads(
            re.compile(r'\((.*?)\);').findall(resp2.text)[0])

        for playlist in json_parser['Playlist']:
            datas_video = playlist['MediaFiles']['M3u8']
            for data in datas_video:
                url = data['Url']

        if download_mode:
            return download.download_video(url)
        return url


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_LIVE_SITE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(
        r'www.dailymotion.com/embed/video/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id, False)
