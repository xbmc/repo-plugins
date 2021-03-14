# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download, web_utils
from resources.lib.menu_utils import item_post_treatment


# TO DO
# QUality Mode

URL_TV5MAF_ROOT = 'https://afrique.tv5monde.com'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_TV5MAF_ROOT + '/videos',
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()

    for category_datas in root.iterfind(".//div[@class='view-header']"):
        if category_datas.find(".//h2") is not None:
            category_title = category_datas.find(".//h2").text
            if category_datas.find('.//a') is not None:
                category_url = URL_TV5MAF_ROOT + category_datas.find('.//a').get('href')
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
    resp = urlquick.get(category_url,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='views-row']"):
        if program_datas.find('.//h2') is not None:
            program_title = program_datas.find('.//h2').text
            if 'http' in program_datas.find('.//a').get('href'):
                program_url = program_datas.find('.//a').get('href')
            else:
                program_url = URL_TV5MAF_ROOT + program_datas.find('.//a').get('href')
            if 'http' in program_datas.find('.//img').get('src'):
                program_image = program_datas.find('.//img').get('src')
            else:
                program_image = URL_TV5MAF_ROOT + program_datas.find('.//img').get(
                    'src')

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            item.set_callback(list_videos,
                              item_id=item_id,
                              program_url=program_url)
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()
    if root.find(".//nav[@class='title-season']") is None:
        video_datas = root.find(".//main[@class='layout-3col__full']")
        video_title = video_datas.find('.//h1').text.strip()
        video_image = re.compile(r'image\" content=\"(.*?)\"').findall(
            resp.text)[0]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=program_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)

        yield item
    else:
        list_seasons = root.find(
            ".//nav[@class='title-season']").findall(
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
                ".//div[@class='season-1 views-row']")
            # TODO Get season number
            for video_datas in list_videos_datas:
                if video_datas.find('.//h2') is not None:
                    video_title = video_datas.find('.//h2').text
                    if 'http' in video_datas.find('.//img').get('src'):
                        video_image = video_datas.find('.//img').get('src')
                    else:
                        video_image = URL_TV5MAF_ROOT + video_datas.find('.//img').get(
                            'src')
                    if 'http' in video_datas.find('.//a').get('href'):
                        video_url = video_datas.find('.//a').get('href')
                    else:
                        video_url = URL_TV5MAF_ROOT + video_datas.find('.//a').get(
                            'href')

                    item = Listitem()
                    item.label = video_title
                    item.art['thumb'] = item.art['landscape'] = video_image

                    item.set_callback(get_video_url,
                                      item_id=item_id,
                                      video_url=video_url)
                    item_post_treatment(item,
                                        is_playable=True,
                                        is_downloadable=True)
                    yield item


@Route.register
def list_videos_season(plugin, item_id, season_url, **kwargs):
    resp = urlquick.get(season_url,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='season-1 views-row']"):
        # TODO Season value
        if video_datas.find('.//h2') is not None:
            video_title = video_datas.find('.//h2').text
            if 'http' in video_datas.find('.//img').get('src'):
                video_image = video_datas.find('.//img').get('src')
            else:
                video_image = URL_TV5MAF_ROOT + video_datas.find('.//img').get(
                    'src')
            if 'http' in video_datas.find('.//a').get('href'):
                video_url = video_datas.find('.//a').get('href')
            else:
                video_url = URL_TV5MAF_ROOT + video_datas.find('.//a').get(
                    'href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_json = re.compile('data-broadcast=\'(.*?)\'').findall(resp.text)[0]
    json_parser = json.loads(video_json)
    final_video_url = json_parser["files"][0]["url"]

    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url
