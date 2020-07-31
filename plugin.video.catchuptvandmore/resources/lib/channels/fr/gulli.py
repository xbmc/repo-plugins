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

# Verify md5 still present in hashlib python 3 (need to find another way if it is not the case)
# https://docs.python.org/3/library/hashlib.html
from hashlib import md5

import re
import json
import time
import urlquick

# TO DO
# Improve Live TV (Title, picture, plot)

SECRET_KEY = '19nBVBxv791Xs'

CATEGORIES = {}

CATEGORIES['Dessins animés'] = (
    'http://sslreplay.gulli.fr/replay/api?'
    'call=%%7B%%22api_key%%22:%%22%s%%22,%%22'
    'method%%22:%%22programme.getLatest'
    'Episodes%%22,%%22params%%22:%%7B%%22'
    'program_image_thumb%%22:%%5B310,230%%5D,%%22'
    'category_id%%22:%%22dessins-animes%%22%%7D%%7D')

CATEGORIES['Émissions'] = (
    'https://sslreplay.gulli.fr/replay/api?'
    'call=%%7B%%22api_key%%22:%%22%s%%22,%%22method'
    '%%22:%%22programme.getLatestEpisodes%%22,%%'
    '22params%%22:%%7B%%22program_image_thumb%%'
    '22:%%5B310,230%%5D,%%22category_id%%22:%%22'
    'emissions%%22%%7D%%7D')

CATEGORIES['Séries & films'] = (
    'https://sslreplay.gulli.fr/replay/api?'
    'call=%%7B%%22api_key%%22:%%22%s%%22,%%2'
    '2method%%22:%%22programme.getLatest'
    'Episodes%%22,%%22params%%22:%%7B%%22program_'
    'image_thumb%%22:%%5B310,230%%5D,%%22category'
    '_id%%22:%%22series%%22%%7D%%7D')

URL_LIST_SHOW = (
    'https://sslreplay.gulli.fr/replay/api?call=%%7B%%22api_key'
    '%%22:%%22%s%%22,%%22'
    'method%%22:%%22programme.getEpisodesByProgramIds%%22,%%22'
    'params%%22:%%7B%%22program_id_list%%22:%%5B%%22%s%%22%%5D'
    '%%7D%%7D')

URL_LIVE_TV = 'http://replay.gulli.fr/Direct'


def get_api_key():
    """Compute the API key"""
    date = time.strftime("%Y%m%d")
    key = SECRET_KEY + date
    key = md5(key.encode('utf-8')).hexdigest()
    return 'iphoner_' + key


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    for category_title, program_url in list(CATEGORIES.items()):
        item = Listitem()
        item.label = category_title
        item.set_callback(list_programs,
                          item_id=item_id,
                          program_url=program_url % get_api_key())
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, program_url, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(program_url,
                        headers={'User-Agent': web_utils.get_random_ua()})
    json_parser = json.loads(resp.text)

    for program in json_parser['res']:
        program_title = program['program_title']
        program_id = program['program_id']
        program_image = program['program_image']

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.art['fanart'] = program_image
        item.set_callback(list_videos, item_id=item_id, program_id=program_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_id, **kwargs):

    resp = urlquick.get(URL_LIST_SHOW % (get_api_key(), program_id),
                        headers={'User-Agent': web_utils.get_random_ua()})
    json_parser = json.loads(resp.text)

    for show in json_parser['res']:
        # media_id = show['media_id']
        # program_title = show['program_title']
        # cat_id = show['cat_id']
        # program_id = show['program_id']
        fanart = show['program_image']
        thumb = show['episode_image']
        episode_title = show['episode_title']
        episode_number = show['episode_number']
        season_number = show['season_number']
        # total_episodes_in_season = show['total_episodes_in_season']
        video_url = show['url_streaming']
        # url_streaming = show['url_streaming']
        short_desc = show['short_desc']
        note = float(show['note']) * 2
        date_debut = show['date_debut']
        # "2017-02-03 00:00:00"
        year = int(date_debut[:4])
        day = date_debut[8:10]
        month = date_debut[5:7]
        date = '.'.join((day, month, str(year)))
        aired = '-'.join((str(year), month, day))

        item = Listitem()
        item.label = episode_title
        item.info['episode'] = episode_number
        item.info['season'] = season_number
        item.info['plot'] = short_desc
        item.info['rating'] = note
        item.info['date'] = date
        item.info['aired'] = aired
        item.info['year'] = year
        item.art['thumb'] = item.art['landscape'] = thumb
        item.art['fanart'] = fanart

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

    if download_mode:
        return download.download_video(video_url)
    return video_url


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    url_live = ''
    live_html = urlquick.get(URL_LIVE_TV,
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)
    url_live_embeded = re.compile('<iframe src=\"(.*?)\"').findall(
        live_html.text)[0]
    root_live_embeded_html = urlquick.get(
        url_live_embeded,
        headers={'User-Agent': web_utils.get_random_ua()},
        max_age=-1)
    all_url_video = re.compile(r'file: \'(.*?)\'').findall(
        root_live_embeded_html.text)

    for url_video in all_url_video:
        if url_video.count('m3u8') > 0:
            url_live = url_video
    return url_live
