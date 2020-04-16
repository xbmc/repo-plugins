# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2018  SylvainCecchetto

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

from builtins import range
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib.menu_utils import item_post_treatment

import json
import re
import requests
import urlquick
from kodi_six import xbmcgui

# TO DO

DESIRED_QUALITY = Script.setting['quality']

URL_ROOT = 'https://www.mitele.es'

URL_LIVE_DATAS = 'http://indalo.mediaset.es/mmc-player/api/mmc/v1/%s/live/html5.json'
# channel name

URL_LIVE_STREAM = 'https://pubads.g.doubleclick.net/ssai/event/%s/streams'
# Live Id

URL_LIVE_HASH = 'https://gatekeeper.mediaset.es/'

URL_MAB = 'https://mab.mediaset.es/1.0.0/get'

URL_STREAM_DATAS = 'https://caronte.mediaset.es/delivery/vod/ooyala/%s/mtweb'

LIST_PROGRAMS = {
    "Informativos": "informativos",
    "Música": "musica",
    "Documentales": "documentales",
    "Cine": "peliculas",
    "Miniseries": "miniseries",
    "Programas": "programas-tv",
    "TV Movies": "tv-movies",
    "Series": "series-online",
    "Más deporte": "deportes"
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
    for category_title, category_program in list(LIST_PROGRAMS.items(
    )):
        item = Listitem()
        item.label = category_title
        item.set_callback(list_programs,
                          item_id=item_id,
                          category_program=category_program,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_program, page, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    datas = {
        'oid': 'bitban',
        'eid': '/automaticIndex/mtweb?url=www.mitele.es/%s/&page=%s&id=a-z&size=24' % (category_program, page)
    }
    resp = urlquick.get(URL_MAB, params=datas)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser["editorialObjects"]:
        program_title = program_datas["title"]
        program_image = program_datas["image"]["src"]
        program_url = URL_ROOT + program_datas["image"]["href"]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_sub_programs,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             category_program=category_program,
                             page=str(int(page) + 1))


@Route.register
def list_sub_programs(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    json_sub_programs_datas = re.compile(
        r'container_mtweb \= (.*?) \<\/script\>').findall(resp.text)[0]

    json_parser = json.loads(json_sub_programs_datas)

    for sub_program_datas in json_parser["container"]["tabs"]:

        if 'detail' not in sub_program_datas["type"]:
            sub_program_title = sub_program_datas["title"]
            sub_program_part_url = sub_program_datas["link"]["href"]
            sub_program_id = sub_program_datas["id"]

            item = Listitem()
            item.label = sub_program_title
            item.set_callback(list_videos,
                              item_id=item_id,
                              sub_program_part_url=sub_program_part_url,
                              sub_program_id=sub_program_id)
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, sub_program_part_url, sub_program_id, **kwargs):

    datas = {
        'oid': 'bitban',
        'eid': '/tabs/mtweb?url=www.mitele.es%s&tabId=%s' % (sub_program_part_url, sub_program_id)
    }
    resp = urlquick.get(URL_MAB, params=datas)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["contents"]:
        video_title = video_datas["title"] + ' - ' + video_datas["subtitle"]
        video_image = video_datas["images"]["thumbnail"]["src"]
        video_plot = video_datas["info"]["synopsis"]
        video_duration = 0
        if 'duration' in video_datas["info"]:
            video_duration = video_datas["info"]["duration"]
        video_url = URL_ROOT + video_datas["link"]["href"]
        content_id = video_datas["id"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url,
                          content_id=content_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  content_id,
                  download_mode=False,
                  **kwargs):

    session = urlquick.Session()

    resp = session.get(video_url,
                       headers={'User-Agent': web_utils.get_random_ua()},
                       max_age=-1)
    video_id = re.compile(
        r'dataMediaId\"\:\"(.*?)\"').findall(resp.text)[0]

    resp2 = session.get(URL_STREAM_DATAS % video_id,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    json_parser2 = json.loads(resp2.text)

    url_stream = ''
    for stream_datas in json_parser2["dls"]:
        if 'hls' in stream_datas["format"]:
            url_stream = stream_datas["stream"]

    datas = {
        'oid': 'bitban_api',
        'eid': '/api/greenBox?contentId=%s&platform=mtweb' % content_id
    }
    resp3 = session.get(URL_MAB, params=datas)
    json_parser3 = json.loads(resp3.text)

    session.get(json_parser2["cerbero"] + '/geo', headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)

    payload = {
        'bbx': json_parser2["bbx"],
        'gbx': json_parser3["gbx"]
    }
    resp4 = session.post(json_parser2["cerbero"],
                         json=payload,
                         headers={'User-Agent': web_utils.get_random_ua()},
                         max_age=-1)
    json_parser4 = json.loads(resp4.text)
    return url_stream + '?' + json_parser4["tokens"]["2"]["cdn"]


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    session_requests = requests.session()
    resp = session_requests.get(URL_LIVE_DATAS % item_id)
    json_parser = json.loads(resp.text)

    root = ''

    if json_parser["locations"][0]["ask"] is not None:
        lives_stream_json = session_requests.post(
            URL_LIVE_STREAM % json_parser["locations"][0]["ask"])
        lives_stream_jsonparser = json.loads(lives_stream_json.text)

        url_stream_without_hash = lives_stream_jsonparser["stream_manifest"]

        lives_hash_json = session_requests.post(
            URL_LIVE_HASH,
            data='{"gcp": "%s"}' % (json_parser["locations"][0]["gcp"]),
            headers={
                'Connection': 'keep-alive',
                'Content-type': 'application/json'
            })
        lives_hash_jsonparser = json.loads(lives_hash_json.text)

        if 'message' in lives_hash_jsonparser:
            if 'geoblocked' in lives_hash_jsonparser['message']:
                plugin.notify('ERROR', plugin.localize(30713))
            return False

        m3u8_video_auto = session_requests.get(url_stream_without_hash + '&' +
                                               lives_hash_jsonparser["suffix"])
    else:
        lives_stream_json = session_requests.post(
            URL_LIVE_HASH,
            data='{"gcp": "%s"}' % (json_parser["locations"][0]["gcp"]),
            headers={
                'Connection': 'keep-alive',
                'Content-type': 'application/json'
            })
        lives_stream_jsonparser = json.loads(lives_stream_json.text)

        if 'message' in lives_stream_jsonparser:
            if 'geoblocked' in lives_stream_jsonparser['message']:
                plugin.notify('ERROR', plugin.localize(30713))
            return False

        m3u8_video_auto = session_requests.get(
            lives_stream_jsonparser["stream"])
        root = lives_stream_jsonparser["stream"].split('master.m3u8')[0]

    lines = m3u8_video_auto.text.splitlines()
    if DESIRED_QUALITY == "DIALOG":
        all_datas_videos_quality = []
        all_datas_videos_path = []
        for k in range(0, len(lines) - 1):
            if 'RESOLUTION=' in lines[k]:
                all_datas_videos_quality.append(
                    lines[k].split('RESOLUTION=')[1])
                if 'http' in lines[k + 1]:
                    all_datas_videos_path.append(lines[k + 1])
                else:
                    all_datas_videos_path.append(root + '/' + lines[k + 1])
        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(LABELS['choose_video_quality']),
            all_datas_videos_quality)
        if seleted_item > -1:
            return all_datas_videos_path[seleted_item]
        else:
            return False
    elif DESIRED_QUALITY == 'BEST':
        # Last video in the Best
        for k in range(0, len(lines) - 1):
            if 'RESOLUTION=' in lines[k]:
                if 'http' in lines[k + 1]:
                    url = lines[k + 1]
                else:
                    url = root + '/' + lines[k + 1]
        return url
    else:
        for k in range(0, len(lines) - 1):
            if 'RESOLUTION=' in lines[k]:
                if 'http' in lines[k + 1]:
                    url = lines[k + 1]
                else:
                    url = root + '/' + lines[k + 1]
            break
        return url
