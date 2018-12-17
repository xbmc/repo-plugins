# -*- coding: utf-8 -*-
'''
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
'''
# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

import re
from bs4 import BeautifulSoup as bs

from codequick import Route, Resolver, Listitem, utils
import urlquick
import json

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import download


# TO DO
# Fix Download Mode

URL_ROOT = 'http://lesargonautes.telequebec.tv'

URL_VIDEOS = URL_ROOT + '/Episodes'

URL_STREAM_DATAS = 'https://mnmedias.api.telequebec.tv/api/v2/media/mediaUid/%s'

URL_STREAM = 'https://mnmedias.api.telequebec.tv/m3u8/%s.m3u8'
# VideoId

def website_entry(plugin, item_id):
    """
    First executed function after website_bridge
    """
    return root(plugin, item_id)


def root(plugin, item_id):
    """Add modes in the listing"""
    resp = urlquick.get(URL_VIDEOS)
    list_seasons_datas = re.compile(
        r'li path\=\"(.*?)\"').findall(resp.text)

    for season_datas in list_seasons_datas:
        season_title = season_datas

        item = Listitem()
        item.label = season_title
        item.set_callback(
            list_videos,
            item_id=item_id,
            season_title=season_title)
        yield item


@Route.register
def list_videos(plugin, item_id, season_title):

    resp = urlquick.get(URL_VIDEOS)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find(
        'li', attrs={'path': season_title}).find_all(
            'li', class_='episode')
    
    for video_datas in list_videos_datas:
        video_title = video_datas.find(
            'div', class_='title').text.strip() + ' (' + \
                video_datas.find(
                    'div', class_='header').text.strip() + ')'
        video_image = video_datas.find('img', class_='screen').get('src')
        video_plot = video_datas.find('div', class_='summary').text.strip()
        video_id = video_datas.find(
            'input', attrs={'path': 'MediaUid'}).get('value')

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
    """Get video URL and start video player"""

    if video_id == '':
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    resp = urlquick.get(URL_STREAM_DATAS % video_id, verify=False)
    json_parser = json.loads(resp.text)

    final_video_url = URL_STREAM % json_parser['media']['mediaId']

    if download_mode:
        return download.download_video(final_video_url, video_label)
    return final_video_url
