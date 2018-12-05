# -*- coding: utf-8 -*-
"""
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
# Token (live) maybe more work todo
# Fix Download Mode

URL_ROOT = 'https://www.telemb.be'

URL_PROGRAMS = URL_ROOT + '/emissions'

URL_LIVE = URL_ROOT + '/direct'

URL_STREAM_LIVE = 'https://telemb.fcst.tv/player/embed/%s'
# LiveId


def replay_entry(plugin, item_id):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id):

    resp = resp = urlquick.get(URL_PROGRAMS)
    root_soup = bs(resp.text, 'html.parser')
    list_programs_datas = root_soup.find_all('a')

    for program_datas in list_programs_datas:

        if program_datas.get('href'):
            if 'emission/' in program_datas.get('href'):
                program_title = program_datas.find('div').text
                program_image = 'https:' + program_datas.find('img').get('src')
                program_url = URL_ROOT + program_datas.get('href')

                item = Listitem()
                item.label = program_title
                item.art['thumb'] = program_image
                item.set_callback(
                    list_videos,
                    item_id=item_id,
                    program_url=program_url,
                    page='0')
                yield item


@Route.register
def list_videos(plugin, item_id, program_url, page):

    resp = urlquick.get(program_url + '?page=%s' % page)
    root_soup = bs(resp.text, 'html.parser')
    list_videos_datas = root_soup.find_all('div', class_='video-block')

    for video_datas in list_videos_datas:
        video_title = ''
        video_image = ''
        if video_datas.find("img"):
            video_image = 'https:' + video_datas.find("img").get('src')
        video_url = ''
        list_a_node_datas = video_datas.find_all('a')
        for a_node_datas in list_a_node_datas:
            if a_node_datas.get('href'):
                video_title = a_node_datas.text
                video_url = URL_ROOT + a_node_datas.get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = video_image

        item.context.script(
            get_video_url,
            plugin.localize(LABELS['Download']),
            item_id=item_id,
            video_url=video_url,
            video_label=LABELS[item_id] + ' - ' + item.label,
            download_mode=True)

        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_url=video_url)
        yield item

    yield Listitem.next_page(
        item_id=item_id,
        program_url=program_url,
        page=str(int(page) + 1))


@Resolver.register
def get_video_url(
        plugin, item_id, video_url, download_mode=False, video_label=None):

    resp = urlquick.get(video_url, max_age=-1)
    root_soup = bs(resp.text, 'html.parser')
    video_id_url = root_soup.find_all('iframe')[1].get('src')

    resp2 = urlquick.get(video_id_url, max_age=-1)
    final_video_url = 'https://tvl-vod.l3.freecaster.net' + re.compile(
        r'freecaster\.net(.*?)\"').findall(resp2.text)[0] + '/master.m3u8'
    if download_mode:
        return download.download_video(final_video_url, video_label)
    return final_video_url


def live_entry(plugin, item_id, item_dict):
    return get_live_url(plugin, item_id, item_id.upper(), item_dict)


@Resolver.register
def get_live_url(plugin, item_id, video_id, item_dict):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    live_id = re.compile(
         r'telemb.fcst.tv/player/embed\/(.*?)[\?\"]').findall(resp.text)[0]
    resp2 = urlquick.get(URL_STREAM_LIVE % live_id, max_age=-1)
    return 'https://tvl-live.l3.freecaster.net' + re.compile(
        r'freecaster\.net(.*?)\"').findall(resp2.text)[0]
