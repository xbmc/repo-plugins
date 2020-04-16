# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2019  SylvainCecchetto

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
from resources.lib.menu_utils import item_post_treatment

import json
import re
import urlquick
from kodi_six import xbmcgui

# TO DO
# Add replay

URL_ROOT = 'http://www.lemanbleu.ch'

# Live
URL_LIVE = URL_ROOT + '/fr/Live.html'

URL_INFOMANIAK_LIVE = 'http://livevideo.infomaniak.com/iframe.php?stream=naxoo&name=test&player=%s'
# Player

URL_REPLAY = URL_ROOT + '/replay/video.html'

URL_VIDEOS = URL_ROOT + '/Scripts/Modules/CustomView/List.aspx?idn=9667&name=ReplaySearch&EmissionID=%s&pg=%s'
# program_id

QUALITIES_STREAM = ['sd', 'md', 'hq', 'hd']


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Les Programmes
    - ...
    """
    resp = urlquick.get(URL_REPLAY)
    root = resp.parse("ul", attrs={"id": "itemFilters"})

    for program_datas in root.iterfind(".//li"):
        program_title = program_datas.find('.//a').text
        program_id = re.compile(r'this\,(.*?)\)').findall(
            program_datas.find('.//a').get('onclick'))[0]

        item = Listitem()
        item.label = program_title
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

    for video_datas in root.iterfind(".//li[@class='item']"):
        video_title = video_datas.find('.//h3').text
        video_image = URL_ROOT + video_datas.find('.//img').get('src')
        video_plot = video_datas.find('.//p').text
        video_url = URL_ROOT + video_datas.find('.//a').get('href')
        date_value = video_datas.find(".//span[@class='date']").text.split(
            ' ')[1]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info.date(date_value, '%d.%m.%Y')

        item.set_callback(get_video_url,
                          item_id=item_id,
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
                  **kwargs):

    resp = urlquick.get(video_url, max_age=-1)
    stream_url = re.compile(r'og\:video\" content\=\"(.*?)\"').findall(
        resp.text)[0]

    desired_quality = Script.setting.get_string('quality')
    all_datas_videos_quality = []
    all_datas_videos_path = []
    for quality in QUALITIES_STREAM:
        all_datas_videos_quality.append(quality)
        if quality == 'sd':
            all_datas_videos_path.append(
                stream_url.replace('mp4-231', 'mp4-322'))
        elif quality == 'md':
            all_datas_videos_path.append(
                stream_url.replace('mp4-231', 'mp4-323'))
        elif quality == 'hq':
            all_datas_videos_path.append(
                stream_url.replace('mp4-231', 'mp4-12'))
        else:
            all_datas_videos_path.append(stream_url)

    url = ''
    if desired_quality == "DIALOG":
        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(LABELS['choose_video_quality']),
            all_datas_videos_quality)
        if seleted_item == -1:
            url = ''
        url = all_datas_videos_path[seleted_item]
    elif desired_quality == "BEST":
        url_best = ''
        for data_video in all_datas_videos_path:
            url_best = data_video
        url = url_best
    else:
        url = all_datas_videos_path[0]

    if download_mode:
        return download.download_video(url)
    return url


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    player_id = re.compile(r'\&player\=(.*?)\"').findall(resp.text)[0]
    session_urlquick = urlquick.Session(allow_redirects=False)
    resp2 = session_urlquick.get(URL_INFOMANIAK_LIVE % player_id)
    location_url = resp2.headers['Location']
    resp3 = urlquick.get(location_url.replace(
        'infomaniak.com/', 'infomaniak.com/playerConfig.php'),
        max_age=-1)
    json_parser = json.loads(resp3.text)
    stream_url = ''
    for stram_datas in json_parser['data']['integrations']:
        if 'hls' in stram_datas['type']:
            stream_url = stram_datas['url']
    return stream_url
