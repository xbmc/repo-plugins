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
from resources.lib import resolver_proxy
from resources.lib.listitem_utils import item_post_treatment, item2dict

import re
import urlquick

# TO DO

URL_ROOT = 'http://www.onzeo.fr/'


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(
        URL_ROOT,
        headers={
            'User-Agent':
            web_utils.get_random_ua,
            'Host':
            'www.onzeo.fr',
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        })
    root = resp.parse()

    for program_datas in root.iterfind(".//section[@class='une2']"):
        if program_datas.get('style') is None:
            program_title = program_datas.find(
                ".//h2[@class='titreBloc']").text
            if program_datas.find(".//div[@class='zoneb']") is not None:
                program_id = program_datas.find(".//div[@class='zoneb']").get(
                    'id')
            else:
                program_id = program_datas.find(
                    ".//div[@class='zoneb flickity-enabled is-draggable']"
                ).get('id')

            item = Listitem()
            item.label = program_title
            item.set_callback(list_videos,
                              item_id=item_id,
                              program_id=program_id)
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, program_id, **kwargs):

    resp = urlquick.get(URL_ROOT)
    root = resp.parse()

    list_programs_datas = root.findall(".//div[@class='zoneb']")
    list_programs_datas += root.findall(
        ".//div[@class='zoneb flickity-enabled is-draggable']")

    for program_datas in list_programs_datas:
        if program_id == program_datas.get('id'):
            list_videos_datas = program_datas.findall(
                ".//div[@class='cell item']")
            for video_datas in list_videos_datas:
                video_title = video_datas.find('.//h2').text
                video_image = video_datas.find('.//img').get('src')
                video_id = video_datas.get('iddm')

                item = Listitem()
                item.label = video_title
                item.art['thumb'] = video_image

                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_label=LABELS[item_id] + ' - ' +
                                  item.label,
                                  video_id=video_id)
                item_post_treatment(item,
                                    is_playable=True,
                                    is_downloadable=True)
                yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  video_label=None,
                  **kwargs):
    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode, video_label)
