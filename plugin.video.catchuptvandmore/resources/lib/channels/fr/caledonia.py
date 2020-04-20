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
from resources.lib.menu_utils import item_post_treatment

import re
import urlquick

# TO DO
# Add Next Button
# Readd date without beautiful soup

URL_ROOT = 'https://www.caledonia.nc'


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
    resp = urlquick.get(URL_ROOT)
    root = resp.parse()

    for program_datas in root.iterfind(".//a"):
        if program_datas.get('href'):
            if 'emission/' in program_datas.get('href'):
                program_title = program_datas.text
                if URL_ROOT in program_datas.get('href'):
                    program_url = program_datas.get('href')
                else:
                    program_url = URL_ROOT + program_datas.get('href')

                item = Listitem()
                item.label = program_title
                item.set_callback(list_videos,
                                  item_id=item_id,
                                  program_url=program_url)
                item_post_treatment(item)
                yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='block-yt-playlist col-lg-4 col-12 mb-4']"):
        video_title = video_datas.find('.//h3').text.strip()
        video_image = video_datas.find(
            ".//div[@class='bg-img rounded d-flex align-items-center justify-content-center position-relative']"
        ).get('style')
        video_image = re.compile(r'url\(\'(.*?)\'').findall(video_image)[0]
        video_url = 'https:' + video_datas.find('.//a').get('href')
        # date_value = utils.strip_tags(video_datas.find(".//div[@class='wrap-infos mt-3']")).text

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        # try:
        #     item.info.date(date_value, '%d/%m/%Y')
        # except:
        #     pass

        # try:
        #     item.info.date(date_value, '%d-%m-%Y')
        # except:
        #     pass

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

    resp = urlquick.get(video_url)
    video_id = re.compile(r'youtube\.com\/embed\/(.*)\"').findall(resp.text)[0]
    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)
