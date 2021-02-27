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


from resources.lib import web_utils
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

import xml.etree.ElementTree as ET
import htmlement
import re
import urlquick

# TO DO

URL_ROOT = 'https://www1.nyc.gov'

URL_REPLAY = URL_ROOT + '/site/media/shows/shows.page'

URL_API = 'https://a002-vod.nyc.gov/html'

URL_VIDEOS = URL_API + '/nycmedia/pmediaxml.php?pr=%s'
# programId, page

URL_STREAM = URL_API + '/embedplayer.php?id=%s'
# videoId


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
    root = resp.parse("div", attrs={"class": "span6 about-description"})

    list_h2 = root.findall(".//h2")
    list_span_4 = root.findall(".//span[@class='span4']")
    list_span_8 = root.findall(".//span[@class='span8']")

    cpt = 0
    for h2_datas in list_h2:
        program_title = h2_datas.text
        program_image = URL_ROOT + list_span_4[cpt].find('.//img').get('src')
        program_plot = list_span_8[cpt].text
        cpt = cpt + 1
        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.info['plot'] = program_plot
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_title=program_title)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_title, **kwargs):

    resp = urlquick.get(URL_VIDEOS % program_title)

    videos_datas_xml = utils.ensure_native_str(resp.text)
    xml_elements = ET.XML(videos_datas_xml)

    for video in xml_elements.findall(".//video"):

        item = Listitem()
        item.label = video.find(".//show").text

        if video.find(".//description").text:
            item.info['plot'] = utils.strip_tags(
                video.find(".//description").text)
        item.art['thumb'] = item.art['landscape'] = video.find(".//screenshot").text
        video_id = video.find(".//pageurl").text

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(URL_STREAM % video_id)
    list_stream_datas = re.compile('source src="(.*?)"').findall(resp.text)
    stream_url = ''
    for stream_datas in list_stream_datas:
        if 'mp4' in stream_datas:
            stream_url = stream_datas
    if download_mode:
        return download.download_video(stream_url)
    return stream_url
