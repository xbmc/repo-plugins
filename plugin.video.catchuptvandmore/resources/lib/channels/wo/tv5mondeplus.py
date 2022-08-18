# -*- coding: utf-8 -*-
# Copyright: (c) 2016-2020, Team Catch-up TV & More
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json

try:  # Python 3
    from urllib.parse import urlencode
except ImportError:  # Python 2
    from urllib import urlencode

import inputstreamhelper
from codequick import Listitem, Resolver, Route, Script
from kodi_six import xbmcgui
import urlquick

from resources.lib.kodi_utils import (get_kodi_version, get_selected_item_art, get_selected_item_label,
                                      get_selected_item_info, INPUTSTREAM_PROP)
from resources.lib.menu_utils import item_post_treatment

FAKE_DEVICE_ID = "69702f98-260a-ff2d-375c-ffffbf16f78c"

URL_TV5MONDEPLUS_ROOT = 'https://api.tv5mondeplus.com'

API = URL_TV5MONDEPLUS_ROOT + '/v2/whitelabel/customer/TV5MONDE/businessunit/TV5MONDEplus/config/sandwich'

URL_TV5MONDEPLUS_ROOT_API = API + '?onlyPublished=true&allowedCountry=%s'

URL_TV5MONDEPLUS_COMPONENT_API = API + '/component/%s?client=json&onlyPublished=true&allowedCountry=%s'

URL_VIDEOS_DATA = 'https://www.tv5mondeplus.com/api/graphql/v1/'

URL_STREAM_DATA = URL_TV5MONDEPLUS_ROOT + '/v2/customer/TV5MONDE/businessunit/TV5MONDEplus/entitlement/%s/play'
# Video_Id

URL_TV5MONDEPLUS_AUTH_ANONYMOUS_API = URL_TV5MONDEPLUS_ROOT + '/v1/customer/TV5MONDE/businessunit/TV5MONDEplus/auth/anonymous'

# TODO compute hashes instead?
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

# see com.dotscreen.bokit.*Query classes in apk,
# but they don't match queries in web app, queries minifier is not the same?
OPERATION_HASHES_APK = {
    "VODCatalogSection": "04cd97599525e71d64498613bf335a631c2f45c7c7c40101451dac2f7bc8fe76",
    "VODContentDetailsList": "3fe0aac9d078b0f475c0a37a7c71c4e2743e084241e9a9c6fea34e784446a5e7",
    "VODContentDetails": "4ade60432f176b60ac314bf6bec7601e2ea7ca4d4e162887ff41766fedfc1caa",
    "VODContentEpisodes": "3a9eaeea6e03e802fa9399e562efb813d5381604ddce71b34a43cb3e3a1cc02f",
    "VODContentOffers": "1cc9bef4009e32f4c1b6ce048f579f5941cc2df6156a19e5468c3e688b2414d0",
    "VODContentSearch": "0bad359d056555d22f085626ae4d77aadf771746631856869ad8025006e09bca",
    "VODContentSeasons": "7cdf52b778bf9795d7ffb59b76954b464583ede5b19baff28c23ac8e6df196ea",
    "VODPlaybackInfos": "3adb119aaf31bb1a7b1bcc9ee35363fec01a2907f0b6d8ce6a7475a0ad89e256",
    "VODSearchAutocomplete": "0a2db2d986574da358faad165e0339158add13e8fafacec30a2c4fa51210ad0e",
    "VODSectionItems": "63d4e1b1735bddb661d532c3a551a630827af6b58cdf74ec53ecb0d63f14161d",
    "VODSectionSubsections": "9419515f8ea16d402397f4dfbe72c49b62771205a8243e2bb0e3cbbe1c153626",
    "VODTopLevelServices": "5e15d32bbb9c4b2e739223e1c10fb1a1b2e1d3a0a8542bd561700f270029c2e4"
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
    country = Script.setting['tv5mondeplus.country']
    resp = urlquick.get(URL_TV5MONDEPLUS_ROOT_API % country)
    json_parser = resp.json()
    category_reference_id = json_parser["components"]["menu"][0]["referenceId"]

    resp2 = urlquick.get(URL_TV5MONDEPLUS_COMPONENT_API % (category_reference_id, country))
    json_parser2 = resp2.json()

    for menu_category_datas in json_parser2["components"]["menuItems"]:
        if 'appSubType' in menu_category_datas:
            if 'Component' in menu_category_datas["appSubType"]:
                if "" == menu_category_datas["presentation"]["fallback"]["title"]:
                    menu_category_title = json_parser["components"]["homePage"][0]["name"]
                else:
                    menu_category_title = menu_category_datas["presentation"]["fallback"]["title"]
                menu_category_reference_id = menu_category_datas["actions"]["default"]["componentId"]

                item = Listitem()
                item.label = menu_category_title
                item.set_callback(list_menu_sub_categories,
                                  item_id=item_id,
                                  menu_category_reference_id=menu_category_reference_id)
                item_post_treatment(item)
                yield item


@Route.register
def list_menu_sub_categories(plugin, item_id, menu_category_reference_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    country = Script.setting['tv5mondeplus.country']
    resp = urlquick.get(URL_TV5MONDEPLUS_COMPONENT_API % (menu_category_reference_id, country))
    json_parser = resp.json()

    for menu_sub_category_datas in json_parser["components"]["pageBody"]:
        if 'appSubType' in menu_sub_category_datas:
            if 'Curated' in menu_sub_category_datas["appSubType"] \
                    or 'TagsQuery' in menu_sub_category_datas["appSubType"]:
                menu_sub_category_title = menu_sub_category_datas["name"]
                menu_sub_category_reference_id = menu_sub_category_datas["referenceId"]

                item = Listitem()
                item.label = menu_sub_category_title
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
    country = Script.setting['tv5mondeplus.country']
    language = Script.setting['tv5mondeplus.language']
    resp = urlquick.get(URL_TV5MONDEPLUS_COMPONENT_API % (program_reference_id, country))
    json_parser = resp.json()

    new_url = URL_TV5MONDEPLUS_ROOT + json_parser["contentUrl"]["url"]
    resp2 = urlquick.get(new_url)
    json_parser2 = resp2.json()

    for program_datas in json_parser2["items"]:
        program_title = ''
        program_image = ''
        program_plot = ''
        for localized_datas in program_datas["localized"]:
            if language in localized_datas["locale"]:
                program_title = localized_datas["title"]
                program_plot = localized_datas["description"]
                for images_datas in localized_datas["images"]:
                    if 'poster' in images_datas["type"]:
                        program_image = images_datas["url"]
        program_asset_id = program_datas["assetId"]
        program_type = program_datas["type"]

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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        "Accept": "*/*",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "content-type": "application/json",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "referrer": "https://www.tv5mondeplus.com/details/vod/redbee:%s" % program_asset_id
    }

    params = {
        'operationName': 'VODContentDetails',
        'variables': '{"contentId":"redbee:%s:%s"}' % (program_asset_id, language),
        'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"%s"}}'
                      % OPERATION_HASHES_WEB['VODContentDetails']
    }
    resp = urlquick.get(URL_VIDEOS_DATA, params=params, headers=headers)
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
    resp2 = urlquick.get(URL_VIDEOS_DATA, params=params2, headers=headers)
    json_parser2 = resp2.json()

    if "PersistedQueryNotFound" in resp2.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        "Accept": "*/*",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "content-type": "application/json",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }

    params = {
        'operationName': 'VODContentEpisodes',
        'variables': '{"contentId":"%s"}' % season_id,
        'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"%s"}}'
                      % OPERATION_HASHES_WEB['VODContentEpisodes']
    }
    resp = urlquick.get(URL_VIDEOS_DATA, params=params, headers=headers)
    json_parser = resp.json()

    if "PersistedQueryNotFound" in resp.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

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
def list_video_movie(plugin, item_id, program_asset_id, **kwargs):
    language = Script.setting['tv5mondeplus.language']

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        "Accept": "*/*",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "content-type": "application/json",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "referrer": "https://www.tv5mondeplus.com/details/vod/redbee:%s" % program_asset_id
    }

    params = {
        'operationName': 'VODContentDetails',
        'variables': '{"contentId":"redbee:%s:%s"}' % (program_asset_id, language),
        'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"%s"}}'
                      % OPERATION_HASHES_WEB['VODContentDetails']
    }
    resp = urlquick.get(URL_VIDEOS_DATA, params=params, headers=headers)
    json_parser = resp.json()

    if "PersistedQueryNotFound" in resp.text:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False

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

    headers_auth = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "Content-Type": "application/json;charset=utf-8",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
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

    resp = urlquick.post(URL_TV5MONDEPLUS_AUTH_ANONYMOUS_API, json=json_body, headers=headers_auth)
    json_parser = resp.json()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        'authorization': 'Bearer %s' % json_parser["sessionToken"],
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
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

    item = Listitem()
    item.path = json_parser2["formats"][0]["mediaLocator"]
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'

    header_license = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0",
        "Accept": "*/*",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "referrer": "https://www.tv5mondeplus.com/"
    }

    license_server_url = json_parser2["formats"][0]["drm"]["com.widevine.alpha"]["licenseServerUrl"]
    item.property['inputstream.adaptive.license_key'] = '%s|%s|R{SSM}|' \
                                                        % (license_server_url, urlencode(header_license))
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    return item
