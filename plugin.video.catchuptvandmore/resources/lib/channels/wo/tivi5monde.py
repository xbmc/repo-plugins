# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Download Mode / QUality Mode

URL_TIVI5MONDE_ROOT = 'http://www.tivi5mondeplus.com'

URL_TV5MONDE_LIVE = 'http://live.tv5monde.com/'

LIST_LIVE_TV5MONDE = {'tivi5monde': 'tivi5monde'}

CATEGORIES_VIDEOS_TIVI5MONDE = {
    '/series/decouverte': 'REPLAY PROGRAMMES JEUNESSE DÉCOUVERTE',
    '/decouverte': 'LES DERNIERS ÉPISODES DE TES ÉMISSIONS DÉCOUVERTE',
    '/series/dessins-animes': 'REPLAY DESSINS ANIMÉS',
    '/dessins-animes': 'LES DERNIERS ÉPISODES DE TES DESSINS ANIMÉS PRÉFÉRÉS'
}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    for category_context, category_title in list(CATEGORIES_VIDEOS_TIVI5MONDE.items(
    )):
        category_url = URL_TIVI5MONDE_ROOT + category_context
        if 'REPLAY' in category_title:
            next_value = 'list_programs'
        else:
            next_value = 'list_videos'
        item = Listitem()
        item.label = category_title
        item.set_callback(eval(next_value),
                          item_id=item_id,
                          next_url=category_url,
                          page='0')
        item_post_treatment(item)
        yield item

    # Search videos
    item = Listitem.search(list_videos_search, item_id=item_id, page='0')
    item_post_treatment(item)
    yield item


@Route.register
def list_programs(plugin, item_id, next_url, page, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(next_url + '?page=%s' % page,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()

    for program_datas in root.iterfind(
            ".//div[@class='views-field views-field-nothing']"):
        program_title = program_datas.find('.//h3').find('.//a').text.strip()
        program_url = URL_TIVI5MONDE_ROOT + program_datas.find('.//a').get(
            'href')
        program_image = program_datas.find('.//img').get('src')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          next_url=program_url,
                          page='0')
        item_post_treatment(item)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             next_url=next_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, next_url, page, **kwargs):

    resp = urlquick.get(next_url + '?page=%s' % page,
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='row-vignette']"):
        video_title = video_datas.find('.//img').get('alt')
        video_image = video_datas.find('.//img').get('src')
        video_url = URL_TIVI5MONDE_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             next_url=next_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos_search(plugin, search_query, item_id, page, **kwargs):

    resp = urlquick.get(URL_TIVI5MONDE_ROOT +
                        '/recherche?search_api_views_fulltext=%s&page=%s' %
                        (search_query, page),
                        headers={'User-Agent': web_utils.get_random_ua()})
    root = resp.parse()

    at_least_one_item = False
    for video_datas in root.iterfind(".//div[@class='row-vignette']"):
        at_least_one_item = True
        video_title = video_datas.find('.//img').get('alt')
        video_image = video_datas.find('.//img').get('src')
        video_url = URL_TIVI5MONDE_ROOT + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url, item_id=item_id, video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if at_least_one_item:
        yield Listitem.next_page(item_id=item_id,
                                 search_query=search_query,
                                 page=str(int(page) + 1))
    else:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    stream_url = re.compile('contentUrl\"\: \"(.*?)\"').findall(resp.text)[0]

    if download_mode:
        return download.download_video(stream_url)

    return stream_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

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
