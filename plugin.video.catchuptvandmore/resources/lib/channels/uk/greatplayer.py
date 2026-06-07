# -*- coding: utf-8 -*-
# Copyright: (c) 2025
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import json
import requests
import urlquick
import uuid
from builtins import str
from codequick import Listitem, Script, Resolver, Route

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://great-player.com'
ANONYMOUS_TOKEN_URL = URL_ROOT + '/api/core/hello'
PREDICTIVE_SEARCH_URL = URL_ROOT + '/api/core/search'


def get_anonymous_token():
    device_info = {
        'id': str(uuid.UUID(int=uuid.getnode())),
        'hardware': {
            'manufacturer': 'Windows',
            'model': 'Chrome',
            'version': '142.0.0.0',
        },
        'os': {
            'name': 'Windows',
        },
    }

    headers = {
        'x-device-info': json.dumps(device_info),
    }
    data = {
        'deviceInfo': device_info,
    }

    anonymous_token_response = requests.post(ANONYMOUS_TOKEN_URL, headers=headers, json=data)

    if anonymous_token_response.status_code == 200:
        return anonymous_token_response.json()

    return None


COOKIES = {
    'one-token': get_anonymous_token().get('token'),
}


@Route.register
def list_collection(plugin, url, **kwargs):
    collection_json = json.loads(urlquick.get(url, max_age=-1).text)
    if 'data' in collection_json:
        data = collection_json.get('data', [])
        yield from data_to_listitem(data)


@Route.register(content_type='videos')
def do_search(plugin, search_query):
    params = {
        'q': search_query,
        'pageSize': 100,
    }
    search_json = json.loads(urlquick.get(PREDICTIVE_SEARCH_URL, params=params, max_age=-1).text)
    if search_json:
        if 'data' in search_json:
            data = search_json.get('data', [])
            yield from data_to_listitem(data)


def data_to_listitem(data):
    if data:
        for result in data:
            if result:
                listitem = Listitem()
                listitem.label = result.get('title')
                listitem.info['plot'] = result.get('description')
                listitem.info['genre'] = result.get('genres')

                images = result.get('images', {})
                listitem.art['thumb'] = listitem.art['landscape'] = get_image(images, 'thumbnail')
                listitem.art['fanart'] = get_image(images, 'backdrop')
                listitem.art['poster'] = get_image(images, 'poster')

                release_date = result.get('releaseDate')
                if release_date:
                    try:
                        listitem.info.date(release_date.split('T')[0], '%Y-%m-%d')
                    except Exception:
                        pass

                video = result.get('video', {})
                listitem.info['duration'] = video.get('duration')

                type = result.get('type')
                if type == 'ITEM':
                    playback_url = video.get('playback')
                    listitem.set_callback(get_video, url=playback_url)
                elif type == 'COLLECTION':
                    url = result.get('refs', {}).get('self')
                    listitem.set_callback(list_collection, url=url)
                item_post_treatment(listitem)
                yield listitem


def get_image(images, key):
    image_list = images.get(key, {}).get('landscape', [])
    if image_list and image_list[0]:
        return image_list[0].get('url')
    return None


@Route.register
def main_menu(plugin, **kwargs):
    yield Listitem.search(do_search)


@Resolver.register
def get_video(plugin, url, **kwargs):
    json_video = json.loads(urlquick.get(url, cookies=COOKIES, max_age=-1).text)
    video_streams = json_video.get('playbackInfo', {}).get('videoStreams', [])
    for video_stream in video_streams:
        if video_stream.get('streamType') == 'DASH':
            drms = video_stream.get('drms', [])
            for drm in drms:
                if drm.get('type') == 'WIDEVINE':
                    video_url = video_stream.get('url')
                    license_url = drm.get('licenseUrl')
                    return resolver_proxy.get_stream_with_quality(plugin, video_url=video_url, license_url=license_url)
    return None
