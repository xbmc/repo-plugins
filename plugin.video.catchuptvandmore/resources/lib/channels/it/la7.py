# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

import inputstreamhelper
from codequick import Listitem, Resolver, Route
from kodi_six import xbmcgui
import urlquick

from resources.lib import download
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment


# TO DO

URL_ROOT = 'http://www.la7.it'

URL_DAYS = URL_ROOT + '/rivedila7/0/%s'
# Channels (upper)

# Live
URL_LIVE = URL_ROOT + '/dirette-tv'

URL_LICENCE_KEY = 'https://la7.prod.conax.cloud/widevine/license|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&preauthorization=%s|R{SSM}|'


@Route.register
def list_days(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_DAYS % item_id.upper())
    root = resp.parse(
        "div", attrs={
            "class": "wrapper-nav wrapper-nav-%s" % item_id
        })

    for day_datas in root.find(".//div[@class='content']").iterfind(".//a"):
        day_title = day_datas.find(".//div[@class='giorno-text']").text.strip(
        ) + ' - ' + day_datas.find(".//div[@class='giorno-numero']").text.strip(
        ) + ' - ' + day_datas.find(
            ".//div[@class='giorno-mese']").text.strip()
        day_url = URL_ROOT + day_datas.get('href')

        item = Listitem()
        item.label = day_title
        item.set_callback(list_videos, item_id=item_id, day_url=day_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, day_url, **kwargs):

    resp = urlquick.get(day_url)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='item item--guida-tv']"):
        if video_datas.find(".//div[@class='label-no-replica']") is None:
            video_title = video_datas.find(".//h2").text.strip()
            video_image = 'https:' + video_datas.find(
                ".//div[@class='bg-img lozad']").get('data-background-image')
            video_plot = ''
            if video_datas.find(".//div[@class='occhiello']").text is not None:
                video_plot = video_datas.find(
                    ".//div[@class='occhiello']").text.strip()
            video_url = video_datas.find(".//a").get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.info['plot'] = video_plot

            item.set_callback(
                get_video_url,
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
    json_value = re.compile(r'src\: \{(.*?)\}\,').findall(resp.text)[0]
    json_parser = json.loads('{' + json_value + '}')
    if download_mode:
        return download.download_video(json_parser["m3u8"].replace(
            'http://la7-vh.akamaihd.net/i/,/content',
            'https://vodpkg.iltrovatore.it/local/hls/,/content').replace(
                'csmil', 'urlset'))
    return json_parser["m3u8"].replace(
        'http://la7-vh.akamaihd.net/i/,/content',
        'https://vodpkg.iltrovatore.it/local/hls/,/content').replace(
            'csmil', 'urlset')


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    resp = urlquick.get(URL_LIVE, max_age=-1)
    live_url = re.compile(
        r'\'(.*?)mpd').findall(resp.text)[0] + 'mpd'

    preauthorization_url = re.compile(
        r'preTokenUrl = \"(.*?)\"').findall(resp.text)[0]
    resp2 = urlquick.get(preauthorization_url, max_age=-1)
    json_parser = json.loads(resp2.text)

    item = Listitem()
    item.path = live_url
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property[
        'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property[
        'inputstream.adaptive.license_key'] = URL_LICENCE_KEY % json_parser["preAuthToken"]
    return item
