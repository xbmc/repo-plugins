# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'http://www.ouatch.tv'

URL_EMISSIONS = URL_ROOT + '/emissions'

# # Dailymotion Id get from these pages below
# # - https://www.dailymotion.com/ouatchtv
LIVE_DAILYMOTION_ID = {'ouatchtv': 'xuw47s'}


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_EMISSIONS)
    root = resp.parse()

    for program_datas in root.iterfind(".//a[@class='vignepi onglet_emi']"):
        program_title = program_datas.get('title')
        program_image = program_datas.find('.//img').get('src')
        program_url = program_datas.get('href')

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()

    for video_datas in root.iterfind(".//a[@class='mix1 vignepi']"):
        video_title = video_datas.findall('.//p')[0].text
        video_plot = video_datas.findall('.//p')[1].text
        video_image = URL_ROOT + video_datas.findall('.//img')[0].get('src')
        video_url = video_datas.get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

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

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    video_id = re.compile(r'video: "(.*?)"').findall(resp.text)[0]
    return resolver_proxy.get_stream_dailymotion(plugin, video_id,
                                                 download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    return resolver_proxy.get_stream_dailymotion(plugin,
                                                 LIVE_DAILYMOTION_ID[item_id],
                                                 False)
