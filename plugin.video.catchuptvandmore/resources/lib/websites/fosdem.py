# -*- coding: utf-8 -*-
'''
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto
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
'''
# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from builtins import str
from builtins import range
from codequick import Route, Resolver, Listitem, utils
import urlquick
import xml.etree.ElementTree as ET

from resources.lib.labels import LABELS
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

# TO DO
# YEARS BEFORE 2012 (VIDEO in different format and accessible differently)

URL_SCHEDULE_XML = 'https://fosdem.org/%s/schedule/xml'
# Year

BEGINING_YEAR_XML = 2012
LAST_YEAR_XML = 2020


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    for i in range(BEGINING_YEAR_XML, LAST_YEAR_XML + 1):
        item = Listitem()
        year_label = str(i)
        item.label = year_label
        category_url = URL_SCHEDULE_XML % year_label

        item.set_callback(list_videos,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, **kwargs):
    """Build videos listing"""
    videos_datas_xml = urlquick.get(category_url).text
    videos_datas_xml = utils.ensure_native_str(videos_datas_xml)
    xml_elements = ET.XML(videos_datas_xml)

    for video in xml_elements.findall(".//event"):

        video_links = video.findall(".//link")
        video_url = ''
        for video_link in video_links:
            if 'Video' in video_link.text:
                video_url = video_link.get('href')

        if video_url != '':
            item = Listitem()
            item.label = video.find("title").text

            if video.find("abstract").text:
                item.info['plot'] = utils.strip_tags(
                    video.find("abstract").text)

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
    """Get video URL and start video player"""
    if download_mode:
        return download.download_video(video_url)
    return video_url
