# -*- coding: utf-8 -*-
# Copyright: (c) 2025
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import binascii
import hashlib
import hmac
import json
import re
import requests
import time
import urlquick
import xbmc
from codequick import Listitem, Script, Resolver, Route
from kodi_six import xbmcvfs

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

OVP_ENDPOINT_URL = 'https://api3.shahid.net/proxy/v2.1/'
CAROUSEL_URL = OVP_ENDPOINT_URL + 'editorial/carousel'
DRM_URL = OVP_ENDPOINT_URL + 'playout/new/drm'
EDITORIAL_PAGE_URL = OVP_ENDPOINT_URL + 'editorial/page'
PLAYLIST_URL = OVP_ENDPOINT_URL + 'product/playlist'
PRODUCT_PLAYOUT_URL = OVP_ENDPOINT_URL + 'playout/new/url/{product_id}'
PREDICTIVE_SEARCH_URL = OVP_ENDPOINT_URL + 't-search'
COUNTRY = 'SA'
PAGE_SIZE = 25
DEFAULT_LANGUAGE = 'EN'
SUPPORTED_LANGUAGES = {'AR', 'EN', 'FR'}


def get_language():
    xbmc_language = xbmc.convertLanguage(xbmc.getLanguage(), xbmc.ISO_639_1).upper()
    return xbmc_language if xbmc_language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def get_basic_headers():
    language = get_language()
    return {
        'language': language,
        'Accept-Language': language.lower(),
    }


def to_yyyy_mm_dd(date):
    try:
        if date and 'T' in date:
            return date.split('T')[0]
    except Exception:
        pass
    return None


def fetch_editorial_page(page_alias: str, profile_folder: str):
    request_payload = {
        'pageAlias': page_alias,
        'profileFolder': profile_folder
    }
    params = {
        'request': json.dumps(request_payload)
    }
    return json.loads(urlquick.get(EDITORIAL_PAGE_URL, headers=get_basic_headers(), params=params, max_age=-1).text)


def get_carousel_json(carousel_id, page_number):
    request_payload = {
        'displayedItems': 0,
        'id': carousel_id,
        'itemsRequestedStatic': True,
        'pageNumber': page_number,
        'pageSize': PAGE_SIZE,
    }

    params = {
        'request': json.dumps(request_payload),
        'country': COUNTRY,
    }

    return json.loads(urlquick.get(CAROUSEL_URL, headers=get_basic_headers(), params=params, max_age=-1).text)


@Route.register(content_type='videos')
def do_search(plugin, search_query):
    params = {
        'request': json.dumps({
            'name': search_query,
            'pageNumber': 0,
            'pageSize': PAGE_SIZE,
        }),
        'exactMatch': 'false',
        'country': COUNTRY,
    }

    search_json = json.loads(
        urlquick.get(PREDICTIVE_SEARCH_URL, headers=get_basic_headers(), params=params, max_age=-1).text)
    if search_json:
        if 'productList' in search_json:
            results = search_json.get('productList', {})
            if results:
                results = results.get('products', [])
                for idx, item in enumerate(results):
                    if item:
                        label = item.get('label')
                        listitem = Listitem()
                        listitem.label = item.get('title')
                        image = item.get('image')
                        listitem.art['thumb'] = listitem.art['landscape'] = web_utils.remove_params(
                            image.get('thumbnailImage'))
                        listitem.art['fanart'] = web_utils.remove_params(item.get('image', {}).get('landscapeClean'))
                        listitem.art['poster'] = web_utils.remove_params(image.get('posterImage'))
                        url = item.get('productUrl', {}).get('url')
                        plot = item.get('description')
                        if label:
                            plot = plot + '\n\n' + label
                        listitem.info['plot'] = plot

                        product_type = item.get('productType')
                        if product_type == 'MOVIE':
                            listitem.info['mediatype'] = 'movie'
                        elif product_type == 'SHOW':
                            listitem.info['mediatype'] = 'tvshow'
                        else:
                            listitem.info['mediatype'] = 'video'

                        if product_type == 'LIVESTREAM' or product_type == 'MOVIE':
                            listitem.set_callback(get_stream, product_id=item['id'])
                        else:
                            listitem.set_callback(list_seasons, url=url)
                        item_post_treatment(listitem)
                        yield listitem


@Route.register
def main_menu(plugin, **kwargs):
    yield Listitem.search(do_search)

    for item in get_category_list_items():
        yield item


def get_category_list_items():
    category_list_items = []
    has_more = True
    page_number = 0
    while has_more:
        carousel_json = get_carousel_json('Main/WW/allchannels/WW-ExploreEdit-All~Guest', page_number)
        has_more = bool(carousel_json.get('hasMore', False))

        editorial_items = carousel_json.get('editorialItems', [])

        for idx, item_wrapper in enumerate(editorial_items, start=1 + page_number * PAGE_SIZE):
            item = item_wrapper.get('item', {})
            title = item.get('title')
            image = web_utils.remove_params(item.get('image', {}).get('squareImage'))
            path = item.get('path', {})
            if title:
                listitem = Listitem()
                listitem.label = title
                listitem.art['thumb'] = listitem.art['landscape'] = image
                listitem.set_callback(list_category, path=path)
                item_post_treatment(listitem)
                category_list_items.append(listitem)
        page_number += 1
    return category_list_items


def is_eligible(item):
    product_type = item.get('productType')
    if product_type == 'LIVESTREAM' or product_type == 'MOVIE':
        for pricing_plan in item.get('pricingPlans', []):
            type = pricing_plan.get('type')
            if type == 'AVOD':
                return True
    else:
        season = item.get('season')
        number_of_avod_episodes = season.get('numberOfAVODEpisodes', 0)
        return number_of_avod_episodes > 1

    return False


@Route.register
def list_category(plugin, path, **kwargs):
    editorial_json = fetch_editorial_page(path, 'WW')
    carousels = editorial_json.get('carousels', [])
    carousel = carousels[0] if carousels else None
    if not carousel:
        raise RuntimeError('Failed to get carousel')
    program_id = carousel.get('id')
    has_more = True
    page_number = 0
    while has_more:
        data = get_carousel_json(program_id, page_number)

        editorial_items = data.get('editorialItems', [])
        has_more = bool(data.get('hasMore', False))

        for idx, item_wrapper in enumerate(editorial_items, start=1 + page_number * PAGE_SIZE):
            item = item_wrapper.get('item', {})
            if is_eligible(item):
                url_item = item.get('productUrl', {}).get('url')
                listitem = Listitem()
                listitem.label = item.get('title')
                listitem.info['plot'] = item.get('description')
                if 'genres' in item and item['genres']:
                    listitem.info['genre'] = [genre['title'].strip() for genre in item['genres']]
                if 'persons' in item and item['persons']:
                    listitem.info['cast'] = [person['fullName'].strip() for person in item['persons']]
                release_date = to_yyyy_mm_dd(item['releaseDate'])
                if release_date:
                    listitem.info.date(release_date, '%Y-%m-%d')
                image = item.get('image', {})
                listitem.art['thumb'] = listitem.art['landscape'] = web_utils.remove_params(image.get('thumbnailImage'))
                listitem.art['fanart'] = web_utils.remove_params(item.get('image', {}).get('landscapeClean'))
                listitem.art['poster'] = web_utils.remove_params(image.get('posterImage'))

                product_type = item.get('productType')
                if product_type == 'MOVIE':
                    listitem.info['mediatype'] = 'movie'
                elif product_type == 'SHOW':
                    listitem.info['mediatype'] = 'tvshow'
                else:
                    listitem.info['mediatype'] = 'video'

                if product_type == 'LIVESTREAM' or product_type == 'MOVIE':
                    listitem.set_callback(get_stream, product_id=item['id'])
                else:
                    listitem.set_callback(list_seasons, url=url_item)
                item_post_treatment(listitem)
                yield listitem
        page_number += 1


@Route.register
def list_seasons(plugin, url, **kwargs):
    page_text = urlquick.get(url, headers=get_basic_headers(), max_age=-1).text
    json_data = json.loads(re.findall(r'type="application/json"[^<>]*>({.*?})</script>', page_text)[0])
    product_model = json_data.get('props', {}).get('pageProps', {}).get('response', {}).get('productModel', {})
    show = product_model.get('show', {})
    image = show.get('image', {})
    for season in sorted(show.get('seasons', []), key=lambda s: int(s['seasonNumber'])):
        playlist = product_model['playlist']
        playlist_id = playlist['id']
        series_number = season['seasonNumber']
        listitem = Listitem()
        listitem.label = show.get('title') + ' (' + str(series_number) + ')'
        listitem.info['plot'] = show.get('description')
        if 'genres' in show and show['genres']:
            listitem.info['genre'] = [genre['title'].strip() for genre in show['genres']]
        if 'persons' in show and show['persons']:
            listitem.info['cast'] = [person['fullName'].strip() for person in show['persons']]
        release_date = to_yyyy_mm_dd(show['releaseDate'])
        if release_date:
            listitem.info.date(release_date, '%Y-%m-%d')
        listitem.art['thumb'] = listitem.art['landscape'] = web_utils.remove_params(image.get('thumbnailImage'))
        listitem.art['fanart'] = web_utils.remove_params(image.get('landscapeClean'))
        listitem.art['poster'] = web_utils.remove_params(image.get('posterImage'))
        listitem.info['mediatype'] = 'season'
        listitem.info['season'] = series_number

        listitem.set_callback(get_episodes_list, playlist_id)
        item_post_treatment(listitem)
        yield listitem


@Route.register
def get_episodes_list(plugin, playlist_id, **kwargs):
    has_more = True
    page_number = 0
    while has_more:
        params = {
            'request': json.dumps({
                'pageNumber': page_number,
                'pageSize': PAGE_SIZE,
                'playListId': playlist_id,
                'isDynamicPlaylist': False,
                'sorts': [
                    {'order': 'DESC', 'type': 'SORTDATE'}
                ],
            }),
            'country': COUNTRY
        }

        data = json.loads(urlquick.get(PLAYLIST_URL, headers=get_basic_headers(), params=params, max_age=-1).text)
        product_list = data.get('productList', {})
        has_more = bool(product_list.get('hasMore', False))
        episodes = product_list.get('products', [])

        for episode in episodes:
            listitem = Listitem()
            title = str(episode.get('number'))
            episode_title = episode.get('title')
            if episode_title and len(episode_title.strip()) > 0:
                title = title + ' - ' + episode_title
            listitem.label = title
            image = episode.get('image', {})
            listitem.art['thumb'] = listitem.art['landscape'] = web_utils.remove_params(image.get('thumbnailImage'))
            listitem.info['duration'] = episode.get('duration')
            listitem.info['plot'] = episode.get('longDescription')
            release_date = to_yyyy_mm_dd(episode.get('releaseDate'))
            if release_date:
                listitem.info.date(release_date, '%Y-%m-%d')
            listitem.info['mediatype'] = 'episode'
            if 'persons' in episode and episode['persons']:
                listitem.info['cast'] = [person['fullName'].strip() for person in episode['persons']]
            show = episode.get('show', {})
            # item.art['poster'] = web_utils.remove_params(show.get('image', {}).get('posterImage'))
            listitem.art['fanart'] = web_utils.remove_params(show.get('image', {}).get('landscapeClean'))
            season = show.get('season', {})
            if season and 'directors' in season and season['directors']:
                listitem.info['director'] = [director['fullName'].strip() for director in season['directors']]
            if season and 'genres' in season and season['genres']:
                listitem.info['genre'] = [genre['title'].strip() for genre in season['genres']]
            listitem.info['season'] = show.get('season', {}).get('seasonNumber')
            listitem.info['episode'] = episode.get('number')
            listitem.set_callback(get_stream, product_id=episode.get('id'))
            item_post_treatment(listitem, is_playable=True, is_downloadable=True)
            yield listitem
        page_number += 1


def generate_authorization(auth_params):
    # https://forum.videohelp.com/threads/414883-Help-download-videos-from-Shahid-MBC#post2739753
    t = 'z3qQSk17nbajIYUF0dU5f4+O/CxjFizcsEJr9ejOYFw='
    i = ';'.join(f'{k}={v}' for k, v in sorted(auth_params.items()))
    return binascii.hexlify(hmac.new(t.encode('utf-8'), i.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')


@Resolver.register
def get_stream(plugin, product_id, **kwargs):
    playout_params = {'outputParameter': 'vmap', 'country': COUNTRY}
    playout_json = json.loads(requests.get(PRODUCT_PLAYOUT_URL.format(product_id=product_id), headers=get_basic_headers(),
                                           params=playout_params).text)

    faults = playout_json.get('faults', [])
    if faults is None:
        raise RuntimeError('Failed to get stream for product_id {}'.format(product_id))
    else:
        errors = '\n'.join(list(map(lambda f: f.get('userMessage', ''), faults)))
        if errors:
            raise RuntimeError(errors)

    playout_json = playout_json.get('playout')
    video_url = playout_json.get('url').split('&')[0]
    video_url = web_utils.remove_params(video_url, check_url=True)  # Remove quality restricting parameters
    if playout_json.get('drm', False):
        drm_params = {
            'request': json.dumps({'assetId': product_id}),
            'ts': int(time.time() * 1000),
            'country': COUNTRY,
        }

        drm_headers = {
            'Authorization': generate_authorization(drm_params),
            'BROWSER_NAME': 'CHROME',
            'BROWSER_VERSION': '142.0',
            'SHAHID_OS': 'WINDOWS',
        }

        drm_response = json.loads(urlquick.get(DRM_URL, headers=drm_headers, params=drm_params, max_age=-1).text)

        status_code = drm_response.get('responseCode', None)
        if status_code == 403:
            raise RuntimeError("Can't access the stream for product_id: {}".format(product_id))

        license_url = drm_response['signature']

        headers = {
            'content-type': 'application/octet-stream'
        }

        return resolver_proxy.get_stream_with_quality(plugin,
                                                      video_url=video_url,
                                                      license_url=license_url,
                                                      headers=headers)
    else:
        return resolver_proxy.get_stream_with_quality(plugin, video_url)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    return get_stream(plugin, item_id, **kwargs)
