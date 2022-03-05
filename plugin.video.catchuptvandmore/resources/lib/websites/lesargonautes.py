# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download
from resources.lib.menu_utils import item_post_treatment

# TODO fix module, 404 error on url root

URL_ROOT = 'http://lesargonautes.telequebec.tv'

URL_VIDEOS = URL_ROOT + '/Episodes'

URL_STREAM_DATAS = 'https://mnmedias.api.telequebec.tv/api/v2/media/mediaUid/%s'

URL_STREAM = 'https://mnmedias.api.telequebec.tv/m3u8/%s.m3u8'
# VideoId


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    resp = urlquick.get(URL_VIDEOS)
    list_seasons_datas = re.compile(r'li path\=\"(.*?)\"').findall(resp.text)

    for season_datas in list_seasons_datas:
        season_title = season_datas

        item = Listitem()
        item.label = season_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          season_title=season_title)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, season_title, **kwargs):

    resp = urlquick.get(URL_VIDEOS)
    root = resp.parse("li", attrs={"path": season_title})

    for video_datas in root.iterfind(".//li[@class='episode']"):
        video_title = video_datas.find(".//div[@class='title']").text.strip(
        ) + ' - Episode ' + video_datas.find(
            ".//span[@path='Number']").text.strip()
        video_image = video_datas.find(".//img[@class='screen']").get('src')
        video_plot = video_datas.find(".//div[@class='summary']").text.strip()
        video_id = video_datas.find(".//input[@path='MediaUid']").get('value')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):
    """Get video URL and start video player"""

    if video_id == '':
        plugin.notify('ERROR', plugin.localize(30716))
        return False

    resp = urlquick.get(URL_STREAM_DATAS % video_id, verify=False)
    json_parser = json.loads(resp.text)

    final_video_url = URL_STREAM % json_parser['media']['mediaId']

    if download_mode:
        return download.download_video(final_video_url)
    return final_video_url
