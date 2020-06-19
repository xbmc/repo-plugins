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
from builtins import range
from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info

# Verify md5 still present in hashlib python 3 (need to find another way if it is not the case)
# https://docs.python.org/3/library/hashlib.html
from hashlib import md5

import inputstreamhelper
import json
import os
import re
import urlquick
from kodi_six import xbmc
from kodi_six import xbmcgui

# TO DO
# Readd Playlist (if needed)
# Add more infos videos (saison, episodes, casts, etc ...)
# Find a way to get Id for each API call

URL_ROOT = utils.urljoin_partial("https://www.tf1.fr")

URL_VIDEO_STREAM = 'https://delivery.tf1.fr/mytf1-wrd/%s?format=%s'
# videoId, format['hls', 'dash']

URL_LICENCE_KEY = 'https://drm-wide.tf1.fr/proxy?id=%s|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=drm-wide.tf1.fr|R{SSM}|'
# videoId

URL_API = 'https://www.tf1.fr/graphql/web'

DESIRED_QUALITY = Script.setting['quality']

VIDEO_TYPES = {
    'Replay': 'replay',
    'Extrait': 'extract',
    'Exclu': 'bonus'
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
    params = {
        'id': '83ae0bfb82e29a71ad00e07122cca81e840cf88f5d4595f65ffb171bdb701543',
        'variables': '{}'
    }
    headers = {
        'content-type': 'application/json',
        'referer': 'https://www.tf1.fr/programmes-tv',
        'User-Agent': web_utils.get_random_ua()
    }
    resp = urlquick.get(URL_API, params=params, headers=headers)
    json_parser = json.loads(resp.text)

    for json_key in list(json_parser['data'].keys()):
        if json_parser['data'][json_key]['label']:
            category_name = json_parser['data'][json_key]['label']
            category_id = json_parser['data'][json_key]['id']

            item = Listitem()
            item.label = category_name
            item.params['item_id'] = item_id
            item.params['category_id'] = category_id
            item.set_callback(list_programs)
            item_post_treatment(item)

            yield item


@Route.register
def list_programs(plugin, item_id, category_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """

    params = {
        'id': '400be301099f781dbee5bf2641b3bfba74f9fb6c13a54a22cae1fde916e42c7a',
        'variables': '{"context":{"persona":"PERSONA_2","application":"WEB","device":"DESKTOP","os":"WINDOWS"},"filter":{"channel":"%s"},"offset":0,"limit":500}' % item_id
    }
    headers = {
        'content-type': 'application/json',
        'referer': 'https://www.tf1.fr/programmes-tv',
        'User-Agent': web_utils.get_random_ua()
    }
    resp = urlquick.get(URL_API, params=params, headers=headers)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser['data']['programs']['items']:
        is_category = False
        for category_datas in program_datas['categories']:
            if category_id in category_datas['id']:
                is_category = True
        if is_category:
            program_name = program_datas['name']
            program_slug = program_datas['slug']
            program_image = program_datas['decoration']['image']['sources'][0]['url']
            program_background = program_datas['decoration']['background']['sources'][0]['url']

            item = Listitem()
            item.label = program_name
            item.art['thumb'] = item.art['landscape'] = program_image
            item.art['fanart'] = program_background
            item.set_callback(list_program_categories,
                              item_id=item_id,
                              program_slug=program_slug)
            item_post_treatment(item)
            yield item


@Route.register
def list_program_categories(plugin, item_id, program_slug, **kwargs):
    """
    Build program categories
    - Toutes les vidéos
    - Tous les replay
    - Saison 1
    - ...
    """
    for video_type_title, video_type_value in list(VIDEO_TYPES.items()):
        item = Listitem()
        item.label = video_type_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_slug=program_slug,
                          video_type_value=video_type_value,
                          offset='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_slug, video_type_value, offset, **kwargs):

    params = {
        'id': '6708f510f2af7e75114ab3c4378142b2ce25cd636ff5a1ae11f47ce7ad9c4a91',
        'variables': '{"programSlug":"%s","offset":%d,"limit":20,"sort":{"type":"DATE","order":"DESC"},"types":["%s"]}' % (program_slug, int(offset), video_type_value)
    }
    headers = {
        'content-type': 'application/json',
        'referer': 'https://www.tf1.fr/programmes-tv',
        'User-Agent': web_utils.get_random_ua()
    }
    resp = urlquick.get(URL_API, params=params, headers=headers)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['data']['programBySlug']['videos']['items']:
        video_title = video_datas['title']
        try:
            video_image = video_datas['decoration']['images'][1]['sources'][0]['url']
        except Exception:
            video_image = ''
        video_plot = video_datas['decoration']['description']
        video_duration = video_datas['publicPlayingInfos']['duration']
        video_id = video_datas['streamId']

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.info.date(video_datas['date'].split('T')[0], '%Y-%m-%d')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if (20 + int(offset) * 20) < json_parser['data']['programBySlug']['videos']['total']:
        yield Listitem.next_page(item_id=item_id,
                                 program_slug=program_slug,
                                 video_type_value=video_type_value,
                                 offset=str(int(offset) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    video_format = 'hls'
    url_json = URL_VIDEO_STREAM % (video_id, video_format)
    htlm_json = urlquick.get(url_json,
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)
    json_parser = json.loads(htlm_json.text)

    if json_parser['code'] >= 400:
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    # Check DRM in the m3u8 file
    manifest = urlquick.get(json_parser["url"],
                            headers={
                                'User-Agent': web_utils.get_random_ua()},
                            max_age=-1).text
    if 'drm' in manifest:

        if get_kodi_version() < 18:
            xbmcgui.Dialog().ok('Info', plugin.localize(30602))
            return False
        else:
            video_format = 'dash'

    if video_format == 'hls':

        final_video_url = json_parser["url"].replace('2800000', '4000000')
        if download_mode:
            return download.download_video(final_video_url)
        return final_video_url

    else:
        if download_mode:
            xbmcgui.Dialog().ok('Info', plugin.localize(30603))
            return False

        url_json = URL_VIDEO_STREAM % (video_id, video_format)
        htlm_json = urlquick.get(
            url_json,
            headers={'User-Agent': web_utils.get_random_ua()},
            max_age=-1)
        json_parser = json.loads(htlm_json.text)

        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
        if not is_helper.check_inputstream():
            return False

        item = Listitem()
        item.path = json_parser["url"]
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        item.property['inputstreamaddon'] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.property[
            'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
        item.property[
            'inputstream.adaptive.license_key'] = URL_LICENCE_KEY % video_id

        return item


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):
    video_id = 'L_%s' % item_id.upper()

    video_format = 'hls'
    url_json = URL_VIDEO_STREAM % (video_id, video_format)
    htlm_json = urlquick.get(url_json,
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)
    json_parser = json.loads(htlm_json.text)

    if json_parser['code'] > 400:
        plugin.notify('ERROR', plugin.localize(30713))
        return False
    else:
        return json_parser['url'].replace('master_2000000.m3u8',
                                          'master_4000000.m3u8')
