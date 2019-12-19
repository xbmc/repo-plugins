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

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download
from resources.lib.listitem_utils import item_post_treatment, item2dict

import htmlement
import re
import urlquick

# TO DO

URL_ROOT = 'https://a002-vod.nyc.gov'

URL_REPLAY = URL_ROOT + '/html/programs.php'

URL_VIDEOS = URL_ROOT + '/html/pagination/videos.php?id=%s&pn=%s'
# programId, page

URL_STREAM = URL_ROOT + '/html/%s'
# videoId


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_REPLAY)
    root = resp.parse()

    for program_datas in root.iterfind(
            ".//div[@style='float:left; width:490px; height:180px']"):
        program_title = program_datas.findall('.//a')[1].text
        program_image = program_datas.find('.//img').get('src')
        program_id = program_datas.findall('.//a')[1].get('href').split(
            'videos.php?id=')[1]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_id=program_id,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_id, page, **kwargs):

    resp = urlquick.get(URL_VIDEOS % (program_id, page))
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@style='float:left; width:160px; height:220px; padding-left:4px; padding-right:31px']"
    ):

        video_title = video_datas.find(
            './/b/a').text + ' - ' + video_datas.findall(
                './/br')[1].tail.strip()
        video_image = video_datas.find(".//img[@class='thumb']").get('src')
        video_url = URL_STREAM % video_datas.find('.//a').get('href').replace(
            '../', '')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_label=LABELS[item_id] + ' - ' + item.label,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             program_id=program_id,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  video_label=None,
                  **kwargs):

    resp = urlquick.get(video_url)
    list_stream_datas = re.compile('source src="(.*?)"').findall(resp.text)
    stream_url = ''
    for stream_datas in list_stream_datas:
        if 'mp4' in stream_datas:
            stream_url = stream_datas
    if download_mode:
        return download.download_video(stream_url, video_label)
    return stream_url
