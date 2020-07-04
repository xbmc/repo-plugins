# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto

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
from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info

import inputstreamhelper
import datetime
import json
import re
import urlquick
from kodi_six import xbmc
from kodi_six import xbmcgui

# TO DO and Infos
# Add More Video_button (for emissions)
# Add Quality Mode / test Download Mode

URL_ROOT = 'https://www.%s.ch'
# channel_name

# Replay
URL_CATEGORIES_JSON = 'https://www.%s.ch/play/v2/tv/topicList?layout=json'
# channel_name

URL_EMISSIONS = 'https://www.%s.ch/play/tv/%s?index=all'
# channel_name, name_emission

URL_LIST_EPISODES = 'https://www.%s.ch/play/v2/tv/show/%s/' \
                    'latestEpisodes?numberOfEpisodes=50' \
                    '&tillMonth=%s&layout=json'
# channel_name, IdEmission, ThisMonth (11-2017)

# Live
URL_LIVE_JSON = 'http://www.%s.ch/play/v2/tv/live/overview?layout=json'
# (www or play) channel_name

URL_API_V3 = 'https://%s.%s.ch/play/v3/api/%s/production/%s'
# channel_name, channel_name, API method

URL_TOKEN = 'https://tp.srgssr.ch/akahd/token?acl=%s'
# acl

URL_INFO_VIDEO = 'https://il.srgssr.ch/integrationlayer' \
                 '/2.0/%s/mediaComposition/video/%s.json' \
                 '?onlyChapters=true&vector=portalplay'
# channel_name, video_id

EMISSIONS_NAME = {
    'rts': ['Émissions', 'emissions'],
    'rsi': ['Programmi', 'programmi'],
    'rtr': ['Emissiuns', 'emissiuns'],
    'srf': ['Sendungen', 'sendungen']
}

LIVE_LIVE_CHANNEL_NAME = {
    "rtsun": "RTS Un",
    "rtsdeux": "RTS Deux",
    "rtsinfo": "RTS Info",
    "rtscouleur3": "RTS Couleur 3",
    "rsila1": "RSI LA 1",
    "rsila2": "RSI LA 2",
    "srf1": "SRF 1",
    "srfinfo": "SRF info",
    "srfzwei": "SRF zwei",
    "rtraufsrf1": "RTR auf SRF 1",
    "rtraufsrfinfo": "RTR auf SRF Info",
    "rtraufsrf2": "RTR auf SRF 2"
}

SWISSINFO_TOPICS = {
    'Business': 1,
    'Culrure': 2,
    'Politics': 4,
    'Sci & Tech': 5,
    'Society': 6
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
    if item_id == 'swissinfo':
        for topic_name, topic_id in SWISSINFO_TOPICS.items():
            item = Listitem()
            item.label = topic_name
            item.set_callback(list_videos_category,
                              item_id=item_id,
                              category_id=topic_id)
            item_post_treatment(item)
            yield item
    else:
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
        json_parser = json.loads(resp.text)

        for category_datas in json_parser:
            item = Listitem()
            item.label = category_datas['title']
            category_url = URL_ROOT % item_id + \
                category_datas["latestModuleUrl"]

            item.set_callback(list_videos_category,
                              item_id=item_id,
                              category_id=category_datas['id'],
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
    resp = urlquick.get(category_url)
    if item_id == 'rsi':
        json_value = re.compile(
            r'data-alphabetical-sections=\\\"(.*?)\\\"').findall(resp.text)[0]
        json_value = json_value.replace('&quot;', '"')
        json_value = json_value.replace('\\\\"', ' ')
        json_parser = json.loads(json_value)
        for list_letter in json_parser:
            for program_datas in list_letter["showTeaserList"]:
                program_title = program_datas["title"]
                if 'rts.ch' in program_datas["imageUrl"]:
                    program_image = program_datas["imageUrl"] + \
                        '/scale/width/448'
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
    else:
        json_value = re.compile(
            r'__SSR_DATA__ = (.*?)</script>').findall(resp.text)[0]
        json_parser = json.loads(json_value)
        for program_datas in json_parser["initialData"]["shows"]:
            program_title = program_datas["title"]
            if 'rts.ch' in program_datas["imageUrl"]:
                program_image = program_datas["imageUrl"] + \
                    '/scale/width/448'
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
def list_videos_category(plugin, item_id, category_id, category_url=None, next_page=None, **kwargs):
    if item_id == 'rsi':
        resp = urlquick.get(category_url)
        json_value = re.compile(r'data-teaser=\"(.*?)\"').findall(resp.text)[0]
        json_value = json_value.replace('&quot;', '"')
        json_parser = json.loads(json_value)

        for video_datas in json_parser:
            video_title = ''
            if 'showTitle' in video_datas:
                video_title = video_datas["showTitle"] + \
                    ' - ' + video_datas["title"]
            else:
                video_title = video_datas["title"]
            video_plot = ''
            if 'description' in video_datas:
                video_plot = video_datas["description"]
            video_image = video_datas["imageUrl"] + '/scale/width/448'
            video_url = video_datas["absoluteDetailUrl"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item
    else:

        url = URL_API_V3 % (
            'play' if item_id == 'swissinfo' else 'www',
            item_id,
            'swi' if item_id == 'swissinfo' else item_id,
            'latest-media-by-topic')
        params = {'topicId': category_id}
        if next_page:
            params['next'] = next_page
        resp = urlquick.get(url, params=params)
        json_parser = json.loads(resp.text)

        for video_datas in json_parser['data']['data']:
            video_title = ''
            if 'showTitle' in video_datas:
                video_title = video_datas["showTitle"] + \
                    ' - ' + video_datas["title"]
            else:
                video_title = video_datas["title"]
            video_plot = ''
            if 'description' in video_datas:
                video_plot = video_datas["description"]
            video_image = video_datas["imageUrl"] + '/scale/width/448'
            video_id = video_datas['id']

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['plot'] = video_plot
            item.info['duration'] = video_datas['duration'] / 1000
            item.info.date(video_datas['date'].split('T')[0], "%Y-%m-%d")

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url='',
                              video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item
        if 'next' in json_parser['data']:
            yield Listitem.next_page(item_id=item_id,
                                     category_id=category_id,
                                     next_page=json_parser['data']['next'])


@Route.register
def list_videos_program(plugin, item_id, program_id, **kwargs):

    date = datetime.datetime.now()
    actual_month = str(date).split(' ')[0].split('-')[1] + '-' + \
        str(date).split(' ')[0].split('-')[0]

    resp = urlquick.get(URL_LIST_EPISODES %
                        (item_id, program_id, actual_month))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["episodes"]:
        video_title = ''
        if 'showTitle' in video_datas:
            video_title = video_datas["showTitle"] + \
                ' - ' + video_datas["title"]
        else:
            video_title = video_datas["title"]
        video_plot = ''
        if 'description' in video_datas:
            video_plot = video_datas["description"]
        video_image = video_datas["imageUrl"] + '/scale/width/448'
        video_url = video_datas["absoluteDetailUrl"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        time_splitted = video_datas['duration'].split(':')
        item.info['duration'] = int(time_splitted[0]) * 60 + int(time_splitted[1])
        try:
            item.info.date(video_datas['date'].split(',')[0], "%d-%m-%Y")
        except Exception:
            pass

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

    if 'video_id' in kwargs:
        video_id = kwargs['video_id']
    else:
        video_id = video_url.split('=')[1]
    if item_id == 'swissinfo':
        channel_name_value = 'swi'
    else:
        channel_name_value = item_id
    resp = urlquick.get(URL_INFO_VIDEO % (channel_name_value, video_id))
    json_parser = json.loads(resp.text)

    # build url
    stream_url = ''
    for stream_datas in json_parser["chapterList"]:
        if video_id in stream_datas["id"]:
            for stream_datas_url in stream_datas["resourceList"]:
                if 'HD' in stream_datas_url["quality"] and \
                        'mpegURL' in stream_datas_url["mimeType"]:
                    stream_url = stream_datas_url["url"]
                    break
                else:
                    if 'mpegURL' in stream_datas_url["mimeType"]:
                        stream_url = stream_datas_url["url"]
    acl_value = '/i/%s/*' % (
        re.compile(r'\/i\/(.*?)\/master').findall(stream_url)[0])
    token_datas = urlquick.get(URL_TOKEN % acl_value)
    token_jsonparser = json.loads(token_datas.text)
    token = token_jsonparser["token"]["authparams"]

    if '?' in stream_url:
        final_video_url = stream_url + '&' + token
    else:
        final_video_url = stream_url + '?' + token

    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_LIVE_JSON % item_id[:3])
    json_parser = json.loads(resp.text)
    live_id = ''
    for live_datas in json_parser["teaser"]:
        if live_datas["channelName"] in LIVE_LIVE_CHANNEL_NAME[item_id]:
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
            xbmcgui.Dialog().ok('Info', plugin.localize(30602))
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
        item.property['inputstreamaddon'] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.property[
            'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
        item.property[
            'inputstream.adaptive.license_key'] = licence_drm_url + '|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=srg.live.ott.irdeto.com|R{SSM}|'

        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        return item

    else:
        for stream_datas in json_parser2["chapterList"]:
            if live_id in stream_datas["id"]:
                for stream_datas_url in stream_datas["resourceList"]:
                    if 'HD' in stream_datas_url["quality"] and \
                            'mpegURL' in stream_datas_url["mimeType"]:
                        stream_url = stream_datas_url["url"]
                        break
                    else:
                        if 'mpegURL' in stream_datas_url["mimeType"]:
                            stream_url = stream_datas_url["url"]

        acl_value = '/i/%s/*' % (
            re.compile(r'\/i\/(.*?)\/').findall(stream_url)[0])
        token_datas = urlquick.get(URL_TOKEN % acl_value, max_age=-1)
        token_jsonparser = json.loads(token_datas.text)
        token = token_jsonparser["token"]["authparams"]
        if '?' in stream_url:
            final_video_url = stream_url + '&' + token
        else:
            final_video_url = stream_url + '?' + token
        return final_video_url
