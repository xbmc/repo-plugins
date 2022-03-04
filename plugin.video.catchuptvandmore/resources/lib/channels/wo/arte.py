# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import re

import inputstreamhelper
import urlquick
from codequick import Listitem, Resolver, Route, Script
from resources.lib import resolver_proxy, web_utils
from resources.lib.kodi_utils import (INPUTSTREAM_PROP, get_selected_item_art,
                                      get_selected_item_info,
                                      get_selected_item_label)
from resources.lib.menu_utils import item_post_treatment

# TO DO
#   Most recent
#   Most viewed
#   Add some videos Arte Concerts

URL_ROOT = 'https://www.arte.tv/%s/'
# Language

URL_TOKEN = 'https://static-cdn.arte.tv/guide/manifest.js'

URL_LIVE_ARTE = 'https://api.arte.tv/api/player/v2/config/%s/LIVE'
# Langue, ...

# URL_VIDEOS = 'http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/subcategory/%s/page/%s/limit/100/%s'
# VideosCode, Page, language

URL_VIDEOS_2 = 'http://www.arte.tv/hbbtvv2/services/web/index.php/OPA/v3/videos/collection/%s/%s/%s'
# VideosCode, Page, language

DESIRED_LANGUAGE = Script.setting['arte.language']

CORRECT_MONTH = {
    'Jan': '01',
    'Feb': '02',
    'Mar': '03',
    'Apr': '04',
    'May': '05',
    'Jun': '06',
    'Jul': '07',
    'Aug': '08',
    'Sep': '09',
    'Oct': '10',
    'Nov': '11',
    'Dec': '12'
}


def extract_json_from_html(url):
    html = urlquick.get(url).text
    json_value = re.compile(r'application/json">(.*?)\}<').findall(html)[0]
    return json.loads(json_value + '}')


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    url = URL_ROOT % DESIRED_LANGUAGE.lower()
    return list_zone(plugin, item_id, url)


@Route.register
def list_zone(plugin, item_id, url):
    j = extract_json_from_html(url)
    zones = j['props']['pageProps']['initialPage']['zones']
    for zone in zones:
        # Avoid empty folders
        if not zone['data']:
            continue
        # Avoid infinite loop
        if len(zone['data']) == 1 and zone['data'][0]['url'] == url:
            continue

        item = Listitem()
        item.label = zone['title']
        item.info['plot'] = zone['description']

        item.set_callback(list_data,
                          item_id=item_id,
                          url=url,
                          zone_id=zone['id'])
        item_post_treatment(item)
        yield item


@Route.register
def list_data(plugin, item_id, url, zone_id):
    j = extract_json_from_html(url)
    zones = j['props']['pageProps']['initialPage']['zones']
    for zone in zones:
        if zone_id == zone['id']:
            data = zone['data']
            break
    for data in zone['data']:
        title = data['title']
        if 'subtitle' in data and data['subtitle']:
            title += ' - ' + data['subtitle']

        item = Listitem()
        item.label = title
        item.info['plot'] = data.get('shortDescription', None)

        images = data['images']
        thumb = None
        fanart = None
        if 'square' in images:
            try:
                thumb = data['images']['square']['resolutions'][-1]['url']
            except Exception:
                pass
        if 'portrait' in images and thumb is None:
            try:
                thumb = data['images']['portrait']['resolutions'][-1]['url']
            except Exception:
                pass
        try:
            fanart = data['images']['landscape']['resolutions'][-1]['url']
        except Exception:
            pass
        if fanart:
            item.art['fanart'] = item.art['thumb'] = fanart
        if thumb:
            item.art['thumb'] = thumb

        item.info['duration'] = data.get('duration', None)

        try:
            item.info.date(data['availability']['start'].split('T')[0], '%Y-%m-%d')
        except Exception:
            pass

        if data['kind']['code'].lower() in ['shows', 'show']:
            item.set_callback(get_video_url, item_id=item_id, video_id=data['programId'])
            item_post_treatment(
                item,
                is_playable=True,
                is_downloadable=True)
        else:
            # Assume it's a folder
            item.set_callback(list_zone,
                              item_id=item_id,
                              url=data['url'])
            item_post_treatment(item)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    return resolver_proxy.get_arte_video_stream(plugin,
                                                DESIRED_LANGUAGE.lower(),
                                                video_id,
                                                download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_language = kwargs.get('language', DESIRED_LANGUAGE)

    try:
        resp = urlquick.get(URL_TOKEN)
        token = re.compile(r'token\"\:\"(.*?)\"').findall(resp.text)[0]
    except Exception:
        token = 'MzYyZDYyYmM1Y2Q3ZWRlZWFjMmIyZjZjNTRiMGY4MzY4NzBhOWQ5YjE4MGQ1NGFiODJmOTFlZDQwN2FkOTZjMQ'

    headers = {
        'Authorization': 'Bearer %s' % token
    }
    resp2 = urlquick.get(URL_LIVE_ARTE % final_language.lower(), headers=headers)
    json_parser = json.loads(resp2.text)

    is_helper = inputstreamhelper.Helper("hls")
    if not is_helper.check_inputstream():
        return False

    item = Listitem()
    item.path = json_parser["data"]["attributes"]["streams"][0]["url"]
    item.property[INPUTSTREAM_PROP] = "inputstream.adaptive"
    item.property["inputstream.adaptive.manifest_type"] = "hls"

    return item
