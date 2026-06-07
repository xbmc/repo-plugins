# -*- coding: utf-8 -*-
# Copyright: (c) 2025, Jeff2900
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import base64
import re
import json
import uuid

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'https://novo19.ouest-france.fr'
URL_CATEGORIES = URL_ROOT + '/categories'
URL_CATEGORIES_PLUS = URL_ROOT + '/voir-plus/rail/categories/'
REDBEE_BASE_URL = 'https://exposure.api.redbee.live/v2/customer/OuestFrance/businessunit/novoplus'

PATTERN_KEY_ID = re.compile(r"([a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}_[a-f\d]{7})", re.IGNORECASE)
DEVICEID = str(uuid.UUID(int=uuid.getnode()))
GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Nos documentaires et magazines
    - Nos films
    - ...
    """
    response = urlquick.get(URL_CATEGORIES, headers=GENERIC_HEADERS, max_age=-1)
    root = response.parse("script", attrs={"id": "__NEXT_DATA__"})
    json_parser = json.loads(root.text)

    for category_datas in json_parser['props']['pageProps']['serverData']['page']['rails']:
        category_title = category_datas.get('title')
        if category_title is None or category_title == "Nos podcasts":
            continue

        category_type = category_datas.get('type')
        if category_type == 'CAROUSEL':
            category_id = URL_CATEGORIES_PLUS + category_datas.get('id')
            category_image = category_datas.get('src')

            item = Listitem()
            item.label = category_title
            item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = category_image
            item.set_callback(list_programs,
                              category_url=category_id)
            item_post_treatment(item)
            yield item


@Route.register
def list_programs(plugin, category_url, **kwargs):
    """
    Build programs listing
    - Journal de 20H
    - Cash investigation
    """
    response = urlquick.get(category_url, headers=GENERIC_HEADERS, max_age=-1)
    root = response.parse("script", attrs={"id": "__NEXT_DATA__"})
    json_parser = json.loads(root.text)

    for key, value in json_parser['props']['pageProps']['initialState']['api']['queries'].items():
        if key[:7] == 'bffTile':
            for program_datas in value['data']['tiles']:
                program_id = program_datas.get('id')
                if program_id is None:
                    continue
                program_type = program_datas.get('type')
                program_url = URL_ROOT + program_datas.get('href')
                program_title = program_datas.get('title')
                program_subtitle = program_datas.get('subtitle')
                program_desc = program_datas.get('description')
                program_image = program_datas['thumbnail'].get('src')
                program_date = program_datas.get('releaseDate')
                program_duration = program_datas.get('durarion')

                if program_subtitle:
                    program_label = program_subtitle + ' - ' + program_title
                else:
                    program_label = program_title

                item = Listitem()
                item.label = program_label
                item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = program_image
                if program_desc:
                    item.info['plot'] = program_desc
                if program_date:
                    item.info['year'] = program_date
                if program_duration:
                    item.info['duration'] = program_duration
                if program_type == 'SERIE':
                    item.set_callback(list_seasons,
                                      video_url=program_url)
                else:
                    item.set_callback(get_video_url,
                                      video_id=program_id)
                item_post_treatment(item)
                yield item


@Route.register
def list_seasons(plugin, video_url, **kwargs):
    response = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)
    root = response.parse("script", attrs={"id": "__NEXT_DATA__"})
    json_parser = json.loads(root.text)
    at_least_one_item = False

    for seasons in json_parser['props']['pageProps']['serverData']['page']['rails']:
        season_id = seasons.get('id')
        if season_id == 'reco':
            continue
        season_title = seasons.get('title')
        season_image = seasons.get('src')

        at_least_one_item = True
        item = Listitem()
        item.label = season_title
        item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = season_image
        item.set_callback(list_videos,
                          video_url=video_url,
                          season=season_id)
        item_post_treatment(item)
        yield item

    # No season
    if at_least_one_item is False:
        video_id = json_parser['props']['pageProps']['serverData']['page']['content'].get('id')
        video_title = json_parser['props']['pageProps']['serverData']['page']['content'].get('title')
        video_desc = json_parser['props']['pageProps']['serverData']['page']['content'].get('description')
        video_image = json_parser['props']['pageProps']['serverData']['page']['content']['background'].get('src')
        video_date = json_parser['props']['pageProps']['serverData']['page']['content'].get('releaseDate')
        video_duration = json_parser['props']['pageProps']['serverData']['page']['content'].get('duration')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = video_image
        if video_desc:
            item.info['plot'] = video_desc
        if video_date:
            item.info['year'] = video_date
        if video_duration:
            item.info['duration'] = video_duration
        item.set_callback(get_video_url,
                          video_id=video_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, video_url, season, **kwargs):
    response = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)
    root = response.parse("script", attrs={"id": "__NEXT_DATA__"})
    json_parser = json.loads(root.text)
    video_url_all = None
    for key, value in json_parser['props']['pageProps']['initialState']['api']['queries'].items():
        if key[:7] == 'bffTile':
            found_items = PATTERN_KEY_ID.findall(key)
            if len(found_items) == 0 or found_items[len(found_items) - 1] != season:
                continue
            for videos_datas in value['data']['tiles']:
                video_id = videos_datas.get('id')
                if video_id is None:
                    continue
                video_title = videos_datas.get('title')
                video_subtitle = videos_datas.get('subtitle')
                video_desc = videos_datas.get('description')
                video_image = videos_datas['thumbnail'].get('src')
                video_date = videos_datas.get('releaseDate')
                video_duration = videos_datas.get('duration')
                if value['data'].get('more'):
                    video_url_all = URL_ROOT + value['data']['more'].get('href')

                item = Listitem()
                item.label = video_subtitle + ' - ' + video_title
                item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = video_image
                if video_desc:
                    item.info['plot'] = video_desc
                if video_date:
                    item.info['year'] = video_date
                if video_duration:
                    item.info['duration'] = video_duration
                item.set_callback(get_video_url,
                                  video_id=video_id)
                item_post_treatment(item)
                yield item

    if video_url_all:
        yield Listitem.next_page(video_url=video_url_all,
                                 season=season)


@Resolver.register
def get_video_url(plugin, video_id):
    return get_video_redbee(plugin, video_id, is_drm=True)


def get_redbee_token():
    json_data = {
        'device': {
            'name': 'Browser',
            'type': 'WEB',
        },
        'deviceId': DEVICEID,
    }
    response = urlquick.post(REDBEE_BASE_URL + '/auth/anonymous', headers=GENERIC_HEADERS, json=json_data, max_age=-1).json()
    if response.get('sessionToken'):
        return True, response.get('sessionToken')
    else:
        return False, None


@Route.register
def get_video_redbee(plugin, video_id, is_drm):
    is_ok, session_token = get_redbee_token()
    if is_ok is False:
        return False

    video_format, forced_drm = get_redbee_format(plugin, video_id, session_token, is_drm)
    if video_format is None:
        return False

    video_url = video_format['mediaLocator']

    if not is_drm and not forced_drm:
        if re.match('.*m3u8.*', video_url) is not None:
            return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="hls")
        return video_url

    certificate_data = None
    if 'drm' in video_format:
        license_server_url = video_format['drm']['com.widevine.alpha']['licenseServerUrl']
        certificate_url = video_format['drm']['com.widevine.alpha'].get('certificateUrl')
        if len(certificate_url) > 0:
            resp_cert = urlquick.get(certificate_url, headers=GENERIC_HEADERS, max_age=-1).text
            certificate_data = base64.b64encode(resp_cert.encode("utf-8")).decode("utf-8")
    else:
        return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type="mpd")

    # TODO subtitles?
    # subtitles = video_format['sprites'][0]['vtt']

    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'Content-Type': ''
    }

    input_stream_properties = {}
    if certificate_data is not None:
        input_stream_properties = {"server_certificate": certificate_data}

    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, manifest_type='mpd', headers=headers,
                                                  license_url=license_server_url,
                                                  input_stream_properties=input_stream_properties)


def get_redbee_format(plugin, media_id, session_token, is_drm):
    url = REDBEE_BASE_URL + '/entitlement/{}/play'.format(media_id)

    headers = {
        'User-Agent': web_utils.get_random_ua(),
        'authorization': 'Bearer {}'.format(session_token)
    }
    response = urlquick.get(url, headers=headers, max_age=-1, raise_for_status=False)
    if response.status_code != 200:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return None, True

    json_paser = json.loads(response.text)
    formats = json_paser['formats']

    if not is_drm:
        for fmt in formats:
            if fmt['format'] == 'HLS' and 'drm' not in fmt:
                return fmt, is_drm

    # all formats have drm, switch to DASH
    for fmt in formats:
        if fmt['format'] == 'DASH':
            return fmt, True

    return None, True


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    return get_video_redbee(plugin, 'novo19_565BFFb', is_drm=True)
