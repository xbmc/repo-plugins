# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re
import requests

import inputstreamhelper
from codequick import Listitem, Resolver, Route
from kodi_six import xbmcgui
import urlquick

from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment


# TODO
# Mode code brightcove protected by DRM in resolver_proxy

URL_ROOT = 'https://uktvplay.uktv.co.uk'

URL_BRIGHTCOVE_POLICY_KEY = 'https://players.brightcove.net/%s/%s_default/index.min.js'
# AccountId, PlayerId

URL_BRIGHTCOVE_VIDEO_JSON = 'https://edge.api.brightcove.com/'\
                            'playback/v1/accounts/%s/videos/%s'
# AccountId, VideoId

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

URL_LIVE = 'https://uktvplay.uktv.co.uk/watch-live/%s'
# Channel name

URL_STREAM_LIVE = 'https://v2-streams-elb.simplestreamcdn.com/api/live/stream/%s?key=%s&platform=chrome&user=%s'
# data_channel, key, user

URL_LIVE_KEY = 'https://mp.simplestream.com/uktv/1.0.4/ss.js'

URL_LIVE_TOKEN = 'https://sctoken.uktvapi.co.uk/?stream_id=%s'
# data_channel

URL_LOGIN_TOKEN = 'https://s3-eu-west-1.amazonaws.com/uktv-static/fgprod/play/6fc13c8.js'

URL_LOGIN_MODAL = 'https://uktvplay.uktv.co.uk/account/'

URL_COMPTE_LOGIN = 'https://live.mppglobal.com/api/accounts/authenticate/'


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

    resp = urlquick.get(URL_CATEGORIES)
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

    resp = urlquick.get(URL_CATEGORIES)
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

    resp = urlquick.get(URL_PROGRAMS_SUBCATEGORY % sub_category_slug)
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
                        (letter_value.replace('0-9', '0'), letter_value))
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

    resp = urlquick.get(URL_INFO_PROGRAM % program_slug)
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

    resp = urlquick.get(URL_VIDEOS % serie_id)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["episodes"]:
        video_title = video_datas["brand_name"] + \
            ' - ' ' S%sE%s' % (video_datas["series_number"], str(video_datas["episode_number"])) + ' - ' + video_datas["name"]
        video_image = video_datas["image"]
        video_plot = video_datas["synopsis"]
        video_duration = video_datas["duration"] * 60
        video_id = video_datas["video_id"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.set_callback(get_video_url,
                          item_id=item_id,
                          data_video_id=video_id)
        item_post_treatment(item)
        yield item


# BRIGHTCOVE Part
def get_brightcove_policy_key(data_account, data_player):
    """Get policy key"""
    file_js = urlquick.get(URL_BRIGHTCOVE_POLICY_KEY %
                           (data_account, data_player))
    return re.compile('policyKey:"(.+?)"').findall(file_js.text)[0]


@Resolver.register
def get_video_url(plugin, item_id, data_video_id, **kwargs):

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    # create session request
    session_requests = requests.session()

    # Get data_account / data_player
    resp = session_requests.get(URL_ROOT)
    data_account_player = re.search('//players\.brightcove\.net/([0-9]+)/([A-Za-z0-9]+)_default/', resp.text)
    data_account = data_account_player.group(1)
    data_player = data_account_player.group(2)

    # Method to get JSON from 'edge.api.brightcove.com'
    resp2 = session_requests.get(
        URL_BRIGHTCOVE_VIDEO_JSON % (data_account, data_video_id),
        headers={
            'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36',
            'Accept':
            'application/json;pk=%s' %
            (get_brightcove_policy_key(data_account, data_player))
        })

    json_parser = json.loads(resp2.text)

    video_url = ''
    licence_key = ''
    if 'sources' in json_parser:
        for url in json_parser["sources"]:
            if 'src' in url:
                if 'com.widevine.alpha' in url["key_systems"]:
                    video_url = url["src"]
                    licence_key = url["key_systems"]['com.widevine.alpha'][
                        'license_url']

    item = Listitem()
    item.path = video_url
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property[
        'inputstream.adaptive.license_key'] = licence_key + '|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=manifest.prod.boltdns.net|R{SSM}|'

    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    # create session request
    session_requests = requests.session()
    session_requests.get(URL_LOGIN_MODAL)

    resptokenid = session_requests.get(URL_LOGIN_TOKEN)
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
    resplogin = session_requests.post(
        URL_COMPTE_LOGIN, data=payload, headers={
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            'Origin': 'https://uktvplay.uktv.co.uk',
            'Referer': 'https://uktvplay.uktv.co.uk/account/',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
            'X-TokenId': token_id,
            'X-Version': '9.0.0'
        })
    if resplogin.status_code >= 400:
        plugin.notify('ERROR', 'UKTVPlay : ' + plugin.localize(30711))
        return False
    json_parser_resplogin = json.loads(resplogin.content)

    if 'home_uktvplay' in item_id:
        channel_uktvplay_id = 'home'
    else:
        channel_uktvplay_id = item_id

    respdatachannel = session_requests.get(URL_LIVE % channel_uktvplay_id)
    data_channel = re.compile(r'channelStreamId:(.*?)}').findall(
        respdatachannel.text)[0]

    respkey = session_requests.get(URL_LIVE_KEY)
    app_key = re.compile(r'app\_key"\ \: \"(.*?)\"').findall(respkey.text)[0]

    resptoken = session_requests.get(URL_LIVE_TOKEN % data_channel)
    json_parser_resptoken = json.loads(resptoken.text)

    respstreamdatas = session_requests.post(
        URL_STREAM_LIVE % (data_channel, app_key,
                           str(json_parser_resplogin["accountId"])),
        headers={
            'Token-Expiry': json_parser_resptoken["expiry"],
            'Token': json_parser_resptoken["token"],
            'Uvid': data_channel,
            'Userid': str(json_parser_resplogin["accountId"])
        })
    json_parser = json.loads(respstreamdatas.text)

    item = Listitem()
    item.path = json_parser["response"]["drm"]["widevine"]["stream"]
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property[
        'inputstream.adaptive.license_key'] = json_parser["response"]["drm"]["widevine"]["licenseAcquisitionUrl"] + '|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36|R{SSM}|'

    return item
