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

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download


import json
import re
import urlquick
import xbmcgui

# TO DO
# Playlists (cas les blagues de TOTO)
# Some DRM (m3u8) not working old videos (Kamelot)

# Thank you (https://github.com/peak3d/plugin.video.simple)


# Url to get channel's categories
# e.g. Info, Divertissement, Séries, ...
# We get an id by category
URL_ROOT = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
           'm6group_web/services/%s/folders?limit=999&offset=0'

# Url to get catgory's programs
# e.g. Le meilleur patissier, La france à un incroyable talent, ...
# We get an id by program
URL_CATEGORY = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
               'm6group_web/services/6play/folders/%s/programs' \
               '?limit=999&offset=0&csa=6&with=parentcontext'

# Url to get program's subfolders
# e.g. Saison 5, Les meilleurs moments, les recettes pas à pas, ...
# We get an id by subfolder
URL_SUBCATEGORY = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
                  'm6group_web/services/6play/programs/%s' \
                  '?with=links,subcats,rights'


# Url to get shows list
# e.g. Episode 1, Episode 2, ...
URL_VIDEOS = 'http://pc.middleware.6play.fr/6play/v2/platforms/' \
             'm6group_web/services/6play/programs/%s/videos?' \
             'csa=6&with=clips,freemiumpacks&type=vi,vc,playlist&limit=999'\
             '&offset=0&subcat=%s&sort=subcat'

URL_VIDEOS2 = 'https://pc.middleware.6play.fr/6play/v2/platforms/' \
              'm6group_web/services/6play/programs/%s/videos?' \
              'csa=6&with=clips,freemiumpacks&type=vi&limit=999&offset=0'


URL_JSON_VIDEO = 'https://pc.middleware.6play.fr/6play/v2/platforms/' \
                 'm6group_web/services/6play/videos/%s'\
                 '?csa=6&with=clips,freemiumpacks'


URL_IMG = 'https://images.6play.fr/v1/images/%s/raw'

URL_LIVE_JSON = 'https://pc.middleware.6play.fr/6play/v2/platforms/m6group_web/services/6play/live?channel=%s&with=service_display_images,nextdiffusion,extra_data'
# Chaine

DESIRED_QUALITY = Script.setting['quality']


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_categories(plugin, item_id)


@Route.register
def list_categories(plugin, item_id):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    if item_id == 'stories' or \
            item_id == 'comedy' or \
            item_id == 'rtl2' or \
            item_id == 'fun_radio':
        resp = urlquick.get(URL_ROOT % item_id)
    else:
        resp = urlquick.get(URL_ROOT % (item_id + 'replay'))
    json_parser = json.loads(resp.text)

    for array in json_parser:
        category_id = str(array['id'])
        category_name = array['name']

        item = Listitem()
        item.label = category_name
        item.set_callback(
            list_programs,
            item_id=item_id,
            category_id=category_id
        )
        yield item


@Route.register
def list_programs(plugin, item_id, category_id):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_CATEGORY % category_id)
    json_parser = json.loads(resp.text)

    for array in json_parser:
        item = Listitem()
        program_title = array['title']
        program_id = str(array['id'])
        program_desc = array['description']
        program_imgs = array['images']
        program_img = ''
        program_fanart = ''
        for img in program_imgs:
            if img['role'] == 'vignette':
                external_key = img['external_key']
                program_img = URL_IMG % (external_key)
            elif img['role'] == 'carousel':
                external_key = img['external_key']
                program_fanart = URL_IMG % (external_key)

        item.label = program_title
        item.art["thumb"] = program_img
        item.art["fanart"] = program_fanart
        item.info['plot'] = program_desc
        item.set_callback(
            list_program_categories,
            item_id=item_id,
            program_id=program_id
        )
        yield item


@Route.register
def list_program_categories(plugin, item_id, program_id):
    """
    Build program categories
    - Toutes les vidéos
    - Tous les replay
    - Saison 1
    - ...
    """
    resp = urlquick.get(URL_SUBCATEGORY % program_id)
    json_parser = json.loads(resp.text)

    for sub_category in json_parser['program_subcats']:
        item = Listitem()
        sub_category_id = str(sub_category['id'])
        sub_category_title = sub_category['title']

        item.label = sub_category_title
        item.set_callback(
            list_videos,
            item_id=item_id,
            program_id=program_id,
            sub_category_id=sub_category_id
        )
        yield item

    item = Listitem()
    item.label = plugin.localize(30701)
    item.set_callback(
        list_videos,
        item_id=item_id,
        program_id=program_id,
        sub_category_id=None
    )
    yield item


@Route.register
def list_videos(plugin, item_id, program_id, sub_category_id):

    url = ''
    if sub_category_id is None:
        url = URL_VIDEOS2 % program_id
    else:
        url = URL_VIDEOS % (program_id, sub_category_id)
    resp = urlquick.get(url)
    json_parser = json.loads(resp.text)

    # TO DO Playlist More one 'clips'
    if not json_parser:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False

    for video in json_parser:
        video_id = str(video['id'])

        title = video['title']
        duration = video['clips'][0]['duration']
        description = ''
        if 'description' in video:
            description = video['description']
        try:
            aired = video['clips'][0]['product']['last_diffusion']
            aired = aired
            aired = aired[:10]
            year = aired[:4]
            # date : string (%d.%m.%Y / 01.01.2009)
            # aired : string (2008-12-07)
            day = aired.split('-')[2]
            mounth = aired.split('-')[1]
            year = aired.split('-')[0]
            date = '.'.join((day, mounth, year))

        except Exception:
            aired = ''
            year = ''
            date = ''
        img = ''

        program_imgs = video['clips'][0]['images']
        program_img = ''
        for img in program_imgs:
                if img['role'] == 'vignette':
                    external_key = img['external_key']
                    program_img = URL_IMG % (external_key)

        item = Listitem()
        item.label = title
        item.info['plot'] = description
        item.info['duration'] = duration
        item.art["thumb"] = program_img
        item.art["fanart"] = program_img
        try:
            item.info.date(aired, '%Y-%m-%d')
        except:
            pass

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_id=video_id,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id
        )
        yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):

    video_json = urlquick.get(
        URL_JSON_VIDEO % video_id,
        headers={
            'User-Agent': web_utils.get_random_ua,
            'x-customer-name': 'm6web'},
        max_age=-1)
    json_parser = json.loads(video_json.text)

    video_assets = json_parser['clips'][0]['assets']

    if video_assets is None:
        plugin.notify('ERROR', plugin.localize(30712))
        return False

    final_video_url = ''
    all_datas_videos_quality = []
    all_datas_videos_path = []
    for asset in video_assets:
        if 'http_h264' in asset["type"]:
            all_datas_videos_quality.append(asset["video_quality"])
            all_datas_videos_path.append(
                asset['full_physical_path'])
        elif 'h264' in asset["type"]:
            manifest = urlquick.get(
                asset['full_physical_path'],
                headers={'User-Agent': web_utils.get_random_ua}, max_age=-1)
            if 'drm' not in manifest.text:
                all_datas_videos_quality.append(asset["video_quality"])
                all_datas_videos_path.append(
                    asset['full_physical_path'])

    if len(all_datas_videos_quality) == 0:
        Script.notify(
            "INFO",
            plugin.localize(LABELS['drm_notification']),
            Script.NOTIFY_INFO)
        return False
    elif len(all_datas_videos_quality) == 1:
        final_video_url = all_datas_videos_path[0]
    else:
        if DESIRED_QUALITY == "DIALOG":
            seleted_item = xbmcgui.Dialog().select(
                plugin.localize(LABELS['choose_video_quality']),
                all_datas_videos_quality)
            if seleted_item == -1:
                return False
            return all_datas_videos_path[seleted_item]
        elif DESIRED_QUALITY == "BEST":
            url_best = ''
            i = 0
            for data_video in all_datas_videos_quality:
                if 'lq' not in data_video:
                    url_best = all_datas_videos_path[i]
                i = i + 1
            final_video_url = url_best
        else:
            final_video_url = all_datas_videos_path[0]

    if download_mode:
        return download.download_video(final_video_url, video_label)
    return final_video_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    if item_id == 'fun_radio' or \
            item_id == 'rtl2':
        video_json = urlquick.get(
            URL_LIVE_JSON % (item_id),
            headers={'User-Agent': web_utils.get_random_ua}, max_age=-1)
        json_parser = json.loads(video_json.text)
        video_assets = json_parser[item_id][0]['live']['assets']

        if video_assets is None:
            plugin.notify('ERROR', plugin.localize(30712))
            return False

        for asset in video_assets:
            if 'delta_hls_h264' in asset["type"]:
                item = Listitem()
                item.path = asset['full_physical_path']
                item.label = item_dict['label']
                item.info.update(item_dict['info'])
                item.art.update(item_dict['art'])
                return item
    return False
