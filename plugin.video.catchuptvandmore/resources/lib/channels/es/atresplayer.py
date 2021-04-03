# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re

import inputstreamhelper
from six import text_type
from codequick import Listitem, Resolver, Route
from kodi_six import xbmc
import urlquick

from resources.lib import web_utils
from resources.lib.kodi_utils import get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Add Account

URL_ROOT = 'https://www.atresplayer.com/'
# channel name

URL_LIVE_STREAM = 'https://api.atresplayer.com/client/v1/player/live/%s'
# Live Id

URL_COMPTE_LOGIN = 'https://account.atresmedia.com/api/login'

LIVE_ATRES_PLAYER = {
    'antena3': 'ANTENA_3_ID',
    'lasexta': 'LA_SEXTA_ID',
    'neox': 'NEOX_ID',
    'nova': 'NOVA_ID',
    'mega': 'MEGA_ID',
    'atreseries': 'ATRESERIES_ID'
}


@Route.register
def list_categories(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT)
    json_value = re.compile(r'PRELOADED\_STATE\_\_ \= (.*?)\}\;').findall(
        resp.text)[0]
    json_parser = json.loads(json_value + '}')

    for categories_datas in json_parser["channels"]:
        for category_datas in json_parser["channels"][categories_datas][
                "categories"]:
            category_title = category_datas["title"]
            category_url = category_datas["link"]["href"]

            item = Listitem()
            item.label = category_title
            item.set_callback(list_programs,
                              item_id=item_id,
                              category_url=category_url,
                              page='0')
            item_post_treatment(item)
            yield item


@Route.register
def list_programs(plugin, item_id, category_url, page, **kwargs):

    resp = urlquick.get(category_url)
    json_parser = json.loads(resp.text)

    resp2 = urlquick.get(json_parser["rows"][0]["href"] + '&page=%s' % page)
    json_parser2 = json.loads(resp2.text)

    for program_datas in json_parser2["itemRows"]:
        program_title = program_datas["title"]
        program_image = program_datas["image"]["pathHorizontal"]
        program_url = program_datas["link"]["href"]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_sub_programs,
                          item_id=item_id,
                          program_url=program_url)
        item_post_treatment(item)
        yield item

    if json_parser2["pageInfo"]["hasNext"]:
        yield Listitem.next_page(item_id=item_id,
                                 category_url=category_url,
                                 page=str(int(page) + 1))


@Route.register
def list_sub_programs(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    json_parser = json.loads(resp.text)

    for sub_program_datas in json_parser["rows"]:
        if 'EPISODE' in sub_program_datas["type"] or \
                'VIDEO' in sub_program_datas["type"]:
            sub_program_title = sub_program_datas["title"]
            sub_program_url = sub_program_datas["href"]

            item = Listitem()
            item.label = sub_program_title
            item.set_callback(list_videos,
                              item_id=item_id,
                              sub_program_url=sub_program_url,
                              page='0')
            item_post_treatment(item)
            yield item


@Route.register
def list_videos(plugin, item_id, sub_program_url, page, **kwargs):

    resp = urlquick.get(sub_program_url + '&page=%s' % page)
    json_parser = json.loads(resp.text)

    if 'itemRows' in json_parser:
        for video_datas in json_parser["itemRows"]:

            video_title = video_datas["image"]["title"]
            video_image = video_datas["image"]["pathHorizontal"]
            video_url_info = video_datas["link"]["href"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image
            item.set_callback(list_video_more_infos,
                              item_id=item_id,
                              video_url_info=video_url_info)
            item_post_treatment(item)
            yield item

        if json_parser["pageInfo"]["hasNext"]:
            yield Listitem.next_page(item_id=item_id,
                                     sub_program_url=sub_program_url,
                                     page=str(int(page) + 1))


@Route.register
def list_video_more_infos(plugin, item_id, video_url_info, **kwargs):

    resp = urlquick.get(video_url_info)
    json_parser = json.loads(resp.text)

    video_title = json_parser["seoTitle"]
    video_image = json_parser["image"]["pathHorizontal"]
    video_plot = json_parser["seoDescription"]
    video_duration = int(json_parser["duration"])
    video_url = json_parser["urlVideo"]

    item = Listitem()
    item.label = video_title
    item.art['thumb'] = item.art['landscape'] = video_image
    item.info['duration'] = video_duration
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

    is_helper = inputstreamhelper.Helper('mpd')
    if not is_helper.check_inputstream():
        return False

    resp = urlquick.get(video_url)
    json_parser = json.loads(resp.text)

    if 'error' in json_parser:
        # Add Notification
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    # Code from here : https://github.com/asciidisco/plugin.video.telekom-sport/blob/master/resources/lib/Utils.py
    # Thank you asciidisco
    payload = {
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'Addons.GetAddonDetails',
        'params': {
            'addonid': 'inputstream.adaptive',
            'properties': ['enabled', 'version']
        }
    }
    # execute the request
    response = xbmc.executeJSONRPC(json.dumps(payload))
    responses_uni = text_type(response, 'utf-8', errors='ignore')
    response_serialized = json.loads(responses_uni)
    if 'error' in list(response_serialized.keys()):
        # Add Notification
        plugin.notify('ERROR', plugin.localize(30719))
        return False

    result = response_serialized.get('result', {})
    addon = result.get('addon', {})
    if addon.get('enabled', False) is True:
        item = Listitem()
        item.path = json_parser["sources"][1]["src"]
        item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
        item.property['inputstream.adaptive.manifest_type'] = 'mpd'
        item.label = get_selected_item_label()
        item.art.update(get_selected_item_art())
        item.info.update(get_selected_item_info())
        return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_ROOT,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    lives_json = re.compile(r'window.__ENV__ = (.*?)\;').findall(resp.text)[0]
    json_parser = json.loads(lives_json)
    live_stream_json = urlquick.get(
        URL_LIVE_STREAM % json_parser[LIVE_ATRES_PLAYER[item_id]],
        headers={'User-Agent': web_utils.get_random_ua()},
        max_age=-1)
    live_stream_jsonparser = json.loads(live_stream_json.text)
    if "sources" not in live_stream_jsonparser:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    return live_stream_jsonparser["sources"][0]["src"]
