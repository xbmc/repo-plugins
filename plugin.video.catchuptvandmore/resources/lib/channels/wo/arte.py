# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

# TO DO
#   Most recent
#   Most viewed
#   Add some videos Arte Concerts

URL_ARTE_HOME = 'https://api.arte.tv/api/emac/v4/%s/tv/pages/HOME'
URL_ARTE_CATEGORIES = 'https://api.arte.tv/api/emac/v4/%s/app/pages/%s'
URL_ARTE_COLLECTION = 'https://api.arte.tv/api/emac/v4/%s/tv/collections/%s'
URL_ARTE_PROGRAMS = 'https://api.arte.tv/api/emac/v4/%s/tv/programs/%s'
URL_ARTE_SEARCH = 'https://api.arte.tv/api/emac/v4/%s/app/pages/SEARCH'
URL_LIVE_ARTE = 'https://api.arte.tv/api/player/v2/config/%s/LIVE'
# Langue, ...

# URL_VIDEOS = 'http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/subcategory/%s/page/%s/limit/100/%s'
# VideosCode, Page, language

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}
ARTE_API_HEADERS = {
    'user-agent': web_utils.get_random_ua(),
    'accept': 'application/vnd.api+json',
    'authorization': 'Bearer YTEwZWE3M2UxMTVmYmRjZmE0YTdmNjA4ZTI2NDczZDU3YjdjYmVmMmRmNGFjOTM3M2RhNTM5ZjIxYmI3NTc1Zg',
}

DESIRED_LANGUAGE = Script.setting['arte.language']


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    # Search items
    item = Listitem.search(list_videos_search)
    item_post_treatment(item)
    yield item

    url = URL_ARTE_HOME % DESIRED_LANGUAGE.lower()
    response = urlquick.get(url, headers=ARTE_API_HEADERS, max_age=-1)
    json_parser = response.json()

    for zone in json_parser['zones']:
        # Avoid empty folders
        if not zone['content']['data']:
            continue
        # Avoid infinite loop
        data_url_dic = zone['content']['data'][0]['url'].split("/")
        data_url_len = len(data_url_dic)
        data_url = data_url_dic[data_url_len - 3]
        zone_url_dic = url.split("/")
        zone_url_len = len(zone_url_dic)
        zone_url = zone_url_dic[zone_url_len - 1]
        if data_url == zone_url:
            continue

        item = Listitem()
        item.label = zone['title']
        item.info['plot'] = zone['description']
        item.set_callback(list_programs, url=url, zone_id=zone['id'])
        item_post_treatment(item)
        yield item


@Route.register
def list_zone(plugin, url):
    response = urlquick.get(url, headers=ARTE_API_HEADERS, max_age=-1)
    json_parser = response.json()

    for zone in json_parser['zones']:
        # Avoid empty folders
        if not zone['content']['data']:
            continue
        # Avoid infinite loop
        data_url_dic = zone['content']['data'][0]['url'].split("/")
        data_url_len = len(data_url_dic)
        data_url = data_url_dic[data_url_len - 3]
        zone_url_dic = url.split("/")
        zone_url_len = len(zone_url_dic)
        zone_url = zone_url_dic[zone_url_len - 1]
        if data_url == zone_url:
            continue

        item = Listitem()
        item.label = zone['title']
        item.info['plot'] = zone['description']
        item.set_callback(list_programs, url=url, zone_id=zone['id'])
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_search(plugin, search_query, **kwargs):
    if search_query is None or len(search_query) == 0:
        return False

    params = {
        'query': search_query,
    }
    response = urlquick.get(URL_ARTE_SEARCH % DESIRED_LANGUAGE.lower(), params=params, headers=ARTE_API_HEADERS, max_age=-1)
    json_parser = response.json()

    at_least_one_item = False
    for zone in json_parser['zones']:
        for data in zone['content']['data']:
            item = handle_programs(data)
            at_least_one_item = True
            yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Resolver.register
def handle_programs(data):
    title = data['title']
    if 'subtitle' in data and data['subtitle']:
        title += ' - ' + data['subtitle']

    item = Listitem()
    item.label = title
    if 'teaserText' in data:
        item.info['plot'] = data['teaserText']
    else:
        item.info['plot'] = data.get('shortDescription', None)

    if 'mainImage' in data:
        item.art['thumb'] = item.art["fanart"] = data['mainImage']['url'].replace('__SIZE__', '940x530')
        item.art['landscape'] = data['mainImage']['url'].replace('__SIZE__', '265x397')

    if 'duration' in data:
        item.info['duration'] = data['duration']

    try:
        item.info.date(data['availability']['start'].split('T')[0], '%Y-%m-%d')
    except Exception:
        pass

    if data.get('kind') is not None and data['kind']['code'] in ['SHOWS', 'SHOW']:
        item.set_callback(get_video_url, video_id=data['programId'])
        item_post_treatment(item, is_playable=True, is_downloadable=True)
    else:
        # Assume it's a folder
        if data['deeplink'] is None:
            # No items found
            item.label = Script.localize(30896)
        else:
            deeplink_dic = data['deeplink'].split("/")
            deeplink_len = len(deeplink_dic)
            deeplink = deeplink_dic[deeplink_len - 1]
            if deeplink_dic[deeplink_len - 2] == "emac":
                item.set_callback(list_zone, url=URL_ARTE_CATEGORIES % (DESIRED_LANGUAGE.lower(), deeplink))
                item_post_treatment(item)
            elif deeplink_dic[deeplink_len - 2] == "collection":
                item.set_callback(list_zone, url=URL_ARTE_COLLECTION % (DESIRED_LANGUAGE.lower(), deeplink))
                item_post_treatment(item)
            elif deeplink_dic[deeplink_len - 2] == "program":
                item.set_callback(list_zone, url=URL_ARTE_PROGRAMS % (DESIRED_LANGUAGE.lower(), deeplink))
                item_post_treatment(item)
            else:
                # No items found
                item.label = Script.localize(30896)

    return item


@Route.register
def list_programs(plugin, url, zone_id):
    response = urlquick.get(url, headers=ARTE_API_HEADERS, max_age=-1)
    json_parser = response.json()

    if zone_id != 'pagination_link_next':
        for zone in json_parser['zones']:
            if zone_id == zone['id']:
                data = zone['content']['data']
                break
        for data in zone['content']['data']:
            item = handle_programs(data)
            yield item

        if zone.get('link') is not None and zone['link'].get('page')[:3] == "RC-":
            item = handle_programs(zone.get('link'))
            yield item

        if zone['content'].get('pagination') is not None:
            if zone['content']['pagination']['links'].get('next') is not None:
                url_next = zone['content']['pagination']['links']['next']
                yield Listitem.next_page(url=url_next, zone_id='pagination_link_next')
    else:
        for data in json_parser['data']:
            item = handle_programs(data)
            yield item

        if json_parser.get('pagination') is not None:
            if json_parser['pagination']['links'].get('next') is not None:
                url_next = json_parser['pagination']['links']['next']
                yield Listitem.next_page(url=url_next, zone_id='pagination_link_next')


@Resolver.register
def get_video_url(plugin, video_id, download_mode=False, **kwargs):
    return resolver_proxy.get_arte_video_stream(plugin, DESIRED_LANGUAGE.lower(), video_id, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_language = kwargs.get('language', DESIRED_LANGUAGE)
    resp = urlquick.get(URL_LIVE_ARTE % final_language.lower(), headers=GENERIC_HEADERS)
    json_parser = json.loads(resp.text)

    streams = json_parser["data"]["attributes"]["streams"]
    if len(streams) == 0:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False
    video_url = streams[0]["url"]
    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url)
