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

from resources.lib.codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import htmlement
import json
import re
import requests
from resources.lib import urlquick
from kodi_six import xbmcgui

# TO DO
# Fix Live TV

URL_ROOT = 'https://www.nrj-play.fr'

URL_REPLAY = URL_ROOT + '/%s/replay'
# channel_name (nrj12, ...)

URL_COMPTE_LOGIN = 'https://user-api2.nrj.fr/api/5/login'
# TO DO add account for using Live Direct

URL_LIVE_WITH_TOKEN = URL_ROOT + '/compte/live?channel=%s'
# channel (nrj12, ...) -
# call this url after get session (url live with token inside this page)


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
    resp = urlquick.get(URL_REPLAY % item_id)
    root = resp.parse("ul", attrs={"class": "subNav-menu hidden-xs"})

    for category_datas in root.iterfind(".//a"):
        category_title = category_datas.text.strip()
        category_url = URL_ROOT + category_datas.get('href')

        item = Listitem()
        item.label = category_title
        item.set_callback(list_programs,
                          item_id=item_id,
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
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='linkProgram-visual']"):

        program_title = program_datas.find('.//img').get('alt')
        program_url = URL_ROOT + program_datas.find('.//a').get('href')
        program_image = ''
        if program_datas.find('.//source').get('data-srcset') is not None:
            program_image = program_datas.find('.//source').get('data-srcset')
        else:
            program_image = program_datas.find('.//source').get('srcset')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_title=program_title,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_title, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()

    if len(root.findall(".//figure[@class='thumbnailReplay-visual']")) > 0:
        for video_datas in root.findall(
                ".//figure[@class='thumbnailReplay-visual']"):
            video_title = program_title + ' - ' + video_datas.find(
                './/img').get('alt')
            video_url = URL_ROOT + video_datas.find('.//a').get('href')
            video_image = ''
            if video_datas.find('.//source').get('data-srcset') is not None:
                video_image = video_datas.find('.//source').get('data-srcset')
            else:
                video_image = video_datas.find('.//source').get('srcset')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item
    else:
        video_title = root.find(".//div[@class='nrjVideo-player']").find(
            './/meta').get('alt')
        video_url = program_url
        video_image = root.find(".//div[@class='nrjVideo-player']").find(
            './/meta').get('content')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

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
    # Just One format of each video (no need of QUALITY)
    resp = urlquick.get(video_url)
    root = resp.parse("div", attrs={"class": "nrjVideo-player"})

    stream_url = ''
    for stream in root.iterfind(".//meta"):
        if 'mp4' in stream.get('content'):
            stream_url = stream.get('content')

    if download_mode:
        return download.download_video(stream_url)
    return stream_url


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    # Live TV Not working / find a way to dump html received

    # Create session
    # KO - session_urlquick = urlquick.Session()
    session_requests = requests.session()

    # Build PAYLOAD
    payload = {
        "email": plugin.setting.get_string('nrj.login'),
        "password": plugin.setting.get_string('nrj.password')
    }
    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'origin': 'https://www.nrj-play.fr',
        'referer': 'https://www.nrj-play.fr/'
    }

    # LOGIN
    # KO - resp2 = session_urlquick.post(
    #     URL_COMPTE_LOGIN, data=payload,
    #     headers={'User-Agent': web_utils.get_ua, 'referer': URL_COMPTE_LOGIN})
    resp2 = session_requests.post(URL_COMPTE_LOGIN,
                                  data=payload,
                                  headers=headers)
    if 'error alert alert-danger' in repr(resp2.text):
        plugin.notify('ERROR', 'NRJ : ' + plugin.localize(30711))
        return False

    # GET page with url_live with the session logged
    # KO - resp3 = session_urlquick.get(
    #     URL_LIVE_WITH_TOKEN % item_id,
    #     headers={'User-Agent': web_utils.get_ua, 'referer': URL_LIVE_WITH_TOKEN % item_id})
    resp3 = session_requests.get(URL_LIVE_WITH_TOKEN % (item_id),
                                 headers=dict(referer=URL_LIVE_WITH_TOKEN %
                                              (item_id)))

    parser = htmlement.HTMLement()
    parser.feed(resp3.text)
    root = parser.close()
    live_data = root.find(".//div[@class='player']")

    url_live_json = live_data.get('data-options')
    url_live_json_jsonparser = json.loads(url_live_json)
    return url_live_json_jsonparser["file"]
