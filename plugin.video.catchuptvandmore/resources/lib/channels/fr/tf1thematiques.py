# -*- coding: utf-8 -*-
"""
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
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from builtins import str
from builtins import range
from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib import download
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment

import inputstreamhelper
import json
import re
import os
import urlquick
from kodi_six import xbmcgui

# TO DO
# Move WAT to resolver.py (merge with mytf1 code)

URL_ROOT = 'https://www.%s.fr'
# ChannelName

URL_VIDEOS = 'https://www.%s.fr/videos'
# PageId

URL_WAT_BY_ID = 'https://www.wat.tv/embedframe/%s'

URL_VIDEO_STREAM_WAT = 'https://www.wat.tv/get/webhtml/%s'

URL_VIDEO_STREAM = 'https://delivery.tf1.fr/mytf1-wrd/%s?format=%s'
# videoId, format['hls', 'dash']

URL_LICENCE_KEY = 'https://drm-wide.tf1.fr/proxy?id=%s|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=drm-wide.tf1.fr|R{SSM}|'
# videoId

DESIRED_QUALITY = Script.setting['quality']


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(30701)
    if item_id == 'histoire':
        item.set_callback(list_videos, item_id=item_id, page='0')
    else:
        item.set_callback(list_videos, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):

    resp = urlquick.get(URL_VIDEOS % item_id)
    if item_id == 'tvbreizh':
        resp = urlquick.get(URL_VIDEOS % item_id)
    else:
        resp = urlquick.get(URL_VIDEOS % item_id + '?page=%s' % page)
    root = resp.parse("div", attrs={"class": "view-content"})

    for video_datas in root.iterfind("./div"):
        video_title = video_datas.find(".//span[@class='field-content']").find(
            './/a').text
        video_plot = ''
        if video_datas.find(".//div[@class='field-resume']") is not None:
            video_plot = video_datas.find(
                ".//div[@class='field-resume']").text.strip()
        video_image = URL_ROOT % item_id + \
            video_datas.find('.//img').get('src')
        video_url = URL_ROOT % item_id + '/' + \
            video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if 'tvbreizh' not in item_id:
        yield Listitem.next_page(item_id=item_id, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    if len(re.compile(r'www.wat.tv/embedframe/(.*?)[\"\?]').findall(resp.text)) > 0:
        video_id = re.compile(r'www.wat.tv/embedframe/(.*?)[\"\?]').findall(
            resp.text)[0]
        url_wat_embed = URL_WAT_BY_ID % video_id
        wat_embed_html = urlquick.get(
            url_wat_embed,
            headers={'User-Agent': web_utils.get_random_ua()},
            max_age=-1)
        stream_id = re.compile('UVID=(.*?)&').findall(wat_embed_html.text)[0]
        url_json = URL_VIDEO_STREAM_WAT % stream_id
        htlm_json = urlquick.get(url_json,
                                 headers={'User-Agent': web_utils.get_random_ua()},
                                 max_age=-1)
        json_parser = json.loads(htlm_json.text)

        # Check DRM in the m3u8 file
        manifest = urlquick.get(json_parser["hls"],
                                headers={'User-Agent': web_utils.get_random_ua()},
                                max_age=-1)
        if 'drm' in manifest:
            Script.notify("TEST", plugin.localize(30702),
                          Script.NOTIFY_INFO)
            return False

        root = os.path.dirname(json_parser["hls"])

        manifest = urlquick.get(json_parser["hls"].split('&max_bitrate=')[0],
                                headers={'User-Agent': web_utils.get_random_ua()},
                                max_age=-1)

        lines = manifest.text.splitlines()
        final_video_url = ''
        all_datas_videos_quality = []
        all_datas_videos_path = []
        for k in range(0, len(lines) - 1):
            if 'RESOLUTION=' in lines[k]:
                all_datas_videos_quality.append(
                    re.compile(r'RESOLUTION=(.*?)$').findall(lines[k])[0].split(',')[0])
                all_datas_videos_path.append(root + '/' + lines[k + 1])
        if DESIRED_QUALITY == "DIALOG":
            seleted_item = xbmcgui.Dialog().select(
                plugin.localize(30709),
                all_datas_videos_quality)
            final_video_url = all_datas_videos_path[seleted_item]
        elif DESIRED_QUALITY == 'BEST':
            # Last video in the Best
            for k in all_datas_videos_path:
                url = k
            final_video_url = url
        else:
            final_video_url = all_datas_videos_path[0]

        if download_mode:
            return download.download_video(final_video_url)
        return final_video_url

    else:
        video_id = re.compile(r'tf1.fr/embedplayer/(.*?)[\"\?]').findall(
            resp.text)[0]
        video_format = 'hls'
        url_json = URL_VIDEO_STREAM % (video_id, video_format)
        htlm_json = urlquick.get(url_json,
                                 headers={'User-Agent': web_utils.get_random_ua()},
                                 max_age=-1)
        json_parser = json.loads(htlm_json.text)

        if json_parser['code'] >= 400:
            plugin.notify('ERROR', plugin.localize(30716))
            return False

        # Check DRM in the m3u8 file
        manifest = urlquick.get(json_parser["url"],
                                headers={
                                    'User-Agent': web_utils.get_random_ua()},
                                max_age=-1).text
        if 'drm' in manifest:

            if get_kodi_version() < 18:
                xbmcgui.Dialog().ok('Info', plugin.localize(30602))
                return False
            else:
                video_format = 'dash'

        if video_format == 'hls':

            final_video_url = json_parser["url"].replace('2800000', '4000000')
            if download_mode:
                return download.download_video(final_video_url)
            return final_video_url

        else:
            if download_mode:
                xbmcgui.Dialog().ok('Info', plugin.localize(30603))
                return False

            url_json = URL_VIDEO_STREAM % (video_id, video_format)
            htlm_json = urlquick.get(
                url_json,
                headers={'User-Agent': web_utils.get_random_ua()},
                max_age=-1)
            json_parser = json.loads(htlm_json.text)

            is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
            if not is_helper.check_inputstream():
                return False

            item = Listitem()
            item.path = json_parser["url"]
            item.label = get_selected_item_label()
            item.art.update(get_selected_item_art())
            item.info.update(get_selected_item_info())
            item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
            item.property['inputstream.adaptive.manifest_type'] = 'mpd'
            item.property[
                'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
            item.property[
                'inputstream.adaptive.license_key'] = URL_LICENCE_KEY % video_id

            return item
