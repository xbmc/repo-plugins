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

from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download

import json
import urlquick

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

CATEGORIES_MODE = {
    'FEATURED': 'featured',
    'MOST POPULAR': 'most-popular',
    'NEW': 'new',
    'LEAVING SOON': 'leaving-soon'
}

CATEGORIES_MODE_AZ = {
    'A-Z': '-az'
}


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
    for category_name_title, category_name_value in CATEGORIES_MODE.iteritems():

        item = Listitem()
        item.label = category_name_title
        item.set_callback(
            list_programs_mode,
            item_id=item_id,
            category_name_value=category_name_value
        )
        yield item

    for category_name_title, category_name_value in CATEGORIES_MODE_AZ.iteritems():

        item = Listitem()
        item.label = category_name_title
        item.set_callback(
            list_programs_mode_az,
            item_id=item_id,
            category_name_value=category_name_value
        )
        yield item


@Route.register
def list_programs_mode(plugin, item_id, category_name_value):
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
        program_image = program_datas["image"]["src"]

        item = Listitem()
        item.label = program_title
        item.art["thumb"] = program_image
        item.set_callback(
            list_program_seasons,
            item_id=item_id,
            program_id=program_id
        )
        yield item


@Route.register
def list_programs_mode_az(plugin, item_id, category_name_value):
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
            item.set_callback(
                list_program_seasons,
                item_id=item_id,
                program_id=program_id
            )
            yield item


@Route.register
def list_program_seasons(plugin, item_id, program_id):
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
        item.set_callback(
            list_videos,
            item_id=item_id,
            program_id=program_id,
            program_season_number=program_season_number
        )
        yield item


@Route.register
def list_videos(plugin, item_id, program_id, program_season_number):

    resp = urlquick.get(URL_VIDEOS % program_id)
    json_parser = json.loads(resp.text)

    at_least_one_item = False

    if 'episode' in json_parser["videos"]:
        if str(program_season_number) in json_parser["videos"]["episode"]:
            for video_datas in json_parser["videos"]["episode"][str(program_season_number)]:
                at_least_one_item = True
                video_title = video_datas["title"]
                video_duration = int(str(int(video_datas["videoDuration"]) / 1000))
                video_plot = video_datas["description"]
                video_image = video_datas["image"]["src"]
                video_id = video_datas["path"]

                item = Listitem()
                item.label = video_title
                item.art["thumb"] = video_image
                item.art["fanart"] = video_image
                item.info["plot"] = video_plot
                item.info["duration"] = video_duration

                item.context.script(
                    get_video_url,
                    plugin.localize(LABELS['Download']),
                    item_id=item_id,
                    video_id=video_id,
                    video_title=video_title,
                    video_plot=video_plot,
                    video_image=video_image,
                    video_label=LABELS[item_id] + ' - ' + item.label,
                    download_mode=True)

                item.set_callback(
                    get_video_url,
                    item_id=item_id,
                    video_id=video_id,
                    video_title=video_title,
                    video_plot=video_plot,
                    video_image=video_image
                )
                yield item

    if not at_least_one_item:
        plugin.notify(plugin.localize(LABELS['No videos found']), '')
        yield False


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, video_title, video_plot, video_image,
        download_mode=False, video_label=None):

    resp = urlquick.get(URL_STREAM % video_id, max_age=-1)
    json_parser = json.loads(resp.text)

    if 'error' in json_parser:
        if json_parser["error"] is not None:
            if json_parser["error"]["status"] == '403':
                plugin.notify('ERROR', plugin.localize(30713))
            else:
                plugin.notify('ERROR', plugin.localize(30716))
            return False

    if 'drmEnabled' in json_parser["playback"]:
        if json_parser["playback"]["drmEnabled"]:
            Script.notify(
                "TEST",
                plugin.localize(LABELS['drm_notification']),
                Script.NOTIFY_INFO)
            return False
    final_video_url = json_parser["playback"]["streamUrlHls"]

    if download_mode:
        return download.download_video(final_video_url, video_label)

    return final_video_url
