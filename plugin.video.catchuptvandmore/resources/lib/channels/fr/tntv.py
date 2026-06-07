# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re
from builtins import str
import base64
import time
import uuid

from codequick import Listitem, Resolver, Route, Script
import urlquick
import json
import htmlement

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = "https://www.tntv.pf"
URL_API = URL_ROOT + "/tntv/wp-admin/admin-ajax.php"
URL_BEACON_TNTV_COVE = 'https://beacon.playback.api.brightcove.com/tntv/api'
URL_TNTV_KEYS = URL_BEACON_TNTV_COVE + '/cache_keys'
URL_TNTV_API = URL_BEACON_TNTV_COVE + '/assets/%s'
URL_EPG_API = URL_BEACON_TNTV_COVE + '/onnow'
URL_TNTV_TOKEN = URL_BEACON_TNTV_COVE + '/account/anonymous_login'
URL_TNTV_STREAM = URL_TNTV_API + '/streams/%s'
URL_LIVE = URL_ROOT + "/direct"

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    duplicate = []

    for subject in root.iterfind(".//li"):
        if subject.get('class') is not None and 'taxonomy' in subject.get('class'):
            for category in subject.findall(".//a"):
                if category.get('href') is not None:
                    program = category.get('href')
                    if 'category/programme' in program:
                        category_name = category.find(".//div[@class='tdb-menu-item-text']").text
                        if category_name not in duplicate:
                            duplicate.append(category_name)
                            item = Listitem()
                            item.label = category.find(".//div[@class='tdb-menu-item-text']").text
                            item.set_callback(list_subcategories, subject=subject)
                            item_post_treatment(item)
                            yield item


@Route.register
def list_subcategories(plugin, subject, **kwargs):
    for submenu in subject.find(".//ul[@class='sub-menu']").iterfind(".//li"):
        submenu_url = submenu.find(".//a").get('href')
        if submenu_url[0] == '/':
            submenu_url = URL_ROOT + submenu_url

        sub_page = urlquick.get(submenu_url, headers=GENERIC_HEADERS, max_age=-1)
        sub_page_text = sub_page.text
        picture_url = re.compile(r'property\=\"og\:image\" content\=\"(.*?)\"').findall(sub_page_text)[0]
        for defered_script in sub_page.parse().iterfind('.//script'):
            script = defered_script.get('src')
            if script is not None and 'data:text/javascript;base64,' in script:
                coded_script = re.compile(r'data:text\/[^;]+;base64,([^"]+)$').findall(script)[0]
                decoded_script = base64.b64decode(coded_script).decode("utf-8")
                if 'tdBlockNonce' in decoded_script:
                    token = re.compile(r'tdBlockNonce\=\"(.*?)\"').findall(decoded_script)[0]
                if 'block_tdi_84.atts' in decoded_script:
                    atts = re.compile(r'block\_tdi\_84\.atts \= \'\{(.*?)\}\'').findall(decoded_script)[0].replace('+', ' ')

        item = Listitem()
        item.art['thumb'] = item.art['landscape'] = picture_url
        item.label = submenu.find(".//div").text
        item.set_callback(list_videos, page='1', token=token, atts=atts)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, page, token, atts, **kwargs):
    data = {
        'td_atts': "{" + atts + "}",
        'action': 'td_ajax_block',
        'td_block_id': 'tdi_84',
        'td_column_number': '3',
        'td_current_page': page,
        'block_type': 'tdb_single_related',
        'td_filter_value': '',
        'td_user_action': '',
        'td_magic_token': token,
    }

    params = {
        'td_theme_name': 'Newspaper',
        'v': '12',
    }

    resp = urlquick.post(URL_API, headers=GENERIC_HEADERS, params=params, data=data, max_age=-1)
    json_parser = json.loads(resp.text)
    root = htmlement.fromstring(json_parser['td_data'])

    for video in root.iterfind(".//div[@class='tdb_module_related td_module_wrap td-animation-stack']"):
        item = Listitem()
        for video_pict in video.iterfind('.//span'):
            if video_pict.get('style') is not None:
                pict_url = re.compile(r"url\(\'(.*?)\'").findall(video_pict.get('style'))[0]
        item.art['thumb'] = item.art['landscape'] = pict_url
        video_desc = video.find(".//h3").find(".//a")
        item.label = video_desc.get('title')
        video_url = video_desc.get('href')
        item.set_callback(get_video_url, video_url=video_url, is_playable=True, is_downloadable=True)
        yield item

    if json_parser['td_hide_next'] is False:
        yield Listitem.next_page(page=str(int(page) + 1), token=token, atts=atts)


@Resolver.register
def get_video_url(plugin, video_url, download_mode=False, **kwargs):
    resp = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for player in root.iterfind(".//frame"):
        if player.get('lazy') is None:
            video_id = re.compile(r'embed\/\?feature').findall(player.get('src'))
            if len(video_id) > 0:
                return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)

    player = root.find('.//video-js')
    data_account = player.get('data-account')
    data_player = player.get('data-player')
    data_video_id = player.get('data-video-id')
    return resolver_proxy.get_brightcove_video_json(plugin, data_account, data_player, data_video_id, None, download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.tntv.pf/',
    }

    params = {
        'device_type': 'web',
    }

    resp = urlquick.post(URL_TNTV_KEYS, params=params, headers=headers, max_age=-1)
    cohort = resp.json()['data'][0]['value']

    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'Referer': URL_ROOT,
    }

    params = {
        'cohort': cohort,
        'device_type': 'web',
        'device_layout': 'web',
        'datetimestamp': time.time(),
        'limit': '999',
    }

    resp = urlquick.get(URL_EPG_API, params=params, headers=headers, max_age=-1)
    datas = resp.json()
    asset_id = datas['data']['blocks'][0]['widgets'][0]['playlist']['contents'][0]['id']

    params = {
        'cohort': cohort,
        'device_type': 'web',
        'device_layout': 'web',
        'asset_id': asset_id,
    }

    resp = urlquick.get(URL_TNTV_API % asset_id, params=params, headers=headers, max_age=-1)
    datas = resp.json()

    policy_key = datas['data']['asset']['vc_playback_data']['policy_key']
    account_id = datas['data']['asset']['vc_playback_data']['bc_account_id']
    stream_id = datas['data']['asset']['streams'][0]['id']

    params = {
        'device_type': 'web',
        'duid': uuid.uuid4(),
    }

    resp = urlquick.post(URL_TNTV_TOKEN, params=params, headers=headers, max_age=-1)

    datas = resp.json()
    auth_token = datas['auth_token']

    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'Referer': URL_ROOT,
        'Authorization': 'Bearer ' + auth_token,
    }

    params = {
        'cohort': cohort,
        'device_type': 'web',
        'device_layout': 'web',
    }

    resp = urlquick.post(URL_TNTV_STREAM % (asset_id, stream_id), params=params, headers=headers, max_age=-1)

    datas = resp.json()
    data_video_id = datas['data']['stream']['url']
    ad_config_id = datas['data']['stream']['playback_query_parameters'][0]['value']
    params = {'ad_config_id': ad_config_id}

    return resolver_proxy.get_brightcove_video_json(plugin, account_id, None, data_video_id, policy_key, params=params)
