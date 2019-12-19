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
from __future__ import division

from builtins import str
from resources.lib.common import old_div
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
import resources.lib.cq_utils as cqu
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import inputstreamhelper
import json
import re
import urlquick
from kodi_six import xbmc
from kodi_six import xbmcgui

# TO DO

URL_ROOT = 'https://www.questod.co.uk'

URL_SHOWS = URL_ROOT + '/api/shows/%s'
# mode

URL_SHOWS_AZ = URL_ROOT + '/api/shows%s'
# mode

URL_VIDEOS = URL_ROOT + '/api/show-detail/%s'
# showId

URL_STREAM = URL_ROOT + '/api/video-playback/%s'
# path

URL_LIVE = 'https://www.questod.co.uk/channel/%s'

URL_LICENCE_KEY = 'https://lic.caas.conax.com/nep/wv/license|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&PreAuthorization=%s&Host=lic.caas.conax.com|R{SSM}|'
# videoId

CATEGORIES_MODE = {
    'FEATURED': 'featured',
    'MOST POPULAR': 'most-popular',
    'NEW': 'new',
    'LEAVING SOON': 'last-chance'
}

CATEGORIES_MODE_AZ = {'A-Z': '-az'}


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
    for category_name_title, category_name_value in list(CATEGORIES_MODE.items(
    )):

        item = Listitem()
        item.label = category_name_title
        item.set_callback(list_programs_mode,
                          item_id=item_id,
                          category_name_value=category_name_value)
        item_post_treatment(item)
        yield item

    for category_name_title, category_name_value in list(CATEGORIES_MODE_AZ.items(
    )):

        item = Listitem()
        item.label = category_name_title
        item.set_callback(list_programs_mode_az,
                          item_id=item_id,
                          category_name_value=category_name_value)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs_mode(plugin, item_id, category_name_value, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_SHOWS % category_name_value)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser["items"]:
        program_title = program_datas["title"]
        program_id = program_datas["id"]
        program_image = ''
        if 'image' in program_datas:
            program_image = program_datas["image"]["src"]

        item = Listitem()
        item.label = program_title
        item.art["thumb"] = program_image
        item.set_callback(list_program_seasons,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs_mode_az(plugin, item_id, category_name_value, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_SHOWS_AZ % category_name_value)
    json_parser = json.loads(resp.text)

    for program_datas_letter in json_parser["items"]:
        for program_datas in program_datas_letter["items"]:
            program_title = program_datas["title"]
            program_id = program_datas["id"]

            item = Listitem()
            item.label = program_title
            item.set_callback(list_program_seasons,
                              item_id=item_id,
                              program_id=program_id)
            item_post_treatment(item)
            yield item


@Route.register
def list_program_seasons(plugin, item_id, program_id, **kwargs):
    """
    Build programs listing
    - Season 1
    - ...
    """
    resp = urlquick.get(URL_VIDEOS % program_id)
    json_parser = json.loads(resp.text)

    for program_season_datas in json_parser["show"]["seasonNumbers"]:
        program_season_name = 'Season - ' + str(program_season_datas)
        program_season_number = program_season_datas

        item = Listitem()
        item.label = program_season_name
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_id=program_id,
                          program_season_number=program_season_number)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_id, program_season_number, **kwargs):

    resp = urlquick.get(URL_VIDEOS % program_id)
    json_parser = json.loads(resp.text)

    at_least_one_item = False

    if 'episode' in json_parser["videos"]:
        if str(program_season_number) in json_parser["videos"]["episode"]:
            for video_datas in json_parser["videos"]["episode"][str(
                    program_season_number)]:
                at_least_one_item = True
                video_title = video_datas["title"]
                video_duration = old_div(int(video_datas["videoDuration"]), 1000)
                video_plot = video_datas["description"]
                video_image = video_datas["image"]["src"]
                video_id = video_datas["path"]

                item = Listitem()
                item.label = video_title
                item.art["thumb"] = video_image
                item.art["fanart"] = video_image
                item.info["plot"] = video_plot
                item.info["duration"] = video_duration

                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_id=video_id,
                                  video_label=LABELS[item_id] + ' - ' +
                                  item.label,
                                  item_dict=item2dict(item))
                item_post_treatment(item,
                                    is_playable=True,
                                    is_downloadable=True)
                yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  item_dict,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(URL_STREAM % video_id, max_age=-1)
    json_parser = json.loads(resp.text)

    if 'error' in json_parser:
        if json_parser["error"] is not None:
            if json_parser["error"]["status"] == '403':
                plugin.notify('ERROR', plugin.localize(30713))
            else:
                plugin.notify('ERROR', plugin.localize(30716))
            return False

    if 'drmToken' in json_parser["playback"]:

        if cqu.get_kodi_version() < 18:
            xbmcgui.Dialog().ok('Info', plugin.localize(30602))
            return False

        is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
        if not is_helper.check_inputstream():
            return False

        if download_mode:
            xbmcgui.Dialog().ok('Info', plugin.localize(30603))
            return False

        token = json_parser["playback"]["drmToken"]

        item = Listitem()
        item.path = json_parser["playback"]["streamUrlDash"]
        item.label = item_dict['label']
        item.info.update(item_dict['info'])
        item.art.update(item_dict['art'])
        item.property['inputstreamaddon'] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.property[
            'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
        item.property[
            'inputstream.adaptive.license_key'] = URL_LICENCE_KEY % token

        return item
    else:
        final_video_url = json_parser["playback"]["streamUrlHls"]

        if download_mode:
            return download.download_video(final_video_url, video_label)

        return final_video_url


def live_entry(plugin, item_id, item_dict, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict, **kwargs):

    if cqu.get_kodi_version() < 18:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    if item_id == 'questtv':
        resp = urlquick.get(URL_LIVE % 'quest', max_age=-1)
    elif item_id == 'questred':
        resp = urlquick.get(URL_LIVE % 'quest-red', max_age=-1)

    if len(re.compile(r'drmToken\"\:\"(.*?)\"').findall(resp.text)) > 0:
        token = re.compile(r'drmToken\"\:\"(.*?)\"').findall(resp.text)[0]
        if len(re.compile(r'streamUrlDash\"\:\"(.*?)\"').findall(
                resp.text)) > 0:
            live_url = re.compile(r'streamUrlDash\"\:\"(.*?)\"').findall(
                resp.text)[0]

            item = Listitem()
            item.path = live_url
            if item_dict:
                if 'label' in item_dict:
                    item.label = item_dict['label']
                if 'info' in item_dict:
                    item.info.update(item_dict['info'])
                if 'art' in item_dict:
                    item.art.update(item_dict['art'])
            else:
                item.label = LABELS[item_id]
                item.art["thumb"] = ""
                item.art["icon"] = ""
                item.art["fanart"] = ""
                item.info["plot"] = LABELS[item_id]
            item.property['inputstreamaddon'] = 'inputstream.adaptive'
            item.property['inputstream.adaptive.manifest_type'] = 'mpd'
            item.property[
                'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            item.property[
                'inputstream.adaptive.license_key'] = URL_LICENCE_KEY % token
            return item
    plugin.notify('ERROR', plugin.localize(30713))
    return False
