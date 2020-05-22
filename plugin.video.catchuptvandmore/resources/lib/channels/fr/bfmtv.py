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
from __future__ import division

from builtins import str
import sys
from resources.lib.codequick import Route, Resolver, Listitem, utils, Script

from resources.lib.labels import LABELS
from resources.lib import web_utils
from resources.lib import resolver_proxy
from resources.lib import download
from resources.lib.menu_utils import item_post_treatment
from resources.lib.py_utils import old_div

import json
import time
import re
from resources.lib import urlquick
from kodi_six import xbmcgui

# TO DO

# BFMTV, RMC, ONENET, etc ...
URL_TOKEN = 'http://api.nextradiotv.com/%s-applications/'
# channel

URL_MENU = 'http://www.bfmtv.com/static/static-mobile/bfmtv/' \
           'ios-smartphone/v0/configuration.json'

URL_REPLAY = 'http://api.nextradiotv.com/%s-applications/%s/' \
             'getPage?pagename=replay'
# channel, token

URL_SHOW = 'http://api.nextradiotv.com/%s-applications/%s/' \
           'getVideosList?category=%s&count=100&page=%s'
# channel, token, category, page_number

URL_VIDEO = 'http://api.nextradiotv.com/%s-applications/%s/' \
            'getVideo?idVideo=%s'
# channel, token, video_id

# URL Live
# Channel BFMTV
URL_LIVE_BFMTV = 'http://www.bfmtv.com/mediaplayer/live-video/'

# Channel BFM Business
URL_LIVE_BFMBUSINESS = 'http://bfmbusiness.bfmtv.com/mediaplayer/live-video/'

DESIRED_QUALITY = Script.setting['quality']


def replay_entry(plugin, item_id, **kwargs):
    """
    First executed function after replay_bridge
    """
    return list_programs(plugin, item_id)


def get_token(item_id):
    """Get session token"""
    resp = urlquick.get(URL_TOKEN % item_id)
    json_parser = json.loads(resp.text)
    return json_parser['session']['token']


@Route.register
def list_programs(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_REPLAY % (item_id, get_token(item_id)))
    json_parser = json.loads(resp.text)
    json_parser = json_parser['page']['contents'][0]
    json_parser = json_parser['elements'][0]['items']

    for list_program_datas in json_parser:
        program_title = list_program_datas['title']
        program_image = list_program_datas['image_url']
        program_category = list_program_datas['categories']

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_category=program_category,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_category, page, **kwargs):

    resp = urlquick.get(URL_SHOW %
                        (item_id, get_token(item_id), program_category, page))
    json_parser = json.loads(resp.text)

    for video_datas in json_parser['videos']:
        video_id = video_datas['video']
        video_id_ext = video_datas['id_ext']
        category = video_datas['category']
        title = video_datas['title']
        description = video_datas['description']
        # begin_date = video['begin_date']  # 1486725600,
        image = video_datas['image']
        duration = old_div(video_datas['video_duration_ms'], 1000)

        value_date = time.strftime('%d %m %Y',
                                   time.localtime(video_datas["begin_date"]))
        date = str(value_date).split(' ')
        day = date[0]
        mounth = date[1]
        year = date[2]

        date = '.'.join((day, mounth, year))
        aired = '-'.join((year, mounth, day))

        item = Listitem()
        item.label = title
        item.art['thumb'] = item.art['landscape'] = image
        item.info['duration'] = duration
        item.info['plot'] = description
        item.info['genre'] = category
        item.info['aired'] = aired
        item.info['year'] = year
        item.info['date'] = date

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id,
                          video_id_ext=video_id_ext)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             program_category=program_category,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  video_id_ext,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(URL_VIDEO % (item_id, get_token(item_id), video_id))
    json_parser = json.loads(resp.text)

    video_streams = json_parser['video']['medias']
    final_video_url = ''
    if DESIRED_QUALITY == "DIALOG":
        all_datas_videos_quality = []
        all_datas_videos_path = []

        for datas in video_streams:
            all_datas_videos_quality.append("Video Height : " +
                                            str(datas['frame_height']) +
                                            " (Encoding : " +
                                            str(datas['encoding_rate']) + ")")
            all_datas_videos_path.append(datas['video_url'])

        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(LABELS['choose_video_quality']),
            all_datas_videos_quality)

        if seleted_item > -1:
            final_video_url = all_datas_videos_path[seleted_item]
        else:
            return False

    elif DESIRED_QUALITY == 'BEST':
        # GET LAST NODE (VIDEO BEST QUALITY)
        url_best_quality = ''
        for datas in video_streams:
            url_best_quality = datas['video_url']
        final_video_url = url_best_quality
    else:
        # DEFAULT VIDEO
        final_video_url = json_parser['video']['video_url']

    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url


def live_entry(plugin, item_id, **kwargs):
    return get_live_url(plugin, item_id, item_id.upper())


@Resolver.register
def get_live_url(plugin, item_id, video_id, **kwargs):

    if item_id == 'bfmtv':
        resp = urlquick.get(URL_LIVE_BFMTV,
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)
    elif item_id == 'bfmbusiness':
        resp = urlquick.get(URL_LIVE_BFMBUSINESS,
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)

    root = resp.parse()
    live_datas = root.find(".//div[@class='next-player']")
    data_account = live_datas.get('data-account')
    data_video_id = live_datas.get('data-video-id')
    data_player = live_datas.get('data-player')
    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id)
