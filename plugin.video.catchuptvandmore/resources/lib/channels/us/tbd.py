# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'https://tbd.com'

URL_REPLAY = URL_ROOT + '/shows'

URL_LIVE = URL_ROOT + '/live'


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

    for program_datas in root.iterfind(".//a[@class='show-item']"):
        program_title = program_datas.get('href').replace('/shows/',
                                                          '').replace(
                                                              '-', ' ')
        program_image = program_datas.find('.//img').get('src')
        program_url = URL_ROOT + program_datas.get('href')

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

    for video_datas in root.iterfind(".//div[@class='event-item episode']"):
        if video_datas.find(".//p[@class='content-label-secondary']/span") is not None:
            video_title = video_datas.find('.//h3').text + video_datas.find(
                ".//p[@class='content-label-secondary']/span").text
        else:
            video_title = video_datas.find('.//h3').text
        video_image = ''
        for image_datas in video_datas.findall('.//img'):
            if 'jpg' in image_datas.get('src'):
                video_image = image_datas.get('src')
        video_plot = ''
        if video_datas.find(".//p[@class='synopsis']") is not None:
            video_plot = video_datas.find(".//p[@class='synopsis']").text
        video_url = URL_ROOT + video_datas.find('.//a').get('href')

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

    resp = urlquick.get(video_url)
    final_video_url = re.compile(r'file\': "(.*?)"').findall(resp.text)[0]

    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE)
    return re.compile(r'file\': "(.*?)"').findall(resp.text)[0]
