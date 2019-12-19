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
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib import download
import resources.lib.cq_utils as cqu
from resources.lib.listitem_utils import item_post_treatment, item2dict

import json
import time
import urlquick
from kodi_six import xbmcgui
'''
Channels:
    * Franceinfo
'''

URL_API = utils.urljoin_partial('http://api-front.yatta.francetv.fr')

URL_LIVE_JSON = URL_API('standard/edito/directs')

URL_JT_ROOT = 'https://stream.francetvinfo.fr/stream/program/list.json/origin/jt/support/long/page/1/nb/1000'

URL_MAGAZINES_ROOT = 'https://stream.francetvinfo.fr/stream/program/list.json/origin/magazine/support/long/page/1/nb/1000'

URL_AUDIO_ROOT = 'https://stream.francetvinfo.fr/stream/program/list.json/origin/audio/support/long/page/1/nb/1000'

URL_STREAM_ROOT = 'https://stream.francetvinfo.fr'

URL_VIDEOS_ROOT = 'https://stream.francetvinfo.fr/stream/contents/list/videos.json/support/long'

URL_MODULES_ROOT = 'https://stream.francetvinfo.fr/stream/contents/list/videos-selection.json/support/long'

URL_INFO_OEUVRE = 'https://sivideo.webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/?idDiffusion=%s&catalogue=Info-web'
# Param : id_diffusion

DESIRED_QUALITY = Script.setting['quality']


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
    category_title = 'Videos'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos,
                      item_id=item_id,
                      next_url=URL_VIDEOS_ROOT,
                      page='1')
    item_post_treatment(item)
    yield item

    category_title = 'Audio'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_programs, item_id=item_id, next_url=URL_AUDIO_ROOT)
    item_post_treatment(item)
    yield item

    category_title = 'JT'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_programs, item_id=item_id, next_url=URL_JT_ROOT)
    item_post_treatment(item)
    yield item

    category_title = 'Magazines'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_programs,
                      item_id=item_id,
                      next_url=URL_MAGAZINES_ROOT)
    item_post_treatment(item)
    yield item

    category_title = 'Modules'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos,
                      item_id=item_id,
                      next_url=URL_MODULES_ROOT,
                      page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_programs(plugin, item_id, next_url, **kwargs):

    resp = urlquick.get(next_url)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser['programs']:
        program_title = program_datas['label']
        program_url = URL_STREAM_ROOT + program_datas['url']
        program_plot = program_datas['description']

        item = Listitem()
        item.label = program_title
        item.info['plot'] = program_plot
        item.set_callback(list_videos,
                          item_id=item_id,
                          next_url=program_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, next_url, page, **kwargs):

    resp = urlquick.get(next_url + '/page/' + page)
    json_parser = json.loads(resp.text)
    if 'videos' in json_parser:
        list_id = 'videos'
    elif 'contents' in json_parser:
        list_id = 'contents'

    at_least_one_item = False
    for video_datas in json_parser[list_id]:
        at_least_one_item = True
        video_title = video_datas['title']
        video_plot = video_datas['description']
        date_epoch = video_datas['lastPublicationDate']
        date_value = time.strftime('%Y-%m-%d', time.localtime(date_epoch))
        video_url = URL_STREAM_ROOT + video_datas['url']
        video_image = ''
        for media_datas in video_datas['medias']:
            if 'urlThumbnail' in media_datas:
                video_image = URL_STREAM_ROOT + media_datas['urlThumbnail']
                break

        item = Listitem()
        item.label = video_title
        item.info['plot'] = video_plot
        item.art['thumb'] = video_image
        item.info.date(date_value, '%Y-%m-%d')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          item_dict=item2dict(item))
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if at_least_one_item:
        yield Listitem.next_page(item_id=item_id,
                                 next_url=next_url,
                                 page=str(int(page) + 1))
    else:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  item_dict=None,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(video_url)
    json_parser = json.loads(resp.text)

    method = None
    id_diffusion = ''
    urls = []
    for media in json_parser['content']['medias']:
        if 'catchupId' in media:
            method = 'id_diffusion'
            id_diffusion = media['catchupId']
            break
        elif 'streams' in media:
            method = 'stream_videos'
            for stream in media['streams']:
                urls.append((stream['format'], stream['url']))
            break
        elif 'sourceUrl' in media:
            return media['sourceUrl']
    if method == 'id_diffusion':
        return resolver_proxy.get_francetv_video_stream(
            plugin, id_diffusion, item_dict, download_mode, video_label)
    elif method == 'stream_videos':
        url_hd = ''
        url_default = ''
        for url in urls:
            if 'hd' in url[0]:
                url_hd = url[1]
            url_default = url[1]

        if DESIRED_QUALITY == "DIALOG":
            items = []
            for url in urls:
                items.append(url[0])
            seleted_item = xbmcgui.Dialog().select(
                plugin.localize(LABELS['choose_video_quality']), items)

            if seleted_item == -1:
                return False
            url_selected = items[seleted_item][1]
            if url_hd != '':
                url_selected = url_hd
            else:
                url_selected = url_default
        else:
            if url_hd != '':
                url_selected = url_hd
            else:
                url_selected = url_default
        if download_mode:
            return download.download_video(url_selected, video_label)
        return url_selected
    else:
        return False


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    resp = urlquick.get(URL_LIVE_JSON,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    json_parser = json.loads(resp.text)

    for live in json_parser["result"]:
        if live["channel"] == item_id:
            live_datas = live["collection"][0]["content_has_medias"]
            liveId = ''
            for live_data in live_datas:
                if "si_direct_id" in live_data["media"]:
                    liveId = live_data["media"]["si_direct_id"]
            return resolver_proxy.get_francetv_live_stream(plugin, liveId)
