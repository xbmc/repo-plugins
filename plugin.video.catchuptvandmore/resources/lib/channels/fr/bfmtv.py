# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import division, unicode_literals
from builtins import str
import json
import time

from codequick import Listitem, Resolver, Route, Script
from kodi_six import xbmcgui
import urlquick

from resources.lib import download, resolver_proxy, web_utils
from resources.lib.addon_utils import Quality
from resources.lib.menu_utils import item_post_treatment
from resources.lib.py_utils import old_div


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

# Dailymotion Id get from these pages below
# - https://www.dailymotion.com/BFMTV
LIVE_DAILYMOTION_ID = {
    'bfmtv': 'xgz4t1'
}


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

    if item_id == 'bfmtv' or item_id == 'bfmbusiness':
        stream_infos_url = json_parser['video']['long_url']

        resp2 = urlquick.get(stream_infos_url,
                             headers={'User-Agent': web_utils.get_random_ua()},
                             max_age=-1)

        root = resp2.parse()
        live_datas = root.find(".//div[@class='video_block']")
        data_account = live_datas.get('accountid')
        data_video_id = live_datas.get('videoid')
        data_player = live_datas.get('playerid')
        return resolver_proxy.get_brightcove_video_json(plugin, data_account, data_player, data_video_id, None, download_mode)

    video_streams = json_parser['video']['medias']
    final_video_url = ''
    if DESIRED_QUALITY == Quality['DIALOG']:
        all_datas_videos_quality = []
        all_datas_videos_path = []

        for datas in video_streams:
            all_datas_videos_quality.append("Video Height : " +
                                            str(datas['frame_height']) +
                                            " (Encoding : " +
                                            str(datas['encoding_rate']) + ")")
            all_datas_videos_path.append(datas['video_url'])

        seleted_item = xbmcgui.Dialog().select(
            plugin.localize(30709),
            all_datas_videos_quality)

        if seleted_item > -1:
            final_video_url = all_datas_videos_path[seleted_item]
        else:
            return False

    elif DESIRED_QUALITY == Quality['BEST']:
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


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if item_id == 'bfmtv':
        return resolver_proxy.get_stream_dailymotion(plugin, LIVE_DAILYMOTION_ID[item_id], False)

    if item_id == 'bfmbusiness':
        resp = urlquick.get(URL_LIVE_BFMBUSINESS,
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)
        root = resp.parse()
        live_datas = root.find(".//div[@class='video_block']")
        data_account = live_datas.get('accountid')
        data_video_id = live_datas.get('videoid')
        data_player = live_datas.get('playerid')
        return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                        data_player, data_video_id)
