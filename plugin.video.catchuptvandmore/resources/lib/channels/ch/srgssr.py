# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import datetime
import json
import re

import inputstreamhelper
from codequick import Listitem, Resolver, Route, Script
from kodi_six import xbmcgui
import urlquick

from resources.lib import download, web_utils, resolver_proxy
from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info
from resources.lib.menu_utils import item_post_treatment

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote


# TO DO and Infos
# Add More Video_button (for emissions)
# Add Quality Mode / test Download Mode

URL_ROOT = 'https://www.%s.ch'
# channel_name

# Replay
URL_CATEGORIES_JSON = 'https://www.%s.ch/play/tv/'
# channel_name

URL_SHOWLIST = 'https://il.srgssr.ch/integrationlayer/2.0/%s/showList/tv/alphabetical'
# channel_name, name_emission

URL_LIST_EPISODES = 'https://www.%s.ch/play/v3/api/%s/production/videos-by-show-id'
# channel_name, channel_name, IdEmission

URL_LIST_VIDEOS = 'https://www.%s.ch/play/v3/api/%s/production/%s'
# channel_name, channel_name, SectionId

# search items
URL_LIST_SEARCH = 'https://il.srgssr.ch/integrationlayer/2.0/%s/searchResultShowList'

# Live
URL_LIVE_JSON = 'https://www.%s.ch/play/v3/api/%s/production/tv-livestreams'
# channel_name, channel_name

URL_TOKEN = 'https://tp.srgssr.ch/akahd/token'
# acl

URL_BYTOPICURN = 'https://il.srgssr.ch/integrationlayer/2.0/%s/page/byTopicUrn/%s'
URL_TOPIC = 'https://il.srgssr.ch/integrationlayer/2.0/%s/topicList/tv'
URL_INFO_VIDEO = 'https://il.srgssr.ch/integrationlayer' \
                 '/2.0/mediaComposition/byUrn/urn:%s:video:%s.json'

URL_LICENCE_KEY = '%s|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&Host=srg.live.ott.irdeto.com|R{SSM}|'
GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}

# channel_name, video_id
EMISSIONS_NAME = {
    'rts': ['Émissions', 'emissions'],
    'rsi': ['Programmi', 'programmi'],
    'rtr': ['Emissiuns', 'emissiuns'],
    'srf': ['Sendungen', 'sendungen']
}

LIVE_LIVE_CHANNEL_NAME = {
    "rtsun": "RTS 1",
    "rtsdeux": "RTS 2",
    "rtsinfo": "RTS Info",
    "rtscouleur3": "RTS Couleur 3",
    "rsila1": "La 1",
    "rsila2": "La 2",
    "srf1": "SRF 1",
    "srfinfo": "SRF info",
    "srfzwei": "SRF zwei",
    "rtraufsrf1": "RTR auf SRF 1",
    "rtraufsrfinfo": "RTR auf SRF Info",
    "rtraufsrf2": "RTR auf SRF 2"
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
    if item_id != 'swissinfo':
        # search items
        item = Listitem.search(list_search, item_id=item_id, page='0')
        item_post_treatment(item)
        yield item

        # Emission
        category = EMISSIONS_NAME[item_id]

        item = Listitem()
        item.label = category[0]
        item.set_callback(list_programs,
                          item_id=item_id)
        item_post_treatment(item)
        yield item
    else:
        item = Listitem()
        item.label = Script.localize(30896)
        item_post_treatment(item)
        yield item
        return False

    # Other categories (Info, Kids, ...)
    params = {'vector': 'TVPLAY', }
    resp = urlquick.get(URL_TOPIC % item_id, params=params, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    for category_datas in json_parser["topicList"]:
        category_title = category_datas["title"]
        category_image = ''
        if 'imageUrl' in category_datas:
            if 'rts.ch' in category_datas["imageUrl"]:
                category_image = category_datas["imageUrl"] + \
                    '/scale/width/448'
            else:
                category_image = category_datas["imageUrl"]
        category_urn = category_datas['urn']

        item = Listitem()
        item.label = category_title
        item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = category_image
        item.set_callback(list_sub_categories,
                          item_id=item_id,
                          category_urn=category_urn)
        item_post_treatment(item)
        yield item


@Route.register
def list_sub_categories(plugin, item_id, category_urn, **kwargs):
    params = {'isPublished': 'true', 'vector': 'TVPLAY', }
    resp = urlquick.get(URL_BYTOPICURN % (item_id, category_urn), params=params, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    for sub_category_datas in json_parser['sectionList']:
        section_id = sub_category_datas['id']
        section_type = sub_category_datas['sectionType']

        sub_category_title = ''
        if 'title' in sub_category_datas["representation"]['properties']:
            sub_category_title = sub_category_datas["representation"]['properties']["title"]
        else:
            continue
        sub_category_desc = ''
        if 'description' in sub_category_datas["representation"]['properties']:
            sub_category_desc = sub_category_datas["representation"]['properties']["description"]
        sub_category_image = ''
        if 'imageUrl' in sub_category_datas["representation"]['properties']:
            sub_category_image = sub_category_datas["representation"]['properties']["imageUrl"]

        item = Listitem()
        item.label = sub_category_title
        item.info['plot'] = sub_category_desc
        item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = sub_category_image
        item.set_callback(list_videos_category,
                          item_id=item_id,
                          section_type=section_type,
                          section_id=section_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    params = {'pageSize': 'unlimited', 'vector': 'TVPLAY', }
    resp = urlquick.get(URL_SHOWLIST % item_id, params=params, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    for program_datas in json_parser['showList']:
        program_title = program_datas["title"]
        if 'rts.ch' in program_datas["imageUrl"]:
            program_image = program_datas["imageUrl"] + '/scale/width/448'
        else:
            program_image = program_datas["imageUrl"]
        program_id = program_datas["id"]

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = program_image
        item.set_callback(list_videos_program,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_category(plugin, item_id, section_type, section_id, next_value=None, **kwargs):
    if section_type == 'MediaSection':
        url_videos_datas = URL_LIST_VIDEOS % (item_id, item_id[:3], 'media-section')
    elif section_type == 'MediaSectionWithShow':
        url_videos_datas = URL_LIST_VIDEOS % (item_id, item_id[:3], 'media-section-with-show')
    elif section_type == 'ShowSection':
        url_videos_datas = URL_LIST_VIDEOS % (item_id, item_id[:3], 'show-section')
    else:
        return False

    if next_value is not None:
        payload = {'sectionId': section_id, 'preview': 'false', 'next': next_value}
    else:
        payload = {'sectionId': section_id, 'preview': 'false'}

    if item_id == 'swissinfo':
        url_videos_datas = url_videos_datas.replace('www', 'play')

    resp = urlquick.get(url_videos_datas, params=payload, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    if section_type == 'ShowSection':
        for video_datas in json_parser["data"]:
            video_title = video_datas['title']
            if video_title == "default_Showpage_RTS":
                continue
            video_plot = ''
            video_image = video_datas["imageUrl"] + '/scale/width/448'
            video_id = video_datas["id"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = video_image
            item.info['plot'] = video_plot
            item.set_callback(list_videos_program,
                              item_id=item_id,
                              program_id=video_id)
            item_post_treatment(item)
            yield item
    elif section_type == 'MediaSectionWithShow':
        for video_datas in json_parser["data"]["medias"]:
            video_title = video_datas['title']
            if "seasonNumber" in video_datas:
                video_title = 'S' + str(video_datas["seasonNumber"]) + 'E' + str(video_datas["episodeNumber"]) + ' - ' + video_title
            if 'show' in video_datas:
                video_title = video_datas['show']['title'] + ' - ' + video_title
            video_plot = ''
            if 'description' in video_datas:
                video_plot = video_datas["description"]
            video_image = video_datas["imageUrl"] + '/scale/width/448'
            video_id = video_datas["id"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = video_image
            item.info['plot'] = video_plot
            item.info['duration'] = video_datas['duration'] / 1000
            item.info.date(video_datas['date'].split('T')[0], "%Y-%m-%d")
            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item
    else:
        for video_datas in json_parser["data"]["data"]:
            video_title = video_datas['title']
            if "seasonNumber" in video_datas:
                video_title = 'S' + str(video_datas["seasonNumber"]) + 'E' + str(video_datas["episodeNumber"]) + ' - ' + video_title
            if 'show' in video_datas:
                video_title = video_datas['show']['title'] + ' - ' + video_title
            video_plot = ''
            if 'description' in video_datas:
                video_plot = video_datas["description"]
            video_image = video_datas["imageUrl"] + '/scale/width/448'
            video_id = video_datas["id"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = video_image
            item.info['plot'] = video_plot
            item.info['duration'] = video_datas['duration'] / 1000
            item.info.date(video_datas['date'].split('T')[0], "%Y-%m-%d")
            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    if 'next' in json_parser["data"]:
        yield Listitem.next_page(item_id=item_id, section_type=section_type, section_id=section_id, next_value=json_parser['data']['next'])


@Route.register
def list_videos_program(plugin, item_id, program_id, next_value=None, **kwargs):
    if next_value is not None:
        payload = {'showId': program_id, 'next': next_value}
    else:
        payload = {'showId': program_id}
    resp = urlquick.get(URL_LIST_EPISODES % (item_id, item_id), params=payload, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    if len(json_parser["data"]["data"]) == 0:
        item = Listitem()
        item.label = Script.localize(30896)
        item_post_treatment(item)
        yield item
    else:
        for video_datas in json_parser["data"]["data"]:
            video_title = video_datas['title']
            if "seasonNumber" in video_datas:
                video_title = 'S' + str(video_datas["seasonNumber"]) + 'E' + str(video_datas["episodeNumber"]) + ' - ' + video_title
            if 'show' in video_datas:
                video_title = video_datas['show']['title'] + ' - ' + video_title
            video_plot = ''
            if 'description' in video_datas:
                video_plot = video_datas["description"]
            video_image = video_datas["imageUrl"] + '/scale/width/448'
            video_id = video_datas["id"]

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = video_image
            item.info['plot'] = video_plot
            item.info['duration'] = video_datas['duration'] / 1000
            item.info.date(video_datas['date'].split('T')[0], "%Y-%m-%d")
            item.set_callback(get_video_url,
                              item_id=item_id,
                              video_id=video_id)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

        if 'next' in json_parser["data"]:
            yield Listitem.next_page(item_id=item_id, program_id=program_id, next_value=json_parser['data']['next'])


@Route.register
def list_search(plugin, search_query, item_id, page, **kwargs):
    params = {
        'q': search_query,
        'mediaType': 'video',
        'pageSize': '20',
        'vector': 'portalplay'
    }
    resp = urlquick.get(URL_LIST_SEARCH % item_id[:3], params=params, headers=GENERIC_HEADERS, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    found_result = False
    for program_datas in json_parser["searchResultShowList"]:
        program_title = program_datas["title"]
        program_plot = ''
        if 'description' in program_datas:
            program_plot = program_datas["description"]
        if 'rts.ch' in program_datas["imageUrl"]:
            program_image = program_datas["imageUrl"] + '/scale/width/448'
        else:
            program_image = program_datas["imageUrl"]
        program_id = program_datas["id"]

        item = Listitem()
        item.label = program_title
        item.info['plot'] = program_plot
        item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = program_image
        item.set_callback(list_videos_program,
                          item_id=item_id,
                          program_id=program_id)
        item_post_treatment(item)
        found_result = True
        yield item

    if not found_result:
        plugin.notify(plugin.localize(30600), plugin.localize(30718))
        yield False


@Resolver.register
def get_video_url(plugin, item_id, video_id, download_mode=False, **kwargs):
    if item_id == 'swissinfo':
        channel_name_value = 'swi'
    else:
        channel_name_value = item_id
    params = {
        'onlyChapters': 'false',
        'vector': 'portalplay'
    }
    url_video = URL_INFO_VIDEO % (channel_name_value, video_id)
    resp = urlquick.get(url_video, headers=GENERIC_HEADERS, params=params, max_age=-1).content.decode()
    json_parser = json.loads(resp)

    # build stream_url
    subtitle_url = None
    protocol, final_video_url, license_url = get_final_video_url(plugin, json_parser, video_id)

    if final_video_url is None:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    return resolver_proxy.get_stream_with_quality(
        plugin, video_url=final_video_url, manifest_type=protocol,
        subtitles=subtitle_url, license_url=license_url)


def get_final_video_url(plugin, video_assets, video_id):
    RES_PRIORITY = {"sd": 0, "hd": 1}

    chapter = list(filter(lambda c: c["urn"] == video_id, video_assets.get("chapterList", [])))
    if len(chapter) > 0:
        chapter = chapter[0]
    else:
        chapter = video_assets.get("chapterList", [])[0]

    resources = chapter.get("resourceList", [])
    if len(resources) == 0:
        return None, None, None

    resources = list(filter(lambda r: r['protocol'].lower() in ['hls', 'mpd', 'ism', 'dash'], resources))
    resources = sorted(resources, key=lambda r: RES_PRIORITY[r["quality"].lower()], reverse=True)
    content_resource = None
    license_url = None

    for resource in resources:
        protocol = resource.get("protocol", None).lower()
        if protocol == "dash" or protocol == "dash-dvr":
            protocol = "mpd"
        if protocol == "hls-dvr":
            protocol = "hls"

        drm_list = resource.get("drmList", None)
        is_drm = drm_list not in ["", None, []] and type(drm_list) is list

        if is_drm:
            for drm in drm_list:
                if drm.get("type", "").lower() == "widevine":
                    content_resource = resource
                    license_url = drm["licenseUrl"]
                    break
        else:
            content_resource = resource
        if content_resource is not None:
            break

    if content_resource is None:
        return None, None, None

    resource = content_resource
    manifest = resource["url"]
    acl = manifest.split("//")[1].split("?")[0]
    acl = re.search(r"(/.+/)", acl).group(1) + "*"
    resp = urlquick.get(URL_TOKEN, params={"acl": acl}, headers=GENERIC_HEADERS, max_age=-1)
    response = json.loads(resp.content.decode())
    if "?" not in manifest:
        manifest += "?"
    else:
        manifest += "&"

    auth_params = response["token"]["authparams"].split("&")
    temp_params = {}
    for p in auth_params:
        index = p.index("=")
        temp_params[p[0:index]] = quote(p[index + 1:], safe='')
    auth_params = '&'.join([
        f'{k}={v}' for k, v in temp_params.items()
    ]).replace("~", "%7E")

    manifest += auth_params
    manifest_content = urlquick.get(manifest, max_age=-1).content.decode()
    if ">access denied<" in manifest_content.lower():
        return None, None, None

    if license_url is not None:
        license_key = URL_LICENCE_KEY % license_url
    else:
        license_key = None

    return protocol, manifest, license_key


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_LIVE_JSON % (item_id[:3], item_id[:3]), headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    live_id = ''
    for live_datas in json_parser["data"]:
        if live_datas["title"] in LIVE_LIVE_CHANNEL_NAME[item_id]:
            live_id = live_datas["id"]
    if live_id is None:
        # Add Notification
        return False

    params = {
        'onlyChapters': 'false',
        'vector': 'portalplay'
    }

    resp = urlquick.get(URL_INFO_VIDEO % (item_id[:3], live_id), headers=GENERIC_HEADERS, params=params, max_age=-1)
    json_parser = json.loads(resp.text)

    subtitle_url = None
    protocol, final_video_url, license_url = get_final_video_url(plugin, json_parser, live_id)

    if final_video_url is None:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    return resolver_proxy.get_stream_with_quality(
        plugin, video_url=final_video_url, manifest_type=protocol,
        subtitles=subtitle_url, license_url=license_url)
