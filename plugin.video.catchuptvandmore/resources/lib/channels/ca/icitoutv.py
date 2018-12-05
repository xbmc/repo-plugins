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

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download


from bs4 import BeautifulSoup as bs

import json
import re
import urlquick


# TO DO
# Add emissions
# Some videos not working
# Some videos protected by drm
# some videos are paid video (add account ?)

URL_ROOT = 'https://services.radio-canada.ca'

URL_REPLAY_BY_DAY = URL_ROOT + '/toutv/presentation/CatchUp?device=web&version=4'

URL_STREAM_REPLAY = URL_ROOT + '/media/validation/v2/?connectionType=hd&output=json&multibitrate=true&deviceType=ipad&appCode=toutv&idMedia=%s'
# VideoId

URL_CLIENT_KEY_JS = 'https://ici.tou.tv/app.js'
# To GET client-key for menu

URL_CLIENT_KEY_VIDEO_JS = URL_ROOT + '/media/player/client/toutv_beta'
# TODO Get client key for


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_days(plugin, item_id)


@Route.register
def list_days(plugin, item_id):
    """
    Build categories listing
    - day 1
    - day 2
    - ...
    """
    resp = urlquick.get(URL_CLIENT_KEY_JS)
    client_key_value = 'client-key %s' % re.compile(
        r'scope\:\{clientId\:\"(.*?)\"').findall(resp.text)[0]
    headers = {
        'Authorization': client_key_value
    }
    resp2 = urlquick.get(URL_REPLAY_BY_DAY, headers=headers)
    json_parser = json.loads(resp2.text)

    for day_datas in json_parser["Lineups"]:
        day_title = day_datas["Title"]
        day_id = day_datas["Name"]

        item = Listitem()
        item.label = day_title
        item.set_callback(
            list_videos,
            item_id=item_id,
            day_id=day_id)
        yield item


@Route.register
def list_videos(plugin, item_id, day_id):

    resp = urlquick.get(URL_CLIENT_KEY_JS)
    client_key_value = 'client-key %s' % re.compile(
        r'scope\:\{clientId\:\"(.*?)\"').findall(resp.text)[0]
    headers = {
        'Authorization': client_key_value
    }
    resp2 = urlquick.get(URL_REPLAY_BY_DAY, headers=headers)
    json_parser = json.loads(resp2.text)

    for day_datas in json_parser["Lineups"]:

        if day_datas["Name"] == day_id:
            for video_datas in day_datas["LineupItems"]:
                if video_datas["IsFree"] is True and video_datas["IsDrm"] is False:
                    video_title = video_datas["ProgramTitle"] + ' ' + video_datas["HeadTitle"]
                    video_plot = video_datas["Description"]
                    video_image = video_datas["ImageUrl"].replace('w_200,h_300', 'w_300,h_200')
                    video_id = video_datas["IdMedia"]

                    item = Listitem()
                    item.label = video_title
                    item.art['thumb'] = video_image
                    item.info['plot'] = video_plot

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
                        video_id=video_id)
                    yield item


@Resolver.register
def get_video_url(
        plugin, item_id, video_id, download_mode=False, video_label=None):

    resp = urlquick.get(URL_CLIENT_KEY_VIDEO_JS)
    client_key_value = 'client-key %s' % re.compile(
        r'prod\"\,clientKey\:\"(.*?)\"').findall(resp.text)[0]
    headers = {
        'Authorization': client_key_value
    }
    resp2 = urlquick.get(URL_STREAM_REPLAY % video_id, headers=headers)
    json_parser = json.loads(resp2.text)
    final_video_url = json_parser["url"]

    if download_mode:
        return download.download_video(final_video_url, video_label)
    return final_video_url
