# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto, darodi
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import urlquick

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, utils

# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui

from resources.lib import resolver_proxy, web_utils
from resources.lib.kodi_utils import (INPUTSTREAM_PROP, get_selected_item_art,
                                      get_selected_item_info,
                                      get_selected_item_label)
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = "https://www.tf1info.fr"

URL_EMISSION = URL_ROOT + '/emissions'
URL_LCI_EMISSIONS = URL_EMISSION + '/?channel=lci'

URL_VIDEO_STREAM = "https://mediainfo.tf1.fr/mediainfocombo/%s"
PARAMS_VIDEO_STREAM = {
    'context': 'MYTF1',
    'pver': '4008002',
    'platform': 'web',
    'os': 'linux',
    'osVersion': 'unknown',
    'topDomain': 'www.tf1.fr'
}

# videoId
URL_LICENCE_KEY = "https://drm-wide.tf1.fr/proxy?id=%s"

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def lci_root(plugin, item_id, **kwargs):
    """Build programs listing."""
    resp = urlquick.get(URL_LCI_EMISSIONS, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse("script", attrs={"id": "__NEXT_DATA__"})
    json_parser = json.loads(root.text)

    replay_list = json_parser['props']['pageProps']['page']['data'][3]['data'][3]['data'][0]['data']['elementList']

    for emission in replay_list:
        item = Listitem()
        emission_url = URL_ROOT + emission['link']
        item.label = emission['title']
        item.art["thumb"] = item.art["landscape"] = emission['pictures']['elementList'][1]['url']
        item.set_callback(list_videos, emission_url=emission_url, page="1")
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, emission_url, page, **kwargs):
    resp = urlquick.get(emission_url + "%s/" % page, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse("script", attrs={"id": "__NEXT_DATA__"})
    json_parser = json.loads(root.text)
    list_programs = json_parser['props']['pageProps']['page']['data'][3]['data'][3]['data'][0]['data']['elementList']

    for program in list_programs:
        item = Listitem()
        video_url = URL_ROOT + program['link']
        item.label = program['title']
        item.art["thumb"] = item.art["landscape"] = program['pictures']['elementList'][1]['url']
        item.info['plot'] = program['text']
        item.info.date(program['date'].split('T')[0], "%Y-%m-%d")
        item.set_callback(get_video_url, video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item

    # More videos...
    is_next = json_parser['props']['pageProps']['page']['data'][3]['data'][3]['data'][1]['data']['next']
    if is_next is not None:
        yield Listitem.next_page(emission_url=emission_url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin, video_url, download_mode=False, **kwargs):
    resp = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse("script", attrs={"id": "__NEXT_DATA__"})
    json_parser = json.loads(root.text)
    video_id = json_parser["props"]["pageProps"]["page"]["video"]["id"]

    json_parser = urlquick.get(URL_VIDEO_STREAM % video_id, params=PARAMS_VIDEO_STREAM, headers=GENERIC_HEADERS, max_age=-1).json()
    if json_parser["delivery"]["code"] > 400:
        plugin.notify("ERROR", plugin.localize(30713))
        return False

    if download_mode:
        xbmcgui.Dialog().ok("Info", plugin.localize(30603))
        return False

    video_url = json_parser["delivery"]["url"]
    license_url = URL_LICENCE_KEY % video_id

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="mpd", license_url=license_url)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    video_id = "L_%s" % item_id.upper()
    json_parser = urlquick.get(URL_VIDEO_STREAM % video_id, params=PARAMS_VIDEO_STREAM, headers=GENERIC_HEADERS, max_age=-1).json()

    if json_parser["delivery"]["code"] > 400:
        plugin.notify("ERROR", plugin.localize(30713))
        return False

    video_url = json_parser["delivery"]["url"]
    license_url = URL_LICENCE_KEY % video_id

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="mpd", license_url=license_url, workaround='1')
