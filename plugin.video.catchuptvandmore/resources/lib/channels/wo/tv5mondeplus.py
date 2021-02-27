# -*- coding: utf-8 -*-
"""
    Copyright (C) 2016-2020 Team Catch-up TV & More
    This file is part of Catch-up TV & More.
    SPDX-License-Identifier: GPL-2.0-or-later
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from builtins import str
from codequick import Route, Resolver, Listitem, utils, Script


from resources.lib import web_utils
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment

import inputstreamhelper
import json
import urlquick
from kodi_six import xbmcgui
# Working for Python 2/3
try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

URL_TV5MONDEPLUS_ROOT = 'https://api.tv5mondeplus.com'

URL_TV5MONDEPLUS_ROOT_API = URL_TV5MONDEPLUS_ROOT + '/v2/whitelabel/customer/TV5MONDE/businessunit/TV5MONDEplus/config/sandwich?onlyPublished=true&allowedCountry=%s'
# Lang (TODO Add other languages)

URL_TV5MONDEPLUS_COMPONENT_API = URL_TV5MONDEPLUS_ROOT + '/v2/whitelabel/customer/TV5MONDE/businessunit/TV5MONDEplus/config/sandwich/component/%s?client=json&onlyPublished=true&allowedCountry=%s'
# componentId, Lang (TODO Add other languages)

URL_VIDEOS_DATAS = 'https://www.tv5mondeplus.com/api/graphql/v1/'

URL_STREAM_DATAS = URL_TV5MONDEPLUS_ROOT + '/v2/customer/TV5MONDE/businessunit/TV5MONDEplus/entitlement/%s/play'
# Video_Id

URL_TV5MONDEPLUS_AUTH_ANONYMOUS_API = URL_TV5MONDEPLUS_ROOT + '/v1/customer/TV5MONDE/businessunit/TV5MONDEplus/auth/anonymous'

# TODO Add more langue like ARTE
LANG = 'FR'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    resp = urlquick.get(URL_TV5MONDEPLUS_ROOT_API % LANG)
    json_parser = json.loads(resp.text)
    category_referenceId = json_parser["components"]["menu"][0]["referenceId"]

    resp2 = urlquick.get(URL_TV5MONDEPLUS_COMPONENT_API % (category_referenceId, LANG))
    json_parser2 = json.loads(resp2.text)

    for menu_category_datas in json_parser2["components"]["menuItems"]:
        if 'appSubType' in menu_category_datas:
            if 'Component' in menu_category_datas["appSubType"]:
                if "" == menu_category_datas["presentation"]["fallback"]["title"]:
                    menu_category_title = json_parser["components"]["homePage"][0]["name"]
                else:
                    menu_category_title = menu_category_datas["presentation"]["fallback"]["title"]
                menu_category_referenceId = menu_category_datas["actions"]["default"]["componentId"]

                item = Listitem()
                item.label = menu_category_title
                item.set_callback(list_menu_sub_categories,
                                  item_id=item_id,
                                  menu_category_referenceId=menu_category_referenceId)
                item_post_treatment(item)
                yield item


@Route.register
def list_menu_sub_categories(plugin, item_id, menu_category_referenceId, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_TV5MONDEPLUS_COMPONENT_API % (menu_category_referenceId, LANG))
    json_parser = json.loads(resp.text)

    for menu_sub_category_datas in json_parser["components"]["pageBody"]:
        if 'appSubType' in menu_sub_category_datas:
            if 'Curated' in menu_sub_category_datas["appSubType"] or 'TagsQuery' in menu_sub_category_datas["appSubType"]:
                menu_sub_category_title = menu_sub_category_datas["name"]
                menu_sub_category_referenceId = menu_sub_category_datas["referenceId"]

                item = Listitem()
                item.label = menu_sub_category_title
                item.set_callback(list_programs,
                                  item_id=item_id,
                                  program_referenceId=menu_sub_category_referenceId)
                item_post_treatment(item)
                yield item


@Route.register
def list_programs(plugin, item_id, program_referenceId, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_TV5MONDEPLUS_COMPONENT_API % (program_referenceId, LANG))
    json_parser = json.loads(resp.text)

    new_url = URL_TV5MONDEPLUS_ROOT + json_parser["contentUrl"]["url"]
    resp2 = urlquick.get(new_url)
    json_parser2 = json.loads(resp2.text)

    for program_datas in json_parser2["items"]:
        program_title = ''
        program_image = ''
        program_plot = ''
        for localized_datas in program_datas["localized"]:
            if LANG.lower() in localized_datas["locale"]:
                program_title = localized_datas["title"]
                program_plot = localized_datas["description"]
                for images_datas in localized_datas["images"]:
                    if 'poster' in images_datas["type"]:
                        program_image = images_datas["url"]
        program_assetId = program_datas["assetId"]
        program_type = program_datas["type"]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.info['plot'] = program_plot
        if 'MOVIE' in program_type:
            item.set_callback(list_video_movie,
                              item_id=item_id,
                              program_assetId=program_assetId)
        else:
            item.set_callback(list_seasons,
                              item_id=item_id,
                              program_assetId=program_assetId)
        item_post_treatment(item)
        yield item


@Route.register
def list_seasons(plugin, item_id, program_assetId, **kwargs):

    # TODO find sha256Hash ?
    payload = {
        'operationName': 'VODContentDetails',
        'variables': '{"contentId":"redbee:%s:%s"}' % (program_assetId, LANG.lower()),
        'extensions': '{"persistedQuery":%s}' % '{"version":1,"sha256Hash":"ba116fe7551261e4794db5d04739c7a2489a585abc27675dfc89de87e3353b9a"}'
    }
    resp = urlquick.get(URL_VIDEOS_DATAS, params=payload)
    json_parser = json.loads(resp.text)

    payload2 = {
        'operationName': 'VODContentSeasons',
        'variables': '{"contentId":"%s"}' % json_parser["data"]["lookupContent"]["id"],
        'extensions': '{"persistedQuery":%s}' % '{"version":1,"sha256Hash":"c17f7c475debdc90a1e4b7beea6ee5916b74c1756d00f3b5976caf68579cc81c"}'
    }
    resp2 = urlquick.get(URL_VIDEOS_DATAS, params=payload2)
    json_parser2 = json.loads(resp2.text)

    for season_datas in json_parser2["data"]["lookupContent"]["seasons"]["items"]:
        season_title = 'Season %s' % str(season_datas["seasonNumber"])
        season_id = season_datas["id"]

        item = Listitem()
        item.label = season_title
        item.set_callback(list_videos_of_season,
                          item_id=item_id,
                          season_id=season_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_of_season(plugin, item_id, season_id, **kwargs):

    # TODO find sha256Hash ?
    payload = {
        'operationName': 'VODContentEpisodes',
        'variables': '{"contentId":"%s"}' % season_id,
        'extensions': '{"persistedQuery":%s}' % '{"version":1,"sha256Hash":"6517f1871edb821d4d62bade0acb5f9007e3174995ff2efae71969a2ee92eef2"}'
    }
    resp = urlquick.get(URL_VIDEOS_DATAS, params=payload)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["data"]["lookupContent"]["episodes"]["items"]:
        video_title = 'Episode %s' % str(video_datas["episodeNumber"])
        video_image = video_datas["artworks"][0]["source"]
        video_plot = video_datas["description"]
        video_id = video_datas["externalIds"][0]["identifier"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item


@Route.register
def list_video_movie(plugin, item_id, program_assetId, **kwargs):

    # TODO find sha256Hash ?
    payload = {
        'operationName': 'VODContentDetails',
        'variables': '{"contentId":"redbee:%s:%s"}' % (program_assetId, LANG.lower()),
        'extensions': '{"persistedQuery":%s}' % '{"version":1,"sha256Hash":"ba116fe7551261e4794db5d04739c7a2489a585abc27675dfc89de87e3353b9a"}'
    }
    resp = urlquick.get(URL_VIDEOS_DATAS, params=payload)
    json_parser = json.loads(resp.text)
    video_datas = json_parser["data"]["lookupContent"]

    video_title = video_datas["title"]
    video_image = video_datas["artworks"][0]["source"]
    video_plot = video_datas["description"]
    video_id = video_datas["externalIds"][0]["identifier"]

    item = Listitem()
    item.label = video_title
    item.art['thumb'] = item.art['landscape'] = video_image
    item.info['plot'] = video_plot
    item.set_callback(get_video_url,
                      item_id=item_id,
                      video_id=video_id)
    item_post_treatment(item, is_playable=True, is_downloadable=False)
    yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok(plugin.localize(14116), plugin.localize(30602))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    # Get info_poste ?
    info_poste = {
        'height': 1080,
        'width': 1920,
        'model': 'Netscape',
        'name': 'Gecko',
        'os': 'Linux x86_64',
        'osVersion': '5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36","manufacturer":"Google Inc.',
        'type': 'WEB'
    }
    # Get DeviveId ?
    payload = {
        'deviceId': 'WEB_450118664537368504183835373631080192024',
        'device': info_poste,
        'rememberMe': False,
        'username': '',
        'password': ''
    }
    resp = urlquick.post(URL_TV5MONDEPLUS_AUTH_ANONYMOUS_API, json=payload)
    json_parser = json.loads(resp.text)

    headers = {
        'authorization':
        'Bearer %s' % json_parser["sessionToken"],
    }
    resp2 = urlquick.get(URL_STREAM_DATAS % video_id, headers=headers)
    json_parser2 = json.loads(resp2.text)

    item = Listitem()
    item.path = json_parser2["formats"][0]["mediaLocator"]
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property[
        'inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    # Get Licence Key HTTP 500 - {"code":100000,"message":"An error has occurred. See logs for details."}
    headers2 = {
        'authorization':
        'Bearer %s' % json_parser2["playToken"],
        'referer':
        'https://www.tv5mondeplus.com/',
        'user-agent':
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
        'origin':
        'https://www.tv5mondeplus.com',
        'accept':
        '*/*',
        'accept-encoding':
        'gzip, deflate, br',
        'accept-language':
        'en-US,en;q=0.9',
        'sec-fetch-dest':
        'empty',
        'sec-fetch-mode':
        'cors',
        'sec-fetch-site':
        'cross-site'
    }
    item.property[
        'inputstream.adaptive.license_key'] = '%s|%s|R{SSM}|' % (
            json_parser2["formats"][0]["drm"]["com.widevine.alpha"]["licenseServerUrl"], urlencode(headers2))
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    return item
