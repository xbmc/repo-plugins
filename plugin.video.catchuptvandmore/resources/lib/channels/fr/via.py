# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json
import re

import inputstreamhelper
from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import download, resolver_proxy, web_utils
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment


# TODO Add Replay

URL_ROOT = 'https://%s.tv'

URL_LIVE = URL_ROOT + '/direct-tv/'

URL_LIVE_VIAMOSELLE = URL_ROOT + '/direct/'

URL_ROOT_VIAVOSGES = 'https://www.viavosges.tv'

URL_LIVE_VIAVOSGES = URL_ROOT_VIAVOSGES + '/Direct.html'

URL_STREAM = 'https://player.myvideoplace.tv/ajax_actions.php'

URL_STREAM_INFOMANIAK = 'https://livevideo.infomaniak.com/player_config/%s.json'
# player_id


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    if item_id == 'via93':
        category_title = plugin.localize(30701)
        category_url = URL_ROOT % item_id + '/plus30/'

        item = Listitem()
        item.label = category_title
        item.set_callback(list_videos,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, **kwargs):

    resp = urlquick.get(category_url)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='vc_gitem-zone vc_gitem-zone-c']"):
        video_title = video_datas.find(".//a[@class='vc_gitem-link']").get(
            'title')
        video_image = ''  # TODO video_datas.find_all('img', class_='vc_gitem-zone-img')[0].get('src')
        video_url = video_datas.find(".//a[@class='vc_gitem-link']").get(
            'href')

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

    resp = urlquick.get(video_url)
    final_url = 'https://vod.infomaniak.com/redirect/cineplume_vod/' + re.compile(
        r'\[vod\](.*?)\[\/vod\]').findall(resp.text)[0]

    if download_mode:
        return download.download_video(final_url)
    return final_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if item_id == 'viavosges':

        is_helper = inputstreamhelper.Helper('mpd')
        if not is_helper.check_inputstream():
            return False

        live_html = urlquick.get(
            URL_LIVE_VIAVOSGES,
            headers={'User-Agent': web_utils.get_random_ua()},
            max_age=-1)
        root = live_html.parse()
        url_live_datas = URL_ROOT_VIAVOSGES + root.find(
            ".//div[@class='HDR_VISIO']").get('data-url') + '&mode=html'

        resp = urlquick.get(url_live_datas,
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)
        json_parser = json.loads(resp.text)

        item = Listitem()
        item.path = json_parser["files"]["auto"]
        item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        return item

    if item_id == 'viamoselle':
        live_html = urlquick.get(
            URL_LIVE_VIAMOSELLE % item_id,
            headers={'User-Agent': web_utils.get_random_ua()},
            max_age=-1)
    else:
        live_html = urlquick.get(
            URL_LIVE % item_id,
            headers={'User-Agent': web_utils.get_random_ua()},
            max_age=-1)
    root = live_html.parse()
    list_lives_datas = root.findall('.//iframe')
    live_id = ''
    for live_datas in list_lives_datas:
        src_datas = live_datas.get('src')
        break

    if 'dailymotion' in src_datas:
        live_id = re.compile(r'dailymotion.com/embed/video/(.*?)[\?\"]'
                             ).findall(src_datas)[0]
        return resolver_proxy.get_stream_dailymotion(plugin, live_id, False)

    if 'infomaniak' in src_datas:
        player_id = src_datas.split('player=')[1]
        resp2 = urlquick.get(
            URL_STREAM_INFOMANIAK % player_id,
            headers={'User-Agent': web_utils.get_random_ua()},
            max_age=-1)
        json_parser = json.loads(resp2.text)
        return 'https://' + json_parser["sPlaylist"]

    if 'creacast' in src_datas:
        resp2 = urlquick.get(
            src_datas,
            headers={'User-Agent': web_utils.get_random_ua()},
            max_age=-1)
        return re.compile(r'file\: \"(.*?)\"').findall(resp2.text)[0]

    live_id = re.compile(r'v=(.*?)\&').findall(src_datas)[0]
    stream_json = urlquick.post(
        URL_STREAM,
        data={
            'action': 'video_info',
            'refvideo': live_id
        },
        headers={'User-Agent': web_utils.get_random_ua()},
        max_age=-1)
    stream_jsonparser = json.loads(stream_json.text)
    return stream_jsonparser["data"]["bitrates"]["hls"]
