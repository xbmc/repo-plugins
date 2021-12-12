# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json

import inputstreamhelper
from codequick import Route, Resolver, Listitem, utils, Script
from kodi_six import xbmcgui, xbmcplugin
import urlquick

from resources.lib import web_utils
from resources.lib.addon_utils import get_item_media_path
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Readd Playlist (if needed)
# Add more infos videos (saison, episodes, casts, etc ...)
# Find a way to get Id for each API call

URL_ROOT = utils.urljoin_partial("https://www.tf1.fr")

URL_VIDEO_STREAM = 'https://mediainfo.tf1.fr/mediainfocombo/%s?context=MYTF1&pver=4008002&platform=web&os=linux&osVersion=unknown&topDomain=www.tf1.fr'

URL_LICENCE_KEY = 'https://drm-wide.tf1.fr/proxy?id=%s|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=drm-wide.tf1.fr|R{SSM}|'
# videoId

URL_API = 'https://www.tf1.fr/graphql/web'

DESIRED_QUALITY = Script.setting['quality']

VIDEO_TYPES = {
    'Replay': 'replay',
    'Extrait': 'extract',
    'Exclu': 'bonus'
}


@Route.register
def mytf1_root(plugin, **kwargs):

    # (item_id, label, thumb, fanart)
    channels = [
        ('tf1', 'TF1', 'tf1.png', 'tf1_fanart.jpg'),
        ('tmc', 'TMC', 'tmc.png', 'tmc_fanart.jpg'),
        ('tfx', 'TFX', 'tfx.png', 'tfx_fanart.jpg'),
        ('tf1-series-films', 'TF1 Séries Films', 'tf1seriesfilms.png', 'tf1seriesfilms_fanart.jpg')
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/fr/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/fr/' + channel_infos[3])
        item.set_callback(list_categories, channel_infos[0])
        item_post_treatment(item)
        yield item

    # Search feature
    item = Listitem.search(search)
    item_post_treatment(item)
    yield item


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
def search(plugin, search_query, **kwargs):
    plugin.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED)
    headers = {
        'content-type': 'application/json',
        'User-Agent': web_utils.get_random_ua()
    }

    # Programs
    params = {
        'id': '39d70f2bb3004cb243ee0e2e8b108a551940dd8bf9e31ef874dde1a2fe8f4d8d',
        'variables': '{"query":"%s","offset":0,"limit":500}' % search_query
    }
    resp = urlquick.get(URL_API, params=params, headers=headers)
    json_parser = json.loads(resp.text)
    for program_item in handle_programs(json_parser['data']['searchPrograms']['items']):
        yield program_item

    # Videos
    params = {
        'id': 'ac44a0378c28ea485c8c83cd83b12a9ee1606c4e451829ce8663287a8b001e30',
        'variables': '{"query":"%s","offset":0,"limit":500}' % search_query
    }
    resp = urlquick.get(URL_API, params=params, headers=headers)
    json_parser = json.loads(resp.text)
    for video_item in handle_videos(json_parser['data']['searchVideos']['items']):
        yield video_item


def handle_programs(program_items, category_id=None):
    for program_datas in program_items:
        is_category = False
        for category_datas in program_datas['categories']:
            if category_id is None:
                is_category = True
            elif category_id in category_datas['id']:
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
                              program_slug=program_slug)
            item_post_treatment(item)
            yield item


def handle_videos(video_items):
    for video_datas in video_items:
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
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
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
    for program_item in handle_programs(json_parser['data']['programs']['items'], category_id):
        yield program_item


@Route.register
def list_program_categories(plugin, program_slug, **kwargs):
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
                          program_slug=program_slug,
                          video_type_value=video_type_value,
                          offset='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, program_slug, video_type_value, offset, **kwargs):
    plugin.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED)
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

    video_items = json_parser['data']['programBySlug']['videos']['items']

    for video_item in handle_videos(video_items):
        yield video_item

    if len(video_items) == 20:
        yield Listitem.next_page(program_slug=program_slug,
                                 video_type_value=video_type_value,
                                 offset=str(int(offset) + 1))


@Resolver.register
def get_video_url(plugin,
                  video_id,
                  download_mode=False,
                  **kwargs):

    url_json = URL_VIDEO_STREAM % video_id
    htlm_json = urlquick.get(url_json,
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)
    json_parser = json.loads(htlm_json.text)

    if json_parser['delivery']['code'] > 400:
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    if download_mode:
        xbmcgui.Dialog().ok('Info', plugin.localize(30603))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    item = Listitem()
    item.path = json_parser['delivery']['url']
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = URL_LICENCE_KEY % video_id

    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    video_id = 'L_%s' % item_id.upper()
    url_json = URL_VIDEO_STREAM % video_id
    htlm_json = urlquick.get(url_json,
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)
    json_parser = json.loads(htlm_json.text)

    if json_parser['delivery']['code'] > 400:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    item = Listitem()
    item.path = json_parser['delivery']['url']
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = URL_LICENCE_KEY % video_id

    return item
