# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re

from codequick import Listitem, Resolver, Route
from kodi_six import xbmcgui
import urlquick

from resources.lib import resolver_proxy, web_utils

from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'https://u.co.uk'

URL_API = 'https://vschedules.uktv.co.uk'

LETTER_LIST = [
    "0-9", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
    "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
]

URL_PROGRAMS = URL_API + '/vod/brand_list/?starts_with=%s&letter_name=%s&is_watchable=True'
# Letter

URL_INFO_PROGRAM = URL_API + '/vod/brand/?slug=%s'
# Program_slug

URL_VIDEOS = URL_API + '/vod/series/?id=%s'
# Serie_ID

URL_CATEGORIES = URL_API + '/vod/categories/'

URL_PROGRAMS_SUBCATEGORY = URL_API + '/vod/subcategory_brands/?slug=%s&size=999'
# Slug subcategory

URL_LIVE = 'https://u.uktv.co.uk/watch-live/%s'
# Channel name

URL_STREAM_LIVE = 'https://v2-streams-elb.simplestreamcdn.com/api/live/stream/%s?key=%s&platform=chrome&user=%s'
# data_channel, key, user

URL_CHANNEL_ID = "https://vschedules.uktv.co.uk/vod/now_and_next/"

URL_LIVE_KEY = 'https://mp.simplestream.com/uktv/1.0.4/ss.js'

URL_LIVE_TOKEN = 'https://sctoken.uktvapi.co.uk/?stream_id=%s'
# data_channel

URL_LOGIN_TOKEN = 'https://s3-eu-west-1.amazonaws.com/uktv-static/fgprod/play/6fc13c8.js'

URL_LOGIN_MODAL = 'https://uktvplay.uktv.co.uk/account/'

URL_COMPTE_LOGIN = 'https://live.mppglobal.com/api/accounts/authenticate/'

URL_CHUNKS = "https://u.co.uk/shows/%s/series-%s/episode-%s/%s"

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    """
    item = Listitem()
    item.label = 'A-Z'
    item.set_callback(list_letters, item_id=item_id)
    item_post_treatment(item)
    yield item

    resp = urlquick.get(URL_CATEGORIES, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    for category_datas in json_parser["categories"]:
        category_title = category_datas["name"]
        category_slug = category_datas["slug"]
        item = Listitem()
        item.label = category_title
        item.set_callback(list_sub_categories,
                          item_id=item_id,
                          category_slug=category_slug)
        item_post_treatment(item)
        yield item


@Route.register
def list_sub_categories(plugin, item_id, category_slug, **kwargs):

    resp = urlquick.get(URL_CATEGORIES, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    for category_datas in json_parser["categories"]:
        if category_slug in category_datas["slug"]:
            for sub_category_datas in category_datas["subcategories"]:
                sub_category_title = sub_category_datas["name"]
                sub_category_slug = sub_category_datas["slug"]
                item = Listitem()
                item.label = sub_category_title
                item.set_callback(list_programs_sub_categories,
                                  item_id=item_id,
                                  sub_category_slug=sub_category_slug)
                item_post_treatment(item)
                yield item


@Route.register
def list_programs_sub_categories(plugin, item_id, sub_category_slug, **kwargs):

    resp = urlquick.get(URL_PROGRAMS_SUBCATEGORY % sub_category_slug, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser["brand_list"]:
        program_title = program_datas['name']
        program_image = ''
        if 'image' in program_datas:
            program_image = program_datas['image']
        program_slug = program_datas['slug']

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_seasons,
                          item_id=item_id,
                          program_slug=program_slug)
        item_post_treatment(item)
        yield item


@Route.register
def list_letters(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    for letter_value in LETTER_LIST:
        item = Listitem()
        item.label = letter_value
        item.set_callback(list_programs,
                          item_id=item_id,
                          letter_value=letter_value)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, letter_value, **kwargs):

    resp = urlquick.get(URL_PROGRAMS %
                        (letter_value.replace('0-9', '0'), letter_value),
                        headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser:
        program_title = program_datas['name']
        program_image = ''
        if 'image' in program_datas:
            program_image = program_datas['image']
        program_slug = program_datas['slug']

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_seasons,
                          item_id=item_id,
                          program_slug=program_slug)
        item_post_treatment(item)
        yield item


@Route.register
def list_seasons(plugin, item_id, program_slug, **kwargs):

    resp = urlquick.get(URL_INFO_PROGRAM % program_slug, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    for season_datas in json_parser["series"]:
        season_title = 'Season - ' + season_datas['number']
        serie_id = season_datas["id"]

        item = Listitem()
        item.label = season_title
        item.set_callback(list_videos, item_id=item_id, serie_id=serie_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, serie_id, **kwargs):

    resp = urlquick.get(URL_VIDEOS % serie_id, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["episodes"]:
        video_title = video_datas["brand_name"] + \
            ' - ' ' S%sE%s' % (video_datas["series_number"], str(video_datas["episode_number"])) + ' - ' + video_datas["name"]
        video_image = video_datas["image"]
        video_plot = video_datas["synopsis"]
        video_duration = video_datas["duration"] * 60
        video_id = video_datas["video_id"]

        show_name = URL_CHUNKS % (video_datas["brand_slug"],
                                  video_datas["series_number"],
                                  video_datas["episode_number"],
                                  video_datas["video_id"])

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.set_callback(get_video_url,
                          item_id=item_id,
                          data_video_id=video_id,
                          show_name=show_name)
        item_post_treatment(item)
        yield item


@Resolver.register
def get_video_url(plugin, item_id, data_video_id, show_name, **kwargs):
    data_account = "1242911124001"
    data_player = "0RyQs9qPh"

    return resolver_proxy.get_brightcove_video_json(plugin, data_account, data_player, data_video_id)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    # create session request
    session_requests = urlquick.session()
    session_requests.get(URL_LOGIN_MODAL, headers=GENERIC_HEADERS, max_age=-1)

    resptokenid = session_requests.get(URL_LOGIN_TOKEN, headers=GENERIC_HEADERS, max_age=-1)
    token_id = re.compile(r'tokenid\":\"(.*?)\"').findall(resptokenid.text)[0]

    if plugin.setting.get_string(
            'uktvplay.login') == '' or plugin.setting.get_string(
                'uktvplay.password') == '':
        xbmcgui.Dialog().ok('Info',
                            plugin.localize(30604) %
                            ('UKTVPlay', 'https://uktvplay.uktv.co.uk'))
        return False

    # Build PAYLOAD
    payload = {
        'email': plugin.setting.get_string('uktvplay.login'),
        'password': plugin.setting.get_string('uktvplay.password')
    }
    payload = json.dumps(payload)

    # LOGIN
    # KO - resp2 = session_urlquick.post(
    #     URL_COMPTE_LOGIN, data=payload,
    #     headers={'User-Agent': web_utils.get_ua, 'referer': URL_COMPTE_LOGIN})
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Origin': 'https://uktvplay.uktv.co.uk',
        'Content-Type': 'application/json;charset=UTF-8',
        'Referer': 'https://uktvplay.uktv.co.uk/account/',
        'User-Agent': web_utils.get_random_ua(),
        'X-TokenId': token_id,
        'X-Version': '9.0.0'
    }
    resp = session_requests.post(URL_COMPTE_LOGIN, data=payload, headers=headers, max_age=-1)
    if resp.status_code >= 400:
        plugin.notify('ERROR', 'UKTVPlay : ' + plugin.localize(30711))
        return False
    json_parser_resplogin = json.loads(resp.content)

    if 'home_uktvplay' in item_id:
        channel_uktvplay_id = 'home'
    else:
        channel_uktvplay_id = item_id

    resp = session_requests.get(URL_CHANNEL_ID, headers=GENERIC_HEADERS, max_age=-1)
    root = json.loads(resp.text)
    data_channel = str(root[channel_uktvplay_id][0]['channel_stream_id'])

    respkey = session_requests.get(URL_LIVE_KEY, headers=GENERIC_HEADERS, max_age=-1)
    app_key = re.compile(r'app\_key"\ \: \"(.*?)\"').findall(respkey.text)[0]

    resp = session_requests.get(URL_LIVE_TOKEN % data_channel, headers=GENERIC_HEADERS, max_age=-1)
    json_parser_resptoken = json.loads(resp.text)

    data_url = URL_STREAM_LIVE % (data_channel, app_key, str(json_parser_resplogin["accountId"]))
    headers = {
        'Token-Expiry': json_parser_resptoken["expiry"],
        'Token': json_parser_resptoken["token"],
        'Uvid': data_channel,
        'Userid': str(json_parser_resplogin["accountId"]),
        "User-Agent": web_utils.get_random_ua()
    }
    respstreamdatas = session_requests.post(data_url, headers=headers, max_age=-1)
    json_parser = json.loads(respstreamdatas.text)

    headers = {'Content-type': ''}
    video_url = json_parser["response"]["drm"]["widevine"]["stream"]
    license_url = json_parser["response"]["drm"]["widevine"]["licenseAcquisitionUrl"]

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, license_url=license_url,
                                                  headers=headers, manifest_type='mpd')
