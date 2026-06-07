# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import web_utils, resolver_proxy, download
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'https://www.lachainemeteo.com'
URL_VIDEOS = URL_ROOT + '/videos-meteo/videos-la-chaine-meteo'
URL_JWPLAYER = 'https://cdn.jwplayer.com/v2/media/%s'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_VIDEOS, GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='viewVideosSeries']"):
        program_title = program_datas.find(
            ".//div[@class='title']").text.strip() + ' ' + program_datas.find(
                ".//div[@class='title']").find('.//strong').text.strip()

        item = Listitem()
        item.label = program_title
        item.set_callback(list_videos, program_title_value=program_title, root=root)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, program_title_value, root, **kwargs):

    for program_datas in root.iterfind(".//div[@class='viewVideosSeries']"):
        program_title = program_datas.find(
            ".//div[@class='title']").text.strip() + ' ' + program_datas.find(
                ".//div[@class='title']").find('.//strong').text.strip()

        if program_title == program_title_value:
            list_videos_datas = program_datas.findall('.//a')
            for video_datas in list_videos_datas:
                video_title = video_datas.find(".//div[@class='txt']").text
                video_image = video_datas.find('.//img').get('data-src')
                video_url = video_datas.get('href')
                item = Listitem()
                item.label = video_title
                item.art['thumb'] = item.art['landscape'] = video_image
                item.set_callback(get_video_url, video_url=video_url)
                item_post_treatment(item, is_playable=True, is_downloadable=True)
                yield item


@Resolver.register
def get_video_url(plugin, video_url, download_mode=False, **kwargs):

    resp = urlquick.get(video_url)
    data_video = resp.parse().find('.//video').get('data-video-id')

    resp = urlquick.get(URL_JWPLAYER % data_video, GENERIC_HEADERS, max_age=-1)
    video_url = json.loads(resp.text)['playlist'][0]['sources'][0]['file']

    if download_mode:
        return download.download_video(video_url)

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url)
