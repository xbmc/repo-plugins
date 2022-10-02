# -*- coding: utf-8 -*-
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re
from builtins import str

import htmlement
import urlquick
from codequick import Listitem, Resolver, Route
from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

# URL :
URL_ROOT_SITE = 'https://www.cnews.fr'

# Live :
URL_LIVE_CNEWS = URL_ROOT_SITE + '/le-direct'

# Replay CNews
URL_REPLAY_CNEWS = URL_ROOT_SITE + '/replay'
URL_EMISSIONS_CNEWS = URL_ROOT_SITE + '/service/dm_loadmore/dm_emission_index_emissions/%s/0'
# num Page
URL_VIDEOS_CNEWS = URL_ROOT_SITE + '/service/dm_loadmore/dm_emission_index_sujets/%s/0'
# num Page

# TODO: Add more emissions button
# TODO: Check if all videos are here


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    for (label, url, callback) in [('Nos émissions', URL_EMISSIONS_CNEWS, list_emissions), ('Nos vidéos', URL_VIDEOS_CNEWS, list_videos)]:
        item = Listitem()
        item.label = label
        item.set_callback(callback, item_id=item_id, category_url=url, page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url % page, max_age=-1)
    parser = htmlement.HTMLement()
    parser.feed(resp.json())
    data = parser.close()

    for video_datas in data.iterfind(".//div[@class='wrapper-article-middle']"):
        exists_video = video_datas.find(".//div[@id='embed-main-video']")
        if exists_video is not None:
            item = Listitem()
            item.label = video_datas.find(".//h1[@class='article-title']").text
            video_id = exists_video.get('data-videoid')
            item.set_callback(get_video_id, video_id=video_id)
            item_post_treatment(item)
            yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id, category_url=category_url, page=str(int(page) + 1))


@Resolver.register
def get_video_id(plugin, video_id, download_mode=False, **kwargs):

    return resolver_proxy.get_stream_dailymotion(plugin, video_id, download_mode)


@Route.register
def list_emissions(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url % page, max_age=-1)
    parser = htmlement.HTMLement()
    parser.feed(resp.json())
    data = parser.close()

    for video_datas in data.iterfind(".//a[@class='emission-item-wrapper']"):
        item = Listitem()
        item.label = video_datas.find(".//div[@class='field field-type-text']").text
        video_image = video_datas.find('.//img').get('data-echo')
        video_url = URL_ROOT_SITE + video_datas.get('href')
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(list_videos_emission, item_id=item_id, video_url=video_url)
        item_post_treatment(item)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id, category_url=category_url, page=str(int(page) + 1))


@Route.register
def list_videos_emission(plugin, item_id, video_url, **kwargs):

    root = urlquick.get(video_url, max_age=-1).parse()

    info = root.findall(".//p")[0].text
    video_image = root.findall('.//img')[1].get('data-echo')

    for video_datas in root.iterfind(".//a[@class='emission-item-wrapper']"):
        item = Listitem()
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = info
        item.label = video_datas.find(".//span[@class='emission-title']").text
        video_url = URL_ROOT_SITE + video_datas.get('href')
        item.set_callback(get_video_url, item_id=item_id, video_url=video_url)
        item_post_treatment(item)
        yield item

    # yield Listitem.next_page(item_id=item_id,
    #                          category_url=category_url,
    #                          page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin, item_id, video_url, download_mode=False, **kwargs):

    root = urlquick.get(video_url, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1).parse()
    video_id = root.find(".//div[@id='embed-main-video']").get('data-videoid')
    # video_id = re.compile(r'data-videoid\"\=\"(.*?)[\?\"]').findall(resp.text)[0]

    return resolver_proxy.get_stream_dailymotion(plugin, video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    root = urlquick.get(URL_LIVE_CNEWS,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1).parse()
    try:
        live_id = root.find(".//div[@id='player_live']").get('data-videoid')
    except Exception:
        try:
            live_id = root.find(".//div[@id='player_live']").get('data-video-id')
        except Exception:
            live_id = 'x3b68jn'

    return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)
