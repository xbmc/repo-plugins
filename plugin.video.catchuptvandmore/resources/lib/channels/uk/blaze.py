# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
import json

# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import web_utils, resolver_proxy
from resources.lib.menu_utils import item_post_treatment

URL_API = 'https://watch.blaze.tv'
# Live
URL_LIVE = URL_API + '/live/%s'
# Catchup
URL_REPLAY = URL_API + '/series'
URL_STREAM = '%s/streams/api/%s/stream/%s'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


def getPlaylist(mode, stream, streamKey, streamUvid):
    stream = URL_STREAM % (stream, mode, streamUvid)
    licParams = {
        'autoplay': '1',
        'gpdr': '1',
        'gpdr_consent': 'undefined',
        'platform': 'chrome',
        'key': streamKey
    }

    resp = urlquick.get(stream, headers=GENERIC_HEADERS, params=licParams, max_age=-1)
    video_url = json.loads(resp.text)["response"]["stream"].split('?', 1)[0]
    return video_url


@Route.register
def list_categories(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_REPLAY, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='col-auto layout-carousel-column']"):

        video_title = ''
        video_image = None
        video_sub_title = ''
        description = ''
        for video_image_data in video_datas.iterfind('.//img'):
            if video_image_data.get('alt') != 'Logo':
                video_title = video_image_data.get('alt')
                video_image = video_image_data.get('src')
        xdata = video_datas.find('.//a').get('x-data')
        video_id = re.compile(r"href\:\ \'(.*?)\'").findall(xdata)[0]

        episodes_span = video_datas.find(".//span[@data-content-type='episodes']")
        if episodes_span is not None:
            sub_title_data = episodes_span.find('span')
            if sub_title_data is not None:
                # strip new line and HTML indents, and combine to one line.
                video_sub_title = ' '.join(t.strip() for t in sub_title_data.text.strip().split('\n'))

        overlay_data = video_datas.find(".//p[@class='overlay-text mb-0']")
        if overlay_data is not None:
            # strip new line and HTML indents, and combine to one line.
            description = ' '.join(t.strip() for t in overlay_data.text.strip().split('\n'))

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = '\n\n'.join(t for t in (description, video_sub_title) if t)
        item.set_callback(list_videos,
                          item_id=item_id,
                          video_id=video_id,
                          video_image=video_image)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Route.register
def list_videos(plugin, item_id, video_id, **kwargs):

    resp = urlquick.get(video_id, headers=GENERIC_HEADERS, max_age=-1)
    streams = re.search('"streams":"(.+?)"', resp.text)
    stream = streams.group(1).replace("\\", "")
    root = resp.parse()

    for video_active in root.iterfind(".//div[@id='seasonsContent']"):
        for video_datas in video_active.iterfind(".//div[@class='row py-5']"):

            video_title = ''
            video_image = None
            if video_datas.find('.//img') is not None:
                video_title = video_datas.find('.//img').get('alt')
                video_image = video_datas.find('.//img').get('src')

            epno = ''
            for epouter in video_datas.iterfind(".//span[@data-content-type='season-episode']"):
                epno = epouter.find(".//span").text.strip()

            seconds = ''
            for louter in video_datas.iterfind(".//span[@data-content-type='duration']"):
                duration = louter.find(".//span").text.strip()
                duration_datas = duration.replace('h', '').replace('m', '').split(" ")
                if len(duration_datas) > 1:
                    seconds = 3600 * int(duration_datas[0]) + 60 * int(duration_datas[1])
                else:
                    seconds = 60 * int(duration_datas[0])

            plot = ''
            for info in video_datas.iterfind(".//p[@class='text-secondary mb-0']"):
                plot = info.text.strip()
            for drm_details in video_datas.iterfind(".//span[@data-env='production']"):
                streamKey = drm_details.get('data-key')
                streamUvid = drm_details.get('data-uvid')

            item = Listitem()
            item.label = video_title
            item.info['plot'] = '\n'.join((epno, plot))
            item.info['duration'] = seconds
            item.art['thumb'] = item.art['landscape'] = video_image

            item.set_callback(get_video_url, item_id=item_id,
                              streamKey=streamKey, streamUvid=streamUvid,
                              stream=stream)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item


@Resolver.register
def get_video_url(plugin, item_id, streamKey, streamUvid,
                  stream, **kwargs):
    video_url = getPlaylist("replay", stream, streamKey, streamUvid)
    return resolver_proxy.get_stream_with_quality(plugin, video_url)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    if item_id not in ["1227", "1228", "1229", "1235", "1236"]:
        item_id = "553"
    resp = urlquick.get(URL_LIVE, headers=GENERIC_HEADERS, max_age=-1)
    streams = re.search('"streams":"(.+?)"', resp.text)
    stream = str(streams.group(1)).replace("\\", "")
    streamKey = re.findall('data-key="(.+?)"', resp.text)
    streamUvid = re.findall('data-uvid="(.+?)"', resp.text)
    for (k, u) in zip(streamKey, streamUvid):
        if str(u) == item_id:
            uvid = str(u)
            key = str(k)
    video_url = getPlaylist("live", stream, key, uvid)
    return resolver_proxy.get_stream_with_quality(plugin, video_url)
