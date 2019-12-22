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
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import json
import re
import urlquick

# TO DO
# QUality Mode

URL_TV5MAF_ROOT = 'https://afrique.tv5monde.com'


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
    resp = urlquick.get(URL_TV5MAF_ROOT + '/videos')
    root = resp.parse()

    for category_datas in root.iterfind(
            ".//h2[@class='tv5-title tv5-title--beta u-color--goblin']"):
        category_title = category_datas.find('.//a').text
        category_url = URL_TV5MAF_ROOT + category_datas.find('.//a').get(
            'href')
        item = Listitem()
        item.label = category_title
        item.set_callback(list_programs,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_url, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(category_url)
    root = resp.parse()

    for program_datas in root.iterfind(
            ".//div[@class='grid-col-12 grid-col-m-4']"):
        program_title = program_datas.find('.//h2/span').text.strip()
        program_url = URL_TV5MAF_ROOT + program_datas.find('.//a').get('href')
        if 'http' in program_datas.find('.//img').get('src'):
            program_image = program_datas.find('.//img').get('src')
        else:
            program_image = URL_TV5MAF_ROOT + program_datas.find('.//img').get(
                'src')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()
    if root.find(".//div[@class='tv5-pagerTop tv5-pagerTop--green']") is None:
        video_datas = root.find(".//div[@class='tv5-player']")
        video_title = video_datas.find('.//h1').text.strip()
        video_image = re.compile(r'image\" content=\"(.*?)\"').findall(
            resp.text)[0]
        video_plot = video_datas.find(
            ".//div[@class='tv5-desc to-expand u-mg-t--m u-mg-b--s']").get(
                'data-originaltext')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=program_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)

        yield item
    else:
        list_seasons = root.find(
            ".//div[@class='tv5-pagerTop tv5-pagerTop--green']").findall(
                './/a')
        if len(list_seasons) > 1:
            for season in list_seasons:
                season_title = 'Saison ' + season.text
                season_url = URL_TV5MAF_ROOT + season.get('href')

                item = Listitem()
                item.label = season_title
                item.set_callback(list_videos_season,
                                  item_id=item_id,
                                  season_url=season_url)
                item_post_treatment(item)
                yield item
        else:
            list_videos_datas = root.findall(
                ".//div[@class='grid-col-12 grid-col-m-4']")
            for video_datas in list_videos_datas:
                video_title = video_datas.find('.//h2/span').text.strip()
                video_image = video_datas.find('.//img').get('src')
                video_url = URL_TV5MAF_ROOT + video_datas.find('.//a').get(
                    'href')

                item = Listitem()
                item.label = video_title
                item.art['thumb'] = video_image

                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_label=LABELS[item_id] + ' - ' +
                                  item.label,
                                  video_url=video_url)
                item_post_treatment(item,
                                    is_playable=True,
                                    is_downloadable=True)
                yield item


@Route.register
def list_videos_season(plugin, item_id, season_url, **kwargs):
    resp = urlquick.get(season_url)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='grid-col-12 grid-col-m-4']"):
        video_title = video_datas.find('.//h2/span').text.strip()
        video_image = video_datas.find('.//img').get('src')
        video_url = URL_TV5MAF_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


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
