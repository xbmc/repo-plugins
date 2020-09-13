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

from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib.menu_utils import item_post_treatment
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info

import inputstreamhelper
import json
import re
import urlquick
from kodi_six import xbmc
from kodi_six import xbmcgui

# TO DO
# some videos are paid video (add account ?)

URL_ROOT = 'https://services.radio-canada.ca'

URL_REPLAY_BY_DAY = URL_ROOT + '/toutv/presentation/CatchUp?device=web&version=4'

URL_CATEGORIES = URL_ROOT + '/toutv/presentation/TagMenu?sort=Sequence&device=web&version=4'

URL_PROGRAMS = URL_ROOT + '/toutv/presentation/category/%s?device=web&version=4&sort=Popular&filter=All'
# category_key

URL_VIDEOS = URL_ROOT + '/toutv/presentation/%s?device=web&version=4'
# program_url

URL_STREAM_REPLAY = URL_ROOT + '/media/validation/v2/?connectionType=hd&output=json&multibitrate=true&deviceType=multiams&appCode=toutv&idMedia=%s'
# VideoId

URL_CLIENT_KEY_JS = 'https://ici.tou.tv/app.js'
# To GET client-key for menu

URL_CLIENT_KEY_VIDEO_JS = URL_ROOT + '/media/player/client/toutv_beta'

# TODO Get client key for


@Route.register
def list_categories(plugin, item_id, **kwargs):

    item = Listitem()
    item.label = 'Rattrapage'
    item.set_callback(list_days, item_id=item_id)
    item_post_treatment(item)
    yield item

    resp = urlquick.get(URL_CLIENT_KEY_JS)
    client_key_value = 'client-key %s' % re.compile(
        r'client-key \"\.concat\(\"(.*?)\"').findall(resp.text)[0]
    headers = {
        'Authorization': client_key_value,
        'Accept': 'application/json, text/plain, */*'
    }
    resp2 = urlquick.get(URL_CATEGORIES, headers=headers)
    json_parser = json.loads(resp2.text)

    for category_datas in json_parser["Types"]:
        category_title = category_datas["Title"]
        category_key = category_datas["Key"]

        item = Listitem()
        item.label = category_title
        item.set_callback(
            list_programs, item_id=item_id, category_key=category_key)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_key, **kwargs):

    resp = urlquick.get(URL_CLIENT_KEY_JS)
    client_key_value = 'client-key %s' % re.compile(
        r'client-key \"\.concat\(\"(.*?)\"').findall(resp.text)[0]
    headers = {
        'Authorization': client_key_value,
        'Accept': 'application/json, text/plain, */*'
    }
    resp2 = urlquick.get(URL_PROGRAMS % category_key, headers=headers)
    json_parser = json.loads(resp2.text)

    for program_datas in json_parser["LineupItems"]:
        if program_datas["IsFree"] is True:
            program_title = program_datas["Title"]
            program_image = program_datas["ImageUrl"].replace(
                'w_200,h_300', 'w_300,h_200')
            program_plot = program_datas["Description"]
            program_url = program_datas["Url"]

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            item.info["plot"] = program_plot
            if 'épisodes' in program_datas["Description"]:
                item.set_callback(
                    list_seasons, item_id=item_id, program_url=program_url)
            else:
                item.set_callback(
                    list_videos_programs,
                    item_id=item_id,
                    program_url=program_url,
                    season_name='season-1')
            item_post_treatment(item)
            yield item


@Route.register
def list_seasons(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(URL_CLIENT_KEY_JS)
    client_key_value = 'client-key %s' % re.compile(
        r'client-key \"\.concat\(\"(.*?)\"').findall(resp.text)[0]
    headers = {
        'Authorization': client_key_value,
        'Accept': 'application/json, text/plain, */*'
    }
    resp2 = urlquick.get(URL_VIDEOS % program_url, headers=headers)
    json_parser = json.loads(resp2.text)

    for season_datas in json_parser["EmisodeLineups"]:
        if season_datas["IsFree"] is True:
            season_title = season_datas["Title"]
            season_name = season_datas["Name"]

            item = Listitem()
            item.label = season_title
            item.set_callback(
                list_videos_programs,
                item_id=item_id,
                program_url=program_url,
                season_name=season_name)
            item_post_treatment(item)
            yield item


@Route.register
def list_videos_programs(plugin, item_id, program_url, season_name, **kwargs):

    resp = urlquick.get(URL_CLIENT_KEY_JS)
    client_key_value = 'client-key %s' % re.compile(
        r'client-key \"\.concat\(\"(.*?)\"').findall(resp.text)[0]
    headers = {
        'Authorization': client_key_value,
        'Accept': 'application/json, text/plain, */*'
    }
    resp2 = urlquick.get(URL_VIDEOS % program_url, headers=headers)
    json_parser = json.loads(resp2.text)

    for season_datas in json_parser["EmisodeLineups"]:
        if season_name in season_datas["Name"]:
            for video_datas in season_datas["LineupItems"]:
                if video_datas["IsFree"] is True:
                    if video_datas["EpisodeTitle"] in video_datas[
                            "ProgramTitle"]:
                        video_title = video_datas["ProgramTitle"]
                    else:
                        video_title = video_datas["ProgramTitle"] + ' - ' + video_datas["EpisodeTitle"]
                    video_plot = video_datas["Description"]
                    video_image = video_datas["ImageUrl"].replace(
                        'w_200,h_300', 'w_300,h_200')
                    video_duration = video_datas["Details"]["LengthInSeconds"]
                    video_id = video_datas["IdMedia"]

                    item = Listitem()
                    item.label = video_title
                    item.art['thumb'] = item.art['landscape'] = video_image
                    item.info['plot'] = video_plot
                    item.info['duration'] = video_duration
                    if video_datas["Details"]["AirDate"] is not None:
                        publication_date = video_datas["Details"][
                            "AirDate"].split(' ')[0]
                        item.info.date(publication_date, "%Y-%m-%d")
                    item.set_callback(
                        get_video_url,
                        item_id=item_id,
                        video_id=video_id)
                    item_post_treatment(
                        item, is_playable=True, is_downloadable=False)
                    yield item


@Route.register
def list_days(plugin, item_id, **kwargs):
    """
    Build categories listing
    - day 1
    - day 2
    - ...
    """
    resp = urlquick.get(URL_CLIENT_KEY_JS)
    client_key_value = 'client-key %s' % re.compile(
        r'client-key \"\.concat\(\"(.*?)\"').findall(resp.text)[0]
    headers = {
        'Authorization': client_key_value,
        'Accept': 'application/json, text/plain, */*'
    }
    resp2 = urlquick.get(URL_REPLAY_BY_DAY, headers=headers)
    json_parser = json.loads(resp2.text)

    for day_datas in json_parser["Lineups"]:
        day_title = day_datas["Title"]
        day_id = day_datas["Name"]

        item = Listitem()
        item.label = day_title
        item.set_callback(list_videos_days, item_id=item_id, day_id=day_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_days(plugin, item_id, day_id, **kwargs):

    resp = urlquick.get(URL_CLIENT_KEY_JS)
    client_key_value = 'client-key %s' % re.compile(
        r'client-key \"\.concat\(\"(.*?)\"').findall(resp.text)[0]
    headers = {
        'Authorization': client_key_value,
        'Accept': 'application/json, text/plain, */*'
    }
    resp2 = urlquick.get(URL_REPLAY_BY_DAY, headers=headers)
    json_parser = json.loads(resp2.text)

    for day_datas in json_parser["Lineups"]:

        if day_datas["Name"] == day_id:
            for video_datas in day_datas["LineupItems"]:
                if video_datas["IsFree"] is True:
                    video_title = video_datas["ProgramTitle"] + ' ' + video_datas["HeadTitle"]
                    video_plot = video_datas["Description"]
                    video_image = video_datas["ImageUrl"].replace(
                        'w_200,h_300', 'w_300,h_200')
                    video_id = video_datas["IdMedia"]

                    item = Listitem()
                    item.label = video_title
                    item.art['thumb'] = item.art['landscape'] = video_image
                    item.info['plot'] = video_plot
                    item.set_callback(
                        get_video_url,
                        item_id=item_id,
                        video_id=video_id)
                    item_post_treatment(
                        item, is_playable=True, is_downloadable=False)
                    yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    resp = urlquick.get(URL_CLIENT_KEY_VIDEO_JS)
    client_key_value = 'client-key %s' % re.compile(
        r'prod\"\,clientKey\:\"(.*?)\"').findall(resp.text)[0]
    headers = {'Authorization': client_key_value}
    resp2 = urlquick.get(
        URL_STREAM_REPLAY % video_id, headers=headers, max_age=-1)

    json_parser = json.loads(resp2.text)

    if json_parser["params"] is not None:
        licence_key_drm = ''
        for licence_key_drm_datas in json_parser["params"]:
            if 'widevineLicenseUrl' in licence_key_drm_datas["name"]:
                licence_key_drm = licence_key_drm_datas["value"]
        token_drm = ''
        for token_drm_datas in json_parser["params"]:
            if 'widevineAuthToken' in token_drm_datas["name"]:
                token_drm = token_drm_datas["value"]

        item = Listitem()
        item.path = json_parser["url"].replace('filter=',
                                               'format=mpd-time-csf,filter=')
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        item.property['inputstreamaddon'] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.property[
            'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
        item.property[
            'inputstream.adaptive.license_key'] = licence_key_drm + '|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Authorization=%s|R{SSM}|' % token_drm

        return item
    plugin.notify('ERROR', plugin.localize(30713))
    return False
