# -*- coding: utf-8 -*-
"""
    Copyright (C) 2016-2020 Team Catch-up TV & More
    This file is part of Catch-up TV & More.
    SPDX-License-Identifier: GPL-2.0-or-later
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals
from __future__ import division

from builtins import str
from resources.lib.py_utils import old_div
from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib.kodi_utils import get_kodi_version
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info
from resources.lib.addon_utils import get_item_media_path

import inputstreamhelper
import json
import re
import urlquick
from kodi_six import xbmc
from kodi_six import xbmcgui

# TO DO

URL_ROOT = 'https://www.dplay.co.uk'

URL_SHOWS = URL_ROOT + '/api/shows/%s'
# mode

URL_SHOWS_AZ = URL_ROOT + '/api/shows%s'
# mode

URL_VIDEOS = URL_ROOT + '/api/show-detail/%s'
# showId

URL_STREAM = URL_ROOT + '/api/video-playback/%s'
# path

URL_LIVE = URL_ROOT + '/api/channel-playback/%s'

URL_LICENCE_KEY = 'https://lic.caas.conax.com/nep/wv/license|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&PreAuthorization=%s&Host=lic.caas.conax.com|R{SSM}|'
# videoId

CATEGORIES_MODE = {
    'FEATURED': 'featured',
    'MOST POPULAR': 'most-popular',
    'NEW': 'new',
    'LEAVING SOON': 'last-chance',
    'Box Sets': 'box-set'
}

CATEGORIES_MODE_AZ = {'A-Z': '-az'}


@Route.register
def dplay_root(plugin, **kwargs):

    # (item_id, label, thumb, fanart)
    channels = [
        ('all', 'ALL', 'all.png', 'all_fanart.jpg'),
        ('quest', 'Quest', 'questtv.png', 'questtv_fanart.jpg'),
        ('really', 'Really', 'really.png', 'really_fanart.jpg'),
        ('quest-red', 'Quest Red', 'questred.png', 'questred_fanart.jpg'),
        ('food-network', 'Food Network', 'foodnetwork.png', 'foodnetwork_fanart.jpg'),
        ('dmax', 'DMAX', 'dmax.png', 'dmax_fanart.jpg'),
        ('home', 'HGTV', 'hgtv.png', 'hgtv_fanart.jpg')
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/uk/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/uk/' + channel_infos[3])
        item.set_callback(list_categories, channel_infos[0])
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
    if item_id == 'all':
        resp = urlquick.get(URL_SHOWS % category_name_value)
    else:
        resp = urlquick.get(URL_SHOWS % category_name_value + '?channel=%s' % item_id)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser["items"]:
        program_title = program_datas["title"]
        program_id = program_datas["id"]
        program_image = ''
        if 'image' in program_datas:
            program_image = program_datas["image"]["src"]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
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
    if item_id == 'all':
        resp = urlquick.get(URL_SHOWS_AZ % category_name_value)
    else:
        resp = urlquick.get(URL_SHOWS_AZ % category_name_value + '?channel=%s' % item_id)
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
                item.art['thumb'] = item.art['landscape'] = video_image
                item.art['fanart'] = video_image
                item.info["plot"] = video_plot
                item.info["duration"] = video_duration

                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_id=video_id)
                item_post_treatment(item,
                                    is_playable=True,
                                    is_downloadable=True)
                yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
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

        if get_kodi_version() < 18:
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
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
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
            return download.download_video(final_video_url)

        return final_video_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    resp = urlquick.get(URL_LIVE % item_id, max_age=-1)

    if len(re.compile(r'drmToken\"\:\"(.*?)\"').findall(resp.text)) > 0:
        token = re.compile(r'drmToken\"\:\"(.*?)\"').findall(resp.text)[0]
        if len(re.compile(r'streamUrlDash\"\:\"(.*?)\"').findall(
                resp.text)) > 0:
            live_url = re.compile(r'streamUrlDash\"\:\"(.*?)\"').findall(
                resp.text)[0]

            item = Listitem()
            item.path = live_url
            item.label = get_selected_item_label()
            item.art.update(get_selected_item_art())
            item.info.update(get_selected_item_info())
            item.property['inputstreamaddon'] = 'inputstream.adaptive'
            item.property['inputstream.adaptive.manifest_type'] = 'mpd'
            item.property[
                'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            item.property[
                'inputstream.adaptive.license_key'] = URL_LICENCE_KEY % token
            return item
    plugin.notify('ERROR', plugin.localize(30713))
    return False
