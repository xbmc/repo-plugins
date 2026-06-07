# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import range, str
import xml.etree.ElementTree as ET

from codequick import Listitem, Resolver, Route, utils
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

# TO DO
# YEARS BEFORE 2012 (VIDEO in different format and accessible differently)

URL_SCHEDULE_XML = 'https://fosdem.org/%s/schedule/xml'
# Year

BEGINING_YEAR_XML = 2012
LAST_YEAR_XML = 2023


@Route.register
def website_root(plugin, item_id, **kwargs):
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
