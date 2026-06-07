# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info
from resources.lib.menu_utils import item_post_treatment
from resources.lib import resolver_proxy, web_utils


# TO DO
# some videos are paid video (add account ?)

URL_SERVICES = 'https://services.radio-canada.ca/ott/catalog/v2/toutv/%s'

URL_VIDEO = 'https://services.radio-canada.ca/media/validation/v2/'

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    params = {
        'device': 'web'
    }
    resp = urlquick.get(URL_SERVICES % 'browse', headers=GENERIC_HEADERS, params=params, max_age=-1)
    root = json.loads(resp.text)

    for category in root['formats']:
        item = Listitem()
        item.label = category['title']
        item.art['thumb'] = item.art['landscape'] = category['image']['url']
        url = category['url'].replace('categorie', 'category')
        item.set_callback(list_programs, url=url, page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, url, page, **kwargs):
    params = {
        'device': 'web',
        'pageNumber': page,
        'pageSize': '80'
    }
    resp = urlquick.get(URL_SERVICES % url, headers=GENERIC_HEADERS, params=params, max_age=-1)
    json_parser = json.loads(resp.text)['content'][0]
    nbpages = json_parser['items']['totalPages']

    for program in json_parser["items"]["results"]:
        if program["tier"] == 'Standard':
            item = Listitem()
            url = program['url']
            prog_type = program['type']
            item.label = program["title"]
            item.art['thumb'] = item.art['landscape'] = program["images"]["background"]["url"]
            item.info["plot"] = program["description"]
            item.set_callback(list_seasons, url, prog_type=prog_type)
            item_post_treatment(item)
            yield item

    if int(page) < int(nbpages):
        page = str(int(page) + 1)
        yield Listitem.next_page(url=url, page=page)


@Route.register
def list_seasons(plugin, url, prog_type, **kwargs):
    params = {'device': 'web'}
    program_url = prog_type + '/' + url
    resp = urlquick.get(URL_SERVICES % program_url, headers=GENERIC_HEADERS, params=params, max_age=-1)
    json_parser = json.loads(resp.text)

    for season in json_parser['content'][0]['lineups']:
        if season['tier'] == 'Standard':
            item = Listitem()
            item.label = season['title']
            season_url = prog_type + '/' + season['url']
            item.set_callback(list_episodes, season_url=season_url)
            item_post_treatment(item)
            yield item


@Route.register
def list_episodes(plugin, season_url, **kwargs):
    params = {'device': 'web'}
    resp = urlquick.get(URL_SERVICES % season_url, headers=GENERIC_HEADERS, params=params, max_age=-1)
    json_parser = json.loads(resp.text)

    for episode in json_parser['content'][0]['lineups'][0]['items']:
        if episode['tier'] == 'Standard':
            item = Listitem()
            video_id = episode['idMedia']
            item.label = episode["title"]
            item.art['thumb'] = item.art['landscape'] = episode["images"]["card"]["url"]
            item.info["plot"] = episode["description"]
            item.set_callback(get_video_url, video_id=video_id)
            item_post_treatment(item)
            yield item


@Resolver.register
def get_video_url(plugin, video_id, download_mode=False, **kwargs):
    params = {
        'appCode': 'toutv',
        'connectionType': 'hd',
        'deviceType': 'multiams',
        'idMedia': video_id,
        'multibitrate': 'true',
        'output': 'json',
        'tech': 'azuremediaplayer',
        'manifestType': 'desktop',
    }
    resp = urlquick.get(URL_VIDEO, headers=GENERIC_HEADERS, params=params, max_age=-1)
    json_parser = json.loads(resp.text)

    video_url = json_parser['url']

    for item in json_parser['params']:
        if 'name' in item:
            if item['name'] == 'widevineLicenseUrl':
                license_url = item['value']
            if item['name'] == 'widevineAuthToken':
                token = item['value']

    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'Authorization': token
    }

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, license_url=license_url, manifest_type='ism', headers=headers)
