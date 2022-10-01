# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import datetime
import json
import re

import inputstreamhelper
from codequick import Listitem, Resolver, Route
from kodi_six import xbmcgui
import urlquick

from resources.lib import download
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment


# TO DO and Infos
# Add More Video_button (for emissions)
# Add Quality Mode / test Download Mode

URL_ROOT = 'https://www.%s.ch'
# channel_name

# Replay
URL_CATEGORIES_JSON = 'https://www.%s.ch/play/tv/'
# channel_name

URL_EMISSIONS = 'https://www.%s.ch/play/tv/%s?index=all'
# channel_name, name_emission

URL_LIST_EPISODES = 'https://www.%s.ch/play/v3/api/%s/production/videos-by-show-id'
# channel_name, channel_name, IdEmission

URL_LIST_VIDEOS = 'https://www.%s.ch/play/v3/api/%s/production/media-section'
# channel_name, channel_name, SectionId

# Live
URL_LIVE_JSON = 'https://www.%s.ch/play/v3/api/%s/production/tv-livestreams'
# channel_name, channel_name

URL_TOKEN = 'https://tp.srgssr.ch/akahd/token?acl=%s'
# acl

URL_INFO_VIDEO = 'https://il.srgssr.ch/integrationlayer' \
                 '/2.0/mediaComposition/byUrn/urn:%s:video:%s.json' \
                 '?onlyChapters=false&vector=portalplay'
# channel_name, video_id

EMISSIONS_NAME = {
    'rts': ['Émissions', 'emissions'],
    'rsi': ['Programmi', 'programmi'],
    'rtr': ['Emissiuns', 'emissiuns'],
    'srf': ['Sendungen', 'sendungen']
}

LIVE_LIVE_CHANNEL_NAME = {
    "rtsun": "RTS 1",
    "rtsdeux": "RTS 2",
    "rtsinfo": "RTS Info",
    "rtscouleur3": "Couleur 3",
    "rsila1": "RSI LA 1",
    "rsila2": "RSI LA 2",
    "srf1": "SRF 1",
    "srfinfo": "SRF info",
    "srfzwei": "SRF zwei",
    "rtraufsrf1": "RTR auf SRF 1",
    "rtraufsrfinfo": "RTR auf SRF Info",
    "rtraufsrf2": "RTR auf SRF 2"
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

    if item_id != 'swissinfo':
        # Emission
        category = EMISSIONS_NAME[item_id]
        category_url = URL_EMISSIONS % (item_id, category[1])

        item = Listitem()
        item.label = category[0]
        item.set_callback(list_programs,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item

    # Other categories (Info, Kids, ...)
    resp = urlquick.get(URL_CATEGORIES_JSON % item_id)
    json_value = re.compile(r'__SSR_VIDEO_DATA__ = (.*?)</script>').findall(resp.text)[0]
    json_parser = json.loads(json_value)
    for category_datas in json_parser["initialData"]["topics"]:
        category_title = category_datas["title"]
        category_image = ''
        if 'imageUrl' in category_datas:
            if 'rts.ch' in category_datas["imageUrl"]:
                category_image = category_datas["imageUrl"] + \
                    '/scale/width/448'
            else:
                category_image = category_datas["imageUrl"]
        category_urn = category_datas['urn']

        item = Listitem()
        item.label = category_title
        item.art['thumb'] = item.art['landscape'] = category_image
        item.set_callback(list_sub_categories,
                          item_id=item_id,
                          category_urn=category_urn)
        item_post_treatment(item)
        yield item


@Route.register
def list_sub_categories(plugin, item_id, category_urn, **kwargs):

    resp = urlquick.get(URL_CATEGORIES_JSON % item_id)
    json_value = re.compile(r'__SSR_VIDEO_DATA__ = (.*?)</script>').findall(resp.text)[0]
    json_parser = json.loads(json_value)

    for sub_category_datas in json_parser["initialData"]["pacPageConfigs"]["topicSections"][category_urn]:
        sub_category_title = ''
        if 'title' in sub_category_datas["representation"]:
            sub_category_title = sub_category_datas["representation"]["title"]
        section_id = sub_category_datas['id']

        item = Listitem()
        item.label = sub_category_title
        item.set_callback(list_videos_category,
                          item_id=item_id,
                          section_id=section_id)
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
    json_value = re.compile(r'__SSR_VIDEO_DATA__ = (.*?)</script>').findall(resp.text)[0]
    json_parser = json.loads(json_value)
    for program_datas in json_parser["initialData"]["shows"]:
        program_title = program_datas["title"]
        if 'rts.ch' in program_datas["imageUrl"]:
            program_image = program_datas["imageUrl"] + '/scale/width/448'
        else:
            program_image = program_datas["imageUrl"]
        program_id = program_datas["id"]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos_program,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_category(plugin, item_id, section_id, next_value=None, **kwargs):

    if next_value is not None:
        payload = {'sectionId': section_id, 'preview': False, 'next': next_value}
    else:
        payload = {'sectionId': section_id, 'preview': False}
    url_videos_datas = URL_LIST_VIDEOS % (item_id, item_id[:3])
    if item_id == 'swissinfo':
        url_videos_datas = url_videos_datas.replace('www', 'play')
    resp = urlquick.get(url_videos_datas, params=payload)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["data"]["data"]:
        video_title = video_datas['show']['title'] + ' - ' + video_datas['title']
        video_plot = ''
        if 'description' in video_datas:
            video_plot = video_datas["description"]
        video_image = video_datas["imageUrl"] + '/scale/width/448'
        video_id = video_datas["id"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_datas['duration'] / 1000
        item.info.date(video_datas['date'].split('T')[0], "%Y-%m-%d")

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if 'next' in json_parser["data"]:
        yield Listitem.next_page(item_id=item_id, section_id=section_id, next_value=json_parser['data']['next'])


@Route.register
def list_videos_program(plugin, item_id, program_id, next_value=None, **kwargs):

    if next_value is not None:
        payload = {'showId': program_id, 'next': next_value}
    else:
        payload = {'showId': program_id}
    resp = urlquick.get(URL_LIST_EPISODES % (item_id, item_id), params=payload)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["data"]["data"]:
        video_title = video_datas['show']['title'] + ' - ' + video_datas['title']
        video_plot = ''
        if 'description' in video_datas:
            video_plot = video_datas["description"]
        video_image = video_datas["imageUrl"] + '/scale/width/448'
        video_id = video_datas["id"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_datas['duration'] / 1000
        item.info.date(video_datas['date'].split('T')[0], "%Y-%m-%d")

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if 'next' in json_parser["data"]:
        yield Listitem.next_page(item_id=item_id, program_id=program_id, next_value=json_parser['data']['next'])


@Resolver.register
def get_video_url(plugin, item_id, video_id, download_mode=False, **kwargs):

    if item_id == 'swissinfo':
        channel_name_value = 'swi'
    else:
        channel_name_value = item_id
    resp = urlquick.get(URL_INFO_VIDEO % (channel_name_value, video_id))
    json_parser = json.loads(resp.text)

    # build stream_url
    is_drm = False
    for stream_datas in json_parser["chapterList"]:
        if video_id in stream_datas["id"]:
            for stream_datas_url in stream_datas["resourceList"]:
                if 'drmList' in stream_datas_url:
                    is_drm = True

    if is_drm:
        if get_kodi_version() < 18:
            xbmcgui.Dialog().ok(plugin.localize(14116), plugin.localize(30602))
            return False

        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
        if not is_helper.check_inputstream():
            return False

        if download_mode:
            return False

        licence_drm_url = ''
        for stream_datas in json_parser["chapterList"]:
            if video_id not in stream_datas["id"]:
                continue

            for stream_datas_url in stream_datas["resourceList"]:
                if 'DASH' not in stream_datas_url["streaming"]:
                    continue

                stream_url = stream_datas_url["url"]
                for licence_drm_datas in stream_datas_url["drmList"]:
                    if 'WIDEVINE' in licence_drm_datas["type"]:
                        licence_drm_url = licence_drm_datas["licenseUrl"]

        item = Listitem()
        item.path = stream_url
        item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
        item.property['inputstream.adaptive.license_key'] = licence_drm_url + '|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=srg.live.ott.irdeto.com|R{SSM}|'
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        return item

    stream_url = ''
    for stream_datas in json_parser["chapterList"]:
        if video_id in stream_datas["id"]:
            is_token = False
            for stream_datas_url in stream_datas["resourceList"]:
                if stream_datas_url['tokenType'] == 'NONE':
                    stream_url = stream_datas_url['url']
                else:
                    is_token = True
                    if 'HD' in stream_datas_url["quality"] and \
                            'mpegURL' in stream_datas_url["mimeType"]:
                        stream_url = stream_datas_url["url"]
                        break
                    if 'mpegURL' in stream_datas_url["mimeType"]:
                        stream_url = stream_datas_url["url"]
            if is_token:
                acl_value = '/i/%s/*' % (re.compile(r'\/i\/(.*?)\/master').findall(stream_url)[0])
                token_datas = urlquick.get(URL_TOKEN % acl_value, max_age=-1)
                token_jsonparser = json.loads(token_datas.text)
                token = token_jsonparser["token"]["authparams"]
                if '?' in stream_datas_url['url']:
                    stream_url = stream_url + '&' + token
                else:
                    stream_url = stream_url + '?' + token

    if download_mode:
        return download.download_video(stream_url)
    return stream_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE_JSON % (item_id[:3], item_id[:3]))
    json_parser = json.loads(resp.text)

    live_id = ''
    for live_datas in json_parser["data"]:
        if live_datas["title"] in LIVE_LIVE_CHANNEL_NAME[item_id]:
            live_id = live_datas["id"]
    if live_id is None:
        # Add Notification
        return False
    resp2 = urlquick.get(URL_INFO_VIDEO % (item_id[:3], live_id))
    json_parser2 = json.loads(resp2.text)

    # build stream_url
    stream_url = ''
    is_drm = False
    for stream_datas in json_parser2["chapterList"]:
        if live_id in stream_datas["id"]:
            for stream_datas_url in stream_datas["resourceList"]:
                if 'drmList' in stream_datas_url:
                    is_drm = True

    if is_drm:
        if get_kodi_version() < 18:
            xbmcgui.Dialog().ok(plugin.localize(14116), plugin.localize(30602))
            return False

        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
        if not is_helper.check_inputstream():
            return False

        licence_drm_url = ''
        for stream_datas in json_parser2["chapterList"]:
            if live_id in stream_datas["id"]:
                for stream_datas_url in stream_datas["resourceList"]:
                    stream_url = stream_datas_url["url"]
                    for licence_drm_datas in stream_datas_url["drmList"]:
                        if 'WIDEVINE' in licence_drm_datas["type"]:
                            licence_drm_url = licence_drm_datas["licenseUrl"]
                            item = Listitem()
                            item.path = stream_url
                            item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
                            item.property['inputstream.adaptive.manifest_type'] = 'mpd'
                            item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
                            item.property['inputstream.adaptive.license_key'] = licence_drm_url + '|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=srg.live.ott.irdeto.com|R{SSM}|'
                            item.property['inputstream.adaptive.manifest_update_parameter'] = 'full'
                            item.label = get_selected_item_label()
                            item.art.update(get_selected_item_art())
                            item.info.update(get_selected_item_info())
                            return item

    for stream_datas in json_parser2["chapterList"]:
        if live_id in stream_datas["id"]:
            for stream_datas_url in stream_datas["resourceList"]:
                if 'HD' in stream_datas_url["quality"] and \
                        'mpegURL' in stream_datas_url["mimeType"]:
                    stream_url = stream_datas_url["url"]
                    break

                if 'mpegURL' in stream_datas_url["mimeType"]:
                    stream_url = stream_datas_url["url"]

    acl_value = '/i/%s/*' % (re.compile(r'\/i\/(.*?)\/').findall(stream_url)[0])
    token_datas = urlquick.get(URL_TOKEN % acl_value, max_age=-1)
    token_jsonparser = json.loads(token_datas.text)
    token = token_jsonparser["token"]["authparams"]
    if '?' in stream_url:
        final_video_url = stream_url + '&' + token
    else:
        final_video_url = stream_url + '?' + token
    return final_video_url
