# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re
import pytz
import time
from datetime import datetime

import inputstreamhelper
from codequick import Listitem, Resolver, Route
from kodi_six import xbmcgui
import urlquick

from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment
from resources.lib import web_utils

# TO DO

URL_ROOT = 'https://www.npostart.nl'

URL_LIVE_ID = URL_ROOT + '/live/%s'
# Live Id
URL_TOKEN_ID = URL_ROOT + '/player/%s'
# Id video
URL_TOKEN_API = URL_ROOT + '/api/token'
URL_STREAM = 'https://start-player.npo.nl/video/%s/streams'
# Id video, tokenId
URL_SUBTITLE = 'https://rs.poms.omroep.nl/v1/api/subtitles/%s'
# Id Video

URL_API = 'https://start-api.npo.nl'

URL_CATEGORIES = URL_API + '/page/catalogue'
# ApiKey

API_KEY = '07896f1ee72645f68bc75581d7f00d54'

URL_IMAGE = 'https://images.poms.omroep.nl/image/s1280/c1280x720/%s'
# ImageId

GENERIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}


def get_localized_datetime(timestamp):
    try:
        utc_datetime = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
    except TypeError:
        utc_datetime = datetime(*(time.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')[0:6]))

    utc_datetime = pytz.utc.localize(utc_datetime)

    local_timezone = pytz.timezone('Europe/Amsterdam')
    local_datetime = utc_datetime.astimezone(local_timezone)

    return local_datetime


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    params = {'ApiKey': API_KEY}
    resp = urlquick.get(URL_CATEGORIES, params=params, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    for category in json_parser['components'][0]['filters']:
        category_name = category['title']
        category_filter_argument = category['filterArgument']

        item = Listitem()
        item.label = category_name
        item.set_callback(
            list_sub_categories,
            item_id=item_id,
            category_filter_argument=category_filter_argument)
        item_post_treatment(item)
        yield item


@Route.register
def list_sub_categories(plugin, item_id, category_filter_argument, **kwargs):
    params = {'ApiKey': API_KEY}
    resp = urlquick.get(URL_CATEGORIES, params=params, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    for category in json_parser['components'][0]['filters']:
        if category['filterArgument'] and category_filter_argument in category['filterArgument']:
            for sub_category_datas in category['options']:
                sub_category_name = sub_category_datas['display']

                sub_category_value = ''
                if sub_category_datas['value'] is not None:
                    sub_category_value = sub_category_datas['value']

                item = Listitem()
                item.label = sub_category_name
                item.set_callback(
                    list_programs,
                    item_id=item_id,
                    category_filter_argument=category_filter_argument,
                    sub_category_value=sub_category_value,
                    page='1')
                item_post_treatment(item)
                yield item


@Route.register
def list_programs(plugin, item_id, category_filter_argument,
                  sub_category_value, page, **kwargs):

    params = {
        'ApiKey': API_KEY,
        'page': page,
        category_filter_argument: sub_category_value
    }

    resp = urlquick.get(URL_CATEGORIES, params=params, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    for program_datas in json_parser['components'][1]['data']['items']:
        program_title = program_datas['title']

        program_image = ''
        if 'header' in program_datas['images']:
            program_image = URL_IMAGE % program_datas['images']['header']['id']

        program_plot = program_datas['description']
        program_url = program_datas['_links']['page']['href']

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = program_image
        item.info['plot'] = program_plot
        if 'franchise' in program_url:
            item.set_callback(
                list_videos_franchise,
                item_id=item_id,
                program_url=program_url)
        else:
            item.set_callback(
                list_videos_episodes, item_id=item_id, program_url=program_url)

        item_post_treatment(item)
        yield item

    yield Listitem.next_page(
        item_id=item_id,
        category_filter_argument=category_filter_argument,
        sub_category_value=sub_category_value,
        page=str(int(page) + 1))


@Route.register
def list_videos_episodes(plugin, item_id, program_url, **kwargs):
    resp = urlquick.get(program_url + '?ApiKey=%s' % API_KEY)
    json_parser = json.loads(resp.text)

    video_data = json_parser['components'][0]['episode']
    video_title = video_data['title']

    video_image = ''
    if 'header' in video_data['images']:
        video_image = URL_IMAGE % video_data['images']['header']['id']

    video_plot = video_data['description']
    video_id = video_data['id']
    video_duration = video_data['duration']

    broadcast_datetime = get_localized_datetime(video_data['broadcastDate'])
    date_value = broadcast_datetime.strftime('%Y-%m-%d')

    item = Listitem()
    item.label = video_title
    item.art['thumb'] = item.art['landscape'] = video_image
    item.info['plot'] = video_plot
    item.info['duration'] = video_duration
    item.info.date(date_value, '%Y-%m-%d')
    item.set_callback(get_video_url, item_id=item_id, video_id=video_id)
    item_post_treatment(item, is_playable=True, is_downloadable=False)
    yield item


@Route.register
def list_videos_franchise(plugin, item_id, program_url, **kwargs):
    if 'page=' in program_url:
        resp = urlquick.get(program_url + '&ApiKey=%s' % (API_KEY))
        json_parser = json.loads(resp.text)
        response_data = json_parser
    else:
        resp = urlquick.get(program_url.replace('/router', '') + '?ApiKey=%s' % API_KEY)
        json_parser = json.loads(resp.text)
        response_data = json_parser['components'][2]['data']

    # Check if there's a second episode on the same day
    include_time_string = False
    for video_data in response_data['items']:
        broadcast_datetime = get_localized_datetime(video_data['broadcastDate'])

        for ref_video_data in response_data['items']:
            ref_broadcast_datetime = get_localized_datetime(ref_video_data['broadcastDate'])
            if (video_data['episodeTitle'] == ref_video_data['episodeTitle']
                    and video_data['id'] != ref_video_data['id']
                    and broadcast_datetime.strftime('%Y-%m-%d') == ref_broadcast_datetime.strftime('%Y-%m-%d')):

                include_time_string = True
                break

        if include_time_string:
            break

    for video_data in response_data['items']:
        if 'title' not in video_data or not video_data['title']:
            continue

        broadcast_datetime = get_localized_datetime(video_data['broadcastDate'])

        time_string = ''
        if include_time_string:
            time_string = ' (%s)' % broadcast_datetime.strftime('%H:%M')

        subtitle = ''
        if ('seasonNumber' in video_data
                and 'episodeNumber' in video_data
                and video_data['seasonNumber']
                and video_data['episodeNumber']):

            subtitle = ' - S%sE%s' % (
                str(video_data['seasonNumber']),
                str(video_data['episodeNumber']))

        video_title = video_data['title'] + time_string + subtitle

        video_image = ''
        if 'header' in video_data['images']:
            video_image = URL_IMAGE % video_data['images']['header']['id']

        video_plot = video_data['description']
        video_id = video_data['id']
        video_duration = video_data['duration']
        date_value = broadcast_datetime.strftime('%Y-%m-%d')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.info['duration'] = video_duration
        item.info.date(date_value, '%Y-%m-%d')
        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item

    if 'next' in response_data['_links']:
        yield Listitem.next_page(
            item_id=item_id,
            program_url=response_data['_links']['next']['href'])


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    headers = {'X-Requested-With': 'XMLHttpRequest'}

    resp_token = urlquick.get(URL_TOKEN_API, headers=headers, max_age=-1)
    session_token = resp_token.cookies['npo_session']

    json_parser_token = json.loads(resp_token.text)
    api_token = json_parser_token['token']

    # Build PAYLOAD
    payload = {'_token': api_token}
    cookies = {'npo_session': session_token}

    resp = urlquick.post(URL_TOKEN_ID % video_id, cookies=cookies, data=payload, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)
    token_id = json_parser['token']

    params = {
        'profile': 'dash-widevine',
        'quality': 'npo',
        'tokenId': token_id,
        'streamType': 'broadcast',
        'mobile': '0',
        'ios': '0',
        'isChromecast': '0'
    }

    resp = urlquick.get(URL_STREAM % video_id, params=params, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    if 'html' in json_parser and 'Dit programma mag niet bekeken worden vanaf jouw locatie (33).' in json_parser['html']:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    if 'html' in json_parser and 'Dit programma is niet (meer) beschikbaar (15).' in json_parser['html']:
        plugin.notify('ERROR', plugin.localize(30710))
        return False

    licence_url = json_parser['stream']['keySystemOptions'][0]['options']['licenseUrl']
    licence_url_header = json_parser['stream']['keySystemOptions'][0]['options']['httpRequestHeaders']
    xcdata_value = licence_url_header['x-custom-data']

    item = Listitem()
    item.path = json_parser['stream']['src']
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    if plugin.setting.get_boolean('active_subtitle'):
        item.subtitles.append(URL_SUBTITLE % video_id)

    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property[
        'inputstream.adaptive.license_key'] = licence_url + '|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&x-custom-data=%s|R{SSM}|' % xcdata_value

    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if get_kodi_version() < 18:
        xbmcgui.Dialog().ok('Info', plugin.localize(30602))
        return False

    is_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if not is_helper.check_inputstream():
        return False

    headers = {'X-Requested-With': 'XMLHttpRequest'}

    resp_token = urlquick.get(URL_TOKEN_API, headers=headers, max_age=-1)
    session_token = resp_token.cookies['npo_session']

    json_parser_token = json.loads(resp_token.text)
    api_token = json_parser_token['token']

    resp = urlquick.get(URL_LIVE_ID % item_id, headers=GENERIC_HEADERS, max_age=-1)

    video_id = ''
    list_media_id = re.compile(r'media-id\=\"(.*?)\"').findall(resp.text)
    for media_id in list_media_id:
        if 'LI_' in media_id:
            video_id = media_id

    # Build PAYLOAD
    payload = {'_token': api_token}
    cookies = {'npo_session': session_token}

    resp = urlquick.post(URL_TOKEN_ID % video_id, cookies=cookies, data=payload, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)
    token_id = json_parser['token']

    params = {
        'profile': 'dash-widevine',
        'quality': 'npo',
        'tokenId': token_id,
        'streamType': 'broadcast',
        'mobile': '0',
        'ios': '0',
        'isChromecast': '0'
    }
    resp = urlquick.get(URL_STREAM % video_id, params=params, headers=GENERIC_HEADERS, max_age=-1)
    json_parser = json.loads(resp.text)

    if 'html' in json_parser and 'Vanwege uitzendrechten is het niet mogelijk om deze uitzending buiten Nederland te bekijken.' in json_parser['html']:
        plugin.notify('ERROR', plugin.localize(30713))
        return False

    licence_url = json_parser['stream']['keySystemOptions'][0]['options']['licenseUrl']
    licence_url_header = json_parser['stream']['keySystemOptions'][0]['options']['httpRequestHeaders']
    xcdata_value = licence_url_header['x-custom-data']

    item = Listitem()
    item.path = json_parser['stream']['src']
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    if plugin.setting.get_boolean('active_subtitle'):
        item.subtitles.append(URL_SUBTITLE % video_id)

    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.manifest_update_parameter'] = 'full'
    item.property[
        'inputstream.adaptive.license_key'] = licence_url + '|Content-Type=&User-Agent=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3041.0 Safari/537.36&x-custom-data=%s|R{SSM}|' % xcdata_value

    return item
