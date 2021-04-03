# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Route, Resolver, Listitem
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Add Info Date

URL_ROOT = 'http://tele-mag.tv'

URL_EMISSIONS = URL_ROOT + '/emission/emissions'


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_EMISSIONS)
    root = resp.parse("section", attrs={"class": "bloc1 emission_dispo"})

    for program_datas in root.iterfind(".//li"):
        program_title = program_datas.find('.//a').text
        program_url = program_datas.find('.//a').get('href')

        item = Listitem()
        item.label = program_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='bloc1_element_listeVideo']"):
        video_title = video_datas.find('.//a').get('title')
        video_image = URL_ROOT + video_datas.find('.//img').get('src')
        video_url = video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

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
    root = resp.parse()
    stream_url = root.find(".//iframe[@id='main_video']").get('src')
    if 'player.vimeo.com' in stream_url:
        video_id = re.compile(r'player.vimeo.com\/video/(.*?)\?').findall(stream_url)[0]
        return resolver_proxy.get_stream_vimeo(plugin, video_id, download_mode)

    # TODO if new video hoster
    return False


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT)
    root = resp.parse()
    live_datas = root.find('.//iframe')
    resp2 = urlquick.get(live_datas.get('src'))
    live_id = re.compile(r'www.youtube.com\/watch\?v=(.*?)\"').findall(resp2.text)[0]
    return resolver_proxy.get_stream_youtube(plugin, live_id, False)
