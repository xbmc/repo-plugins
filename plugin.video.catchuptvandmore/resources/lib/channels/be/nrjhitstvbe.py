# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib.menu_utils import item_post_treatment

# TO DO

URL_ROOT = 'https://www.nrj.be'

URL_LIVE = URL_ROOT + '/tv'

URL_STREAM = 'https://services.brid.tv/services/get/video/%s/%s.json'

URL_VIDEOS = URL_ROOT + '/replay/videos'


@Route.register
def list_videos(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_VIDEOS)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='col-nrj-card']"):
        if video_datas.find(".//a") is not None:
            video_title = video_datas.find(".//div[@class='nrj-card__text']").text
            video_image_datas = video_datas.find(".//div[@class='nrj-card__pict']").get('style')
            video_image = re.compile(
                r'url\((.*?)\)').findall(video_image_datas)[0]
            video_url = URL_ROOT + video_datas.find(".//a").get('href')

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

    resp = urlquick.get(video_url, max_age=-1)
    data_player = re.compile(r'data-video-player-id\=\"(.*?)\"').findall(
        resp.text)[0]
    data_video_id = re.compile(r'data-video-id\=\"(.*?)\"').findall(
        resp.text)[0]

    resp2 = urlquick.get(
        URL_STREAM % (data_player, data_video_id), max_age=-1)
    json_parser2 = json.loads(resp2.text)
    return 'https:' + json_parser2["Video"][0]["source"]["hd"]


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, max_age=-1)
    data_player = re.compile(r'data-video-player-id\=\"(.*?)\"').findall(
        resp.text)[0]
    data_video_id = re.compile(r'data-video-id\=\"(.*?)\"').findall(
        resp.text)[0]

    resp2 = urlquick.get(
        URL_STREAM % (data_player, data_video_id), max_age=-1)
    json_parser2 = json.loads(resp2.text)
    return json_parser2["Video"][0]["source"]["sd"]
