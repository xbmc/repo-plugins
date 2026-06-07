# -*- coding: utf-8 -*-
# Copyright: (c) 2016-2020, Team Catch-up TV & More
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import random
from builtins import str

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial
# noinspection PyUnresolvedReferences
from kodi_six import xbmcgui

from resources.lib import web_utils, resolver_proxy
from resources.lib.addon_utils import get_item_media_path
from resources.lib.kodi_utils import (get_kodi_version, get_selected_item_art, get_selected_item_label,
                                      get_selected_item_info)
from resources.lib.menu_utils import item_post_treatment
from resources.lib.web_utils import urlencode, get_random_ua

GENERIC_HEADERS = get_random_ua()
COUNTRY = web_utils.geoip()


def generate_fake_id():
    fake_id = ''.join(random.choice('0123456789abcdef') for _ in range(8))
    fake_id += '-'
    fake_id += ''.join(random.choice('0123456789abcdef') for _ in range(4))
    fake_id += '-'
    fake_id += ''.join(random.choice('0123456789abcdef') for _ in range(4))
    fake_id += '-'
    fake_id += ''.join(random.choice('0123456789abcdef') for _ in range(12))
    return fake_id


FAKE_DEVICE_ID = generate_fake_id()

BASE_URL_API = 'https://api.tv5mondeplus.com'
SANDWICH_API = BASE_URL_API + '/v2/whitelabel/customer/TV5MONDE/businessunit/TV5MONDEplus/config/sandwich'
COMPONENT_API = SANDWICH_API + '/component/%s?client=json&onlyPublished=true&allowedCountry=%s'
GRAPHQL_API = 'https://www.tv5mondeplus.com/api/graphql/v1/'
URL_STREAM_DATA = BASE_URL_API + '/v2/customer/TV5MONDE/businessunit/TV5MONDEplus/entitlement/%s/play'
AUTH_ANONYMOUS_API = BASE_URL_API + '/v1/customer/TV5MONDE/businessunit/TV5MONDEplus/auth/anonymous'
SEARCH_API = BASE_URL_API + "/v2/customer/TV5MONDE/businessunit/TV5MONDEplus/content/search/query/%s"

# TODO compute hashes instead
OPERATION_HASHES_WEB = {
    "VODCatalogSection": "TODO",  # TODO
    "VODContentDetailsList": "TODO",  # TODO
    "VODContentDetails": "d34748a7f69fd499dffa6845440c443194aed3b05de23bc5568a34de4689a80d",
    "VODContentEpisodes": "fe8d9bf478e3542a91dd70d989747fba7097b169d7de9b1c8a18748281f29a13",
    "VODContentOffers": "TODO",  # TODO
    "VODContentSearch": "TODO",  # TODO
    "VODContentSeasons": "3dd0d1d4b917a2f453410c92603fe7d066ab3c5eebf050549fcec74006cfd367",
    "VODPlaybackInfos": "TODO",  # TODO
    "VODSearchAutocomplete": "TODO",  # TODO
    "VODSectionItems": "TODO",  # TODO
    "VODSectionSubsections": "TODO",  # TODO
    "VODTopLevelServices": "TODO"  # TODO
}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """

    params = {
        "onlyPublished": "true",
        "allowedCountry": COUNTRY
    }

    resp = urlquick.get(SANDWICH_API, params=params)
    json_parser = resp.json()
    category_reference_id = json_parser["components"]["menu"][0]["referenceId"]

    resp2 = urlquick.get(COMPONENT_API % (category_reference_id, COUNTRY))
    json_parser2 = resp2.json()

    item = Listitem.search(list_videos_search, item_id=item_id, page='0')
    item.label = plugin.localize(30715)
    item_post_treatment(item)
    yield item

    for menu_category_data in json_parser2["components"]["menuItems"]:
        if 'appSubType' in menu_category_data:
            if 'Component' in menu_category_data["appSubType"]:
                if "" == menu_category_data["presentation"]["fallback"]["title"]:
                    menu_category_title = json_parser["components"]["homePage"][0]["name"]
                else:
                    menu_category_title = menu_category_data["presentation"]["fallback"]["title"]
                menu_category_reference_id = menu_category_data["actions"]["default"]["componentId"]

                item = Listitem()
                item.label = menu_category_title
                item.art["thumb"] = get_item_media_path('channels/wo/tv5mondeplus.png')
                item.set_callback(list_menu_sub_categories,
                                  item_id=item_id,
                                  menu_category_reference_id=menu_category_reference_id)
                item_post_treatment(item)
                yield item


@Route.register
def list_videos_search(plugin, search_query, item_id, page, **kwargs):
    language = Script.setting['tv5mondeplus.language']

    headers = {
        "User-Agent": GENERIC_HEADERS,
        "Accept": "*/*",
        "Accept-Language": language + ";q=0.8,en-US;q=0.5,en;q=0.3",
        "referrer": "https://www.tv5mondeplus.com/"
    }

    params = {
        "locale": language,
        "schemes": ["keyword", "subcategory", "category", "origin"],
        "client": "json",
        "allowedCountry": COUNTRY,
        "onlyPublished": "true"
    }
    if search_query is None or len(search_query) == 0:
        return False

    resp = urlquick.get(SEARCH_API % search_query, params=params, headers=headers)
    items = resp.json()["items"]
    assets = [x['asset'] for x in items]
    for i in list_items(item_id, assets, language):
        yield i


@Route.register
def list_menu_sub_categories(plugin, item_id, menu_category_reference_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(COMPONENT_API % (menu_category_reference_id, COUNTRY))
    json_parser = resp.json()

    for menu_sub_category_data in json_parser["components"]["pageBody"]:
        if 'appSubType' in menu_sub_category_data:
            if 'Curated' in menu_sub_category_data["appSubType"] \
                    or 'TagsQuery' in menu_sub_category_data["appSubType"]:
                menu_sub_category_title = menu_sub_category_data["name"]
                menu_sub_category_reference_id = menu_sub_category_data["referenceId"]

                item = Listitem()
                item.label = menu_sub_category_title
                item.art["thumb"] = get_item_media_path('channels/wo/tv5mondeplus.png')
                item.set_callback(list_programs,
                                  item_id=item_id,
                                  program_reference_id=menu_sub_category_reference_id)
                item_post_treatment(item)
                yield item


@Route.register
def list_programs(plugin, item_id, program_reference_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    language = Script.setting['tv5mondeplus.language']
    resp = urlquick.get(COMPONENT_API % (program_reference_id, COUNTRY))
    json_parser = resp.json()

    new_url = BASE_URL_API + json_parser["contentUrl"]["url"]
    resp2 = urlquick.get(new_url)
    items = resp2.json()["items"]
    for i in list_items(item_id, items, language):
        yield i


def list_items(item_id, items, language):
    for item in items:
        program_title = ''
        program_image = ''
        program_plot = ''
        for localized_data in item["localized"]:
            if language in localized_data["locale"]:
                program_title = localized_data["title"]
                program_plot = localized_data.get("description", "")
                for images_data in localized_data["images"]:
                    if 'poster' in images_data["type"]:
                        program_image = images_data["url"]
        program_asset_id = item["assetId"]
        program_type = item["type"]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.info['plot'] = program_plot
        if 'MOVIE' in program_type:
            item.set_callback(list_video_movie,
                              item_id=item_id,
                              program_asset_id=program_asset_id)
        else:
            item.set_callback(list_seasons,
                              item_id=item_id,
                              program_asset_id=program_asset_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_seasons(plugin, item_id, program_asset_id, **kwargs):
    language = Script.setting['tv5mondeplus.language']

    headers = {
        "User-Agent": GENERIC_HEADERS,
        "Accept": "*/*",
        "Accept-Language": language + ";q=0.8,en-US;q=0.5,en;q=0.3",
        "content-type": "application/json",
        "referrer": "https://www.tv5mondeplus.com/details/vod/redbee:%s" % program_asset_id
    }

    params = {
        'operationName': 'VODContentDetails',
        'variables': '{"contentId":"redbee:%s:%s"}' % (program_asset_id, language),
        'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"%s"}}'
                      % OPERATION_HASHES_WEB['VODContentDetails']
    }
    resp = urlquick.get(GRAPHQL_API, params=params, headers=headers)
    json_parser = resp.json()

    if "PersistedQueryNotFound" in resp.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

    params2 = {
        'operationName': 'VODContentSeasons',
        'variables': '{"contentId":"%s"}' % json_parser["data"]["lookupContent"]["id"],
        'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"%s"}}'
                      % OPERATION_HASHES_WEB['VODContentSeasons']
    }
    resp2 = urlquick.get(GRAPHQL_API, params=params2, headers=headers)
    json_parser2 = resp2.json()

    if "PersistedQueryNotFound" in resp2.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

    for season_data in json_parser2["data"]["lookupContent"]["seasons"]["items"]:
        season_title = 'Season %s' % str(season_data["seasonNumber"])
        season_id = season_data["id"]

        item = Listitem()
        item.label = season_title
        item.set_callback(list_videos_of_season,
                          item_id=item_id,
                          season_id=season_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_of_season(plugin, item_id, season_id, **kwargs):
    language = Script.setting['tv5mondeplus.language']

    headers = {
        "User-Agent": GENERIC_HEADERS,
        "Accept": "*/*",
        "Accept-Language": language + ";q=0.8,en-US;q=0.5,en;q=0.3",
        "content-type": "application/json",
    }

    params = {
        'operationName': 'VODContentEpisodes',
        'variables': '{"contentId":"%s"}' % season_id,
        'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"%s"}}'
                      % OPERATION_HASHES_WEB['VODContentEpisodes']
    }
    resp = urlquick.get(GRAPHQL_API, params=params, headers=headers)
    json_parser = resp.json()

    if "PersistedQueryNotFound" in resp.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

    for video_data in json_parser["data"]["lookupContent"]["episodes"]["items"]:
        video_title = 'Episode %s' % str(video_data["episodeNumber"])
        video_image = video_data["artworks"][0]["source"]
        video_plot = video_data.get("description", '')
        video_id = video_data["externalIds"][0]["identifier"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.set_callback(get_video_url, item_id=item_id, video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item


@Route.register
def list_video_movie(plugin, item_id, program_asset_id, **kwargs):
    language = Script.setting['tv5mondeplus.language']

    headers = {
        "User-Agent": GENERIC_HEADERS,
        "Accept": "*/*",
        "Accept-Language": language + ";q=0.8,en-US;q=0.5,en;q=0.3",
        "content-type": "application/json",
        "referrer": "https://www.tv5mondeplus.com/details/vod/redbee:%s" % program_asset_id
    }

    params = {
        'operationName': 'VODContentDetails',
        'variables': '{"contentId":"redbee:%s:%s"}' % (program_asset_id, language),
        'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"%s"}}'
                      % OPERATION_HASHES_WEB['VODContentDetails']
    }
    resp = urlquick.get(GRAPHQL_API, params=params, headers=headers)
    json_parser = resp.json()

    if "PersistedQueryNotFound" in resp.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

    video_data = json_parser["data"]["lookupContent"]

    video_title = video_data["title"]
    video_image = video_data["artworks"][0]["source"]
    video_plot = video_data.get("description", '')
    video_id = video_data["externalIds"][0]["identifier"]

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
    language = Script.setting['tv5mondeplus.language']

    headers_auth = {
        "User-Agent": GENERIC_HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": language + ";q=0.8,en-US;q=0.5,en;q=0.3",
        "Content-Type": "application/json;charset=utf-8",
    }

    json_body = {
        "device": {
            "deviceId": FAKE_DEVICE_ID,
            "width": 1920,
            "height": 1080,
            "type": "WEB",
            "name": "Windows Mozilla Firefox 97"
        },
        "deviceId": FAKE_DEVICE_ID
    }

    resp = urlquick.post(AUTH_ANONYMOUS_API, json=json_body, headers=headers_auth)
    json_parser = resp.json()

    headers = {
        "User-Agent": GENERIC_HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": language + ";q=0.8,en-US;q=0.5,en;q=0.3",
        'authorization': 'Bearer %s' % json_parser["sessionToken"],
        "referrer": "https://www.tv5mondeplus.com/"
    }

    params = {
        "ifa": FAKE_DEVICE_ID,
        "deviceType": "Desktop",
        "width": "1920",
        "height": "1080",
        "pageUrl": "https%3A%2F%2Fwww.tv5mondeplus.com%2Fplayer%2F" + video_id,
        "domain": "www.tv5mondeplus.com",
        "mute": "false",
        "autoplay": "true"
    }

    resp2 = urlquick.get(URL_STREAM_DATA % video_id, params=params, headers=headers)
    json_parser2 = resp2.json()
    video_url = json_parser2["formats"][0]["mediaLocator"]
    license_url = json_parser2["formats"][0]["drm"]["com.widevine.alpha"]["licenseServerUrl"]
    headers = {
        "User-Agent": GENERIC_HEADERS,
        "Content-Type": ''
    }
    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, headers=headers, manifest_type="mpd", license_url=license_url)
