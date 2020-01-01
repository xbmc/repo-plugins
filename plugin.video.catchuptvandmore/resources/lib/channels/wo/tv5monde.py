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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import json
import re
import urlquick

URL_TV5MONDE_LIVE = 'http://live.tv5monde.com/'

URL_TV5MONDE_ROOT = 'http://www.tv5mondeplus.com'

LIST_LIVE_TV5MONDE = {'tv5mondefbs': 'fbs', 'tv5mondeinfo': 'infoplus'}

CATEGORIES_VIDEOS_TV5MONDE = {
    'Information': '1',
    'Série & Fiction': '2',
    'Sport': '3',
    'Documentaire': '4',
    'Jeunesse': '5',
    'Musique': '6',
    'Bonus': '7',
    'Magazine': '9',
    'Divertissement': '8'
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
    resp = urlquick.get(URL_TV5MONDE_ROOT + '/toutes-les-emissions')
    root = resp.parse()
    category_title = root.find(".//nav[@class='footer__emissions']").find(
        ".//div[@class='footer__title']").find('.//span').text.strip()
    item = Listitem()
    item.label = category_title
    item.set_callback(list_programs, item_id=item_id)
    item_post_treatment(item)
    yield item

    for category_title, category_type in list(CATEGORIES_VIDEOS_TV5MONDE.items(
    )):
        item = Listitem()
        item.label = category_title
        item.set_callback(list_videos_category,
                          item_id=item_id,
                          category_type=category_type,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_TV5MONDE_ROOT)
    root = resp.parse("nav", attrs={"class": "footer__emissions"})

    for program_datas in root.iterfind(".//li"):
        program_title = program_datas.find('.//a').text.strip()
        program_url = URL_TV5MONDE_ROOT + program_datas.find('.//a').get(
            'href')

        item = Listitem()
        item.label = program_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, page, **kwargs):

    resp = urlquick.get(program_url + '?page=%s' % page)
    root = resp.parse()

    for video_datas in root.iterfind(".//article"):
        if video_datas.find(".//p[@class='video-item__subtitle']") is not None:
            video_title = video_datas.find('.//h3').text.strip() + \
                ' - ' + video_datas.find(".//p[@class='video-item__subtitle']").text.strip()
        else:
            video_title = video_datas.find('.//h3').text.strip()
        if 'http' in video_datas.find('.//img').get('src'):
            video_image = video_datas.find('.//img').get('src')
        else:
            video_image = URL_TV5MONDE_ROOT + video_datas.find('.//img').get(
                'src')
        video_url = URL_TV5MONDE_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             program_url=program_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos_category(plugin, item_id, category_type, page, **kwargs):
    resp = urlquick.get(URL_TV5MONDE_ROOT +
                        '/toutes-les-videos?order=1&type=%s&page=%s' %
                        (category_type, page))
    root = resp.parse()

    at_least_one_item = False
    for video_datas in root.iterfind(".//article"):
        if video_datas.find(".//a[@class='video-item__link']").get(
                'href') != '':
            if video_datas.find(
                    ".//p[@class_='video-item__subtitle']") is not None:
                video_title = video_datas.find('.//h3').text.strip() + \
                    ' - ' + video_datas.find(".//p[@class_='video-item__subtitle']").text.strip()
            else:
                video_title = video_datas.find('.//h3').text.strip()
            if 'http' in video_datas.find('.//img').get('src'):
                video_image = video_datas.find('.//img').get('src')
            else:
                video_image = URL_TV5MONDE_ROOT + video_datas.find(
                    './/img').get('src')
            video_url = URL_TV5MONDE_ROOT + video_datas.find('.//a').get(
                'href')
            at_least_one_item = True
            item = Listitem()
            item.label = video_title
            item.art['thumb'] = video_image

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_label=LABELS[item_id] + ' - ' + item.label,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    if at_least_one_item:
        yield Listitem.next_page(item_id=item_id,
                                 category_type=category_type,
                                 page=str(int(page) + 1))
    else:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_json = re.compile('data-broadcast=\'(.*?)\'').findall(resp.text)[0]
    json_parser = json.loads(video_json)
    final_video_url = json_parser["files"][0]["url"]

    if download_mode:
        return download.download_video(final_video_url, video_label)

    return final_video_url


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    live_id = ''
    for channel_name, live_id_value in list(LIST_LIVE_TV5MONDE.items()):
        if item_id == channel_name:
            live_id = live_id_value
    resp = urlquick.get(URL_TV5MONDE_LIVE + '%s.html' % live_id,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    live_json = re.compile(r'data-broadcast=\'(.*?)\'').findall(resp.text)[0]
    json_parser = json.loads(live_json)
    return json_parser["files"][0]["url"]
