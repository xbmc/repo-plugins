# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
from datetime import datetime
import importlib
import json
import os
import urlquick
from codequick import Listitem, Resolver, Route, Script
from codequick.storage import Cache
from kodi_six import xbmcgui
from resources.lib import resolver_proxy
from resources.lib.addon_utils import get_item_media_path
from resources.lib.menu_utils import item_post_treatment
from resources.lib.main import tv_guide_menu

CACHE_FILE = os.path.join(Route.get_info("profile"), u".sfrtv_cache.sqlite")
USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 '
              'Safari/537.36')  # fixed as the list of connected devices is limited
TOKEN_MAX_AGE = 840  # 14 minutes to be under the 15 mn token validity limit
CONFIG_URL = 'https://tv.sfr.fr/configs/config.json'
LOGIN_URL = 'https://www.sfr.fr/cas/login'
ACCESS_TOKEN_URL = 'https://www.sfr.fr/cas/oidc/authorize'
USER_PROFILE_URL = 'https://ws-backendtv.sfr.fr/heimdall-core/public/api/v2/userProfiles'
SERVICE_URL = 'https://ws-backendtv.sfr.fr/sekai-service-plan/public/v2/service-list'
LICENSE_URL = 'https://ws-backendtv.sfr.fr/asgard-drm-widevine/public/licence'
MENU_STRUCTURE_URL = 'https://ws-cdn.tv.sfr.net/gaia-core/rest/api/web/v2/menu/{}/structure'
SPOT_CONTENT_URL = 'https://ws-backendtv.sfr.fr/gaia-core/rest/api/web/v2/spot/{}/content'
SPOT_MORE_URL = 'https://ws-backendtv.sfr.fr/gaia-core/rest/api/web/v2/spot/{}/more'
TILE_CONTENT_URL = 'https://ws-backendtv.sfr.fr/gaia-core/rest/api/web/v2/tile/{}/content'
STORE_CATEGORIES_URL = 'https://ws-cdn.tv.sfr.net/gaia-core/rest/api/web/v1/stores/{}/categories'
CATEGORY_CONTENTS_URL = 'https://ws-cdn.tv.sfr.net/gaia-core/rest/api/web/v2/categories/{}/contents'
CONTENT_DETAILS_URL = 'https://ws-cdn.tv.sfr.net/gaia-core/rest/api/web/v1/content/{}/detail'
CONTENT_EPISODES_URL = 'https://ws-cdn.tv.sfr.net/gaia-core/rest/api/web/v1/content/{}/episodes'
CONTENT_OPTIONS_URL = 'https://ws-backendtv.sfr.fr/gaia-core/rest/api/web/v3/content/{}/options'
SEARCH_TEXT_URL = 'https://ws-backendtv.sfr.fr/gaia-core/rest/api/web/v2/search/text'
VOD_PLAY_URL = 'https://ws-backendtv.sfr.fr/gaia-core/rest/api/web/v1/vod/play'
CUSTOMDATA_LIVE = ('description={}&deviceId=byPassARTHIUS&deviceName=Chrome-119.0.0.0----Windows&deviceType=PC'
                   '&osName=Windows&osVersion=10&persistent=false&resolution=1600x900&tokenType=castoken'
                   '&tokenSSO={}&type=LIVEOTT&accountId={}')
CUSTOMDATA_REPLAY = ('description={}&deviceId=byPassARTHIUS&deviceName=Chrome-119.0.0.0----Windows&deviceType=PC'
                     '&osName=Windows&osVersion=10&persistent=false&resolution=1600x900&tokenType=castoken'
                     '&tokenSSO={}&type={}')
CUSTOMDATA_VOD = ('description={}&deviceId=byPassARTHIUS&deviceName=Chrome-119.0.0.0----Windows&deviceType=PC'
                  '&osName=Windows&osVersion=10&persistent=false&resolution=1600x900&tokenType=castoken'
                  '&tokenSSO={}&entitlementId={}&type={}')
MAX_CONTENTS = 20
REQUEST_TIMEOUT = 30
REPLAY_MENU_ID = 'RefMenuItem::gen8-replay-v2'
VOD_MENU_ID = 'RefMenuItem::gen8-vod-v2'
PAID_CONTENT_INDICATORS = ['inPackRented', 'inRent', 'inSVodSubscribed']


def get_sfrtv_config(plugin):
    return urlquick.get(CONFIG_URL,
                        headers={'User-Agent': USER_AGENT},
                        timeout=REQUEST_TIMEOUT).json()


def get_sfrtv_user_profile(plugin, token):
    params = {
        'token': token
    }
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    return urlquick.get(USER_PROFILE_URL,
                        params=params,
                        headers=headers,
                        timeout=REQUEST_TIMEOUT).json()


def get_credentials_from_config(plugin, with_dialog):
    username = plugin.setting.get_string('sfrtv.login')
    password = plugin.setting.get_string('sfrtv.password')

    if not username or not password:
        if with_dialog:
            xbmcgui.Dialog().ok(plugin.localize(30600),
                                plugin.localize(30604) % ('SFR TV', 'https://tv.sfr.fr'))
        return None, None

    return username, password


def get_token(plugin, with_dialog=True):
    username, password = get_credentials_from_config(plugin, with_dialog)
    if not username or not password:
        return None

    # Unable to use urlquick cache due to authentication redirects
    cache = Cache(CACHE_FILE, TOKEN_MAX_AGE)

    if 'token' in cache:
        return cache['token']

    sfrtv_config = get_sfrtv_config(plugin)
    sfrtv_client_id = sfrtv_config['auth']['OIDC_CLIENT_ID']

    session = urlquick.Session()

    params = {
        'client_id': sfrtv_client_id,
        'scope': 'openid',
        'response_type': 'token',
        'redirect_uri': 'https://tv.sfr.fr/'
    }
    headers = {
        'user-agent': USER_AGENT,
        'authority': 'www.sfr.fr',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'referer': 'https://tv.sfr.fr/',
    }
    resp = session.get(ACCESS_TOKEN_URL,
                       params=params,
                       headers=headers,
                       max_age=-1,
                       timeout=REQUEST_TIMEOUT)

    root = resp.parse()
    form_elt = root.find(".//form[@name='loginForm']")
    lt = form_elt.find(".//input[@name='lt']").get('value')
    lrt = form_elt.find(".//input[@name='lrt']").get('value')
    execution = form_elt.find(".//input[@name='execution']").get('value')
    event_id = form_elt.find(".//input[@name='_eventId']").get('value')

    params = {
        'domain': 'mire-sfr',
        'service': 'https://www.sfr.fr/cas/oidc/callbackAuthorize'
    }
    headers = {
        'user-agent': USER_AGENT,
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'authority': 'www.sfr.fr',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded',
        'origin': 'https://www.sfr.fr',
        'referer': resp.url,
    }
    data = {
        'lt': lt,
        'execution': execution,
        'lrt': lrt,
        '_eventId': event_id,
        'username': username,
        'password': password,
        'remember-me': 'on',
        'identifier': ''
    }
    session.post(
        LOGIN_URL,
        params=params,
        headers=headers,
        data=data,
        max_age=-1,
        timeout=REQUEST_TIMEOUT
    )

    params = {
        'client_id': sfrtv_client_id,
        'scope': 'openid',
        'response_type': 'token',
        'redirect_uri': 'https://tv.sfr.fr/',
        'token': 'true',
        'gateway': 'true'
    }
    headers = {
        'user-agent': USER_AGENT,
        'authority': 'www.sfr.fr',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'origin': 'https://tv.sfr.fr',
        'referer': 'https://tv.sfr.fr/',
    }
    resp = session.get(ACCESS_TOKEN_URL,
                       params=params,
                       headers=headers,
                       max_age=-1,
                       timeout=REQUEST_TIMEOUT)
    access_token_b64_bytes = resp.content
    access_token_b64 = access_token_b64_bytes.decode('ascii')
    if not access_token_b64:
        if with_dialog:
            xbmcgui.Dialog().ok(plugin.localize(30600),
                                plugin.localize(30711))
        return None
    access_token_b64_second_part = access_token_b64.split('.')[1]
    access_token_b64_second_part_bytes = access_token_b64_second_part.encode('ascii')
    missing_padding = len(access_token_b64_second_part_bytes) % 4
    if missing_padding:
        access_token_b64_second_part_bytes += b'=' * (4 - missing_padding)
    access_token_second_part_bytes = base64.b64decode(access_token_b64_second_part_bytes)
    access_token_second_part_json = access_token_second_part_bytes.decode('utf-8')
    access_token_second_part = json.loads(access_token_second_part_json)
    token = access_token_second_part['tu']

    cache['token'] = token
    return token


@Route.register(autosort=False)
def provider_root(plugin, **kwargs):
    username, password = get_credentials_from_config(plugin, True)
    if not username or not password:
        yield False
        return

    # Live TV
    item = Listitem()
    item.label = plugin.localize(30030)
    item.art['thumb'] = get_item_media_path('live_tv.png')
    item.set_callback(list_lives)
    item_post_treatment(item)
    yield item

    # Replay
    item = Listitem()
    item.label = 'Replay'
    item.art['thumb'] = get_item_media_path('replay.png')
    item.set_callback(list_replay_stores)
    item_post_treatment(item)
    yield item

    # VOD
    item = Listitem()
    item.label = 'VOD'
    item.art['thumb'] = get_item_media_path('vod.png')
    item.set_callback(list_vod_spots)
    item_post_treatment(item)
    yield item

    # Search feature
    item = Listitem.search(search)
    item_post_treatment(item)
    yield item


def get_menu_structure(plugin, menu_id):
    params = {
        'accountTypes': 'LAND',
        'infrastructures': 'FTTH',
        'operators': 'sfr',
        'noTracking': 'false',
        'app': 'gen8',
        'device': 'browser'
    }
    headers = {
        'Accept': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    return urlquick.get(MENU_STRUCTURE_URL.format(menu_id),
                        params=params,
                        headers=headers,
                        timeout=REQUEST_TIMEOUT).json()


def get_spot_content(plugin, spot_id, token=None):
    if token:
        params = {
            'app': 'gen8',
            'device': 'browser',
            'token': token,
            'operators': 'sfr',
            'infrastructures': 'FTTH',
            'accountTypes': 'LAND',
            'noTracking': 'false',
        }
    else:
        params = {
            'app': 'gen8',
            'device': 'browser',
            'noTracking': 'false',
        }
    headers = {
        'Accept': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    return urlquick.get(SPOT_CONTENT_URL.format(spot_id),
                        params=params,
                        headers=headers,
                        max_age=(TOKEN_MAX_AGE if token else -1),
                        timeout=REQUEST_TIMEOUT).json()


def get_replay_stores(plugin, token):
    menu_structure = get_menu_structure(plugin, REPLAY_MENU_ID)

    # only one spot for Replay
    spot_id = menu_structure['spots'][0]['id']

    spot_content = get_spot_content(plugin, spot_id, token)

    return spot_content['tiles']


@Route.register(autosort=False)
def list_replay_stores(plugin, **kwargs):
    token = get_token(plugin)
    if not token:
        yield False
        return

    for store in get_replay_stores(plugin, token):
        yield build_product_item(plugin, store)


def get_store_categories(plugin, store_id):
    params = {
        'app': 'gen8',
        'device': 'browser',
        'accountTypes': 'LAND',
        'infrastructures': 'FTTH',
        'operators': 'sfr',
        'noTracking': 'false'
    }
    headers = {
        'Accept': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    categories_infos = urlquick.get(STORE_CATEGORIES_URL.format(store_id),
                                    params=params,
                                    headers=headers,
                                    timeout=REQUEST_TIMEOUT).json()
    return categories_infos['categories']


@Route.register(autosort=False)
def list_store_categories(plugin, store_id, **kwargs):
    categories = get_store_categories(plugin, store_id)

    for category in categories:
        item = Listitem()
        item.label = category['name']
        item.set_callback(list_category_contents,
                          category_id=category['id'])
        item_post_treatment(item)
        yield item


def get_category_contents(plugin, category_id, page=0):
    params = {
        'app': 'gen8',
        'device': 'browser',
        'accountTypes': 'LAND',
        'infrastructures': 'FTTH',
        'operators': 'sfr',
        'noTracking': 'false',
        'page': page,
        'size': MAX_CONTENTS  # this parameter doesn't change anything (max 20 contents)
    }
    headers = {
        'Accept': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    return urlquick.get(CATEGORY_CONTENTS_URL.format(category_id),
                        params=params,
                        headers=headers,
                        timeout=REQUEST_TIMEOUT).json()


@Route.register(autosort=False)
def list_category_contents(plugin, category_id, page=0, **kwargs):
    # Pagination seems to be blocked at 20 contents (the "size" parameter doesn't change anything),
    # so let's paginate at 100 contents
    n_loop = 5
    for x in range(n_loop):
        contents = get_category_contents(plugin, category_id, page)

        for content in contents:
            yield build_product_item(plugin, content)

        if len(contents) == MAX_CONTENTS:  # no "count" or "total" information
            if x < (n_loop - 1):
                page += 1
            else:
                yield Listitem.next_page(category_id=category_id,
                                         callback=list_category_contents,
                                         page=page + 1)
        else:
            break


def get_content_details(plugin, content_id, universe='PROVIDER', **kwargs):
    params = {
        'accountTypes': 'LAND',
        'infrastructures': 'FTTH',
        'operators': 'sfr',
        'noTracking': 'false',
        'universe': universe
    }
    headers = {
        'Accept': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    return urlquick.get(CONTENT_DETAILS_URL.format(content_id),
                        params=params,
                        headers=headers,
                        timeout=REQUEST_TIMEOUT).json()


@Route.register(autosort=False)
def list_content_details(plugin, content_id, action_type='', **kwargs):
    token = get_token(plugin)
    if not token:
        yield False
        return

    content_details = get_content_details(plugin, content_id, **kwargs)

    if 'seasons' in content_details:
        for season in content_details['seasons']:
            season_details = get_content_details(plugin, season['id'], **kwargs)
            yield build_product_item(plugin, season_details)
    elif action_type == 'displayFip' and content_details['type'] == 'Season' and content_details.get('seriesId'):
        series_details = get_content_details(plugin, content_details['seriesId'], **kwargs)
        for season in series_details['seasons']:
            season_details = get_content_details(plugin, season['id'], **kwargs)
            yield build_product_item(plugin, season_details)
    elif 'episodes' in content_details:
        for episode in list_content_episodes(plugin, content_id, **kwargs):
            yield episode
    else:
        yield build_product_item(plugin, content_details)


def get_content_episodes(plugin, season_id, universe='PROVIDER', page=0, size=10, **kwargs):
    params = {
        'app': 'gen8',
        'device': 'browser',
        'accountTypes': 'LAND',
        'infrastructures': 'FTTH',
        'operators': 'sfr',
        'noTracking': 'false',
        'universe': universe,
        'page': page,
        'size': size,
        'sortBy': 'DIFFUSIONDATE',
        'sorting': 'DESC'
    }
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'Origin': 'https://tv.sfr.fr',
        'Connection': 'keep-alive'
    }
    search_result = urlquick.get(CONTENT_EPISODES_URL.format(season_id),
                                 params=params,
                                 headers=headers,
                                 timeout=REQUEST_TIMEOUT).json()

    has_next_page = (search_result['count'] - ((page + 1) * size)) > 0

    return search_result['content'], page, has_next_page


@Route.register(autosort=False)
def list_content_episodes(plugin, season_id, **kwargs):
    episodes, page, has_next_page = get_content_episodes(plugin, season_id, **kwargs)

    for episode in episodes:
        yield build_product_item(plugin, episode)

    if has_next_page:
        item = Listitem.next_page(callback=list_content_episodes,
                                  season_id=season_id,
                                  page=page + 1,
                                  **kwargs)
        item.property['SpecialSort'] = 'bottom'
        yield item


def build_product_item(plugin, product, default_preferred_image_ratio='16/9'):
    item = Listitem()

    item.label = product['title']

    if product.get('subTitle'):
        item.label += ' - ' + product['subTitle']

    if product.get('universe') == 'aggregate':
        if product.get('type') == 'Season' and product.get('seasonNumber'):
            item.label += ' - Saison ' + str(product['seasonNumber'])

    if product.get('universe') == 'aggregate' or (product.get('context') and 'VOD' in product['context'].upper()):
        if product.get('genres') and len(product['genres']) > 0:
            item.info['genre'] = product['genres'][0]

    if product.get('description'):
        item.info['plot'] = product['description']
    elif product.get('shortDescription'):
        item.info['plot'] = product['shortDescription']

    if product.get('duration'):
        item.info['duration'] = product['duration']

    if product.get('seasonNumber'):
        item.info['mediatype'] = 'season'
        item.info['season'] = product['seasonNumber']

    if product.get('episodeNumber'):
        item.info['mediatype'] = 'episode'
        item.info['episode'] = product['episodeNumber']

    if product.get('diffusionDate'):
        dt = datetime.fromtimestamp(int(product['diffusionDate'] / 1000))
        dt_format = '%d/%m/%Y'
        item.info.date(dt.strftime(dt_format), dt_format)

    if product.get('releaseDate'):
        item.info['year'] = product['releaseDate']

    if len(product.get('images', [])) > 0:
        pref_ratio = product.get('preferredImageRatio') or default_preferred_image_ratio
        item.art['thumb'] = (next((image['url'] for image in product['images'] if image['format'] == pref_ratio), None)
                             or product['images'][0]['url'])

    product_type = product.get('type')
    if product_type in ['Serie', 'Season', 'CONTENT']:
        callback = list_content_details
    elif product_type == 'BASE':
        if 'categoryId' in product['action']['actionIds']:
            callback = list_category_contents
        elif 'spotId' in product['action']['actionIds']:
            callback = list_spot_more_contents
        elif 'tileId' in product['action']['actionIds']:
            callback = list_tile_contents
        else:
            callback = list_store_categories
    else:
        callback = get_stream

    if product_type == 'CONTENT':
        product_id = product['action']['actionIds']['contentId']
    elif product_type == 'BASE':
        if 'categoryId' in product['action']['actionIds']:
            product_id = product['action']['actionIds']['categoryId']
        elif 'spotId' in product['action']['actionIds']:
            product_id = product['action']['actionIds']['spotId']
        elif 'tileId' in product['action']['actionIds']:
            product_id = product['action']['actionIds']['tileId']
        else:
            product_id = product['action']['actionIds']['storeId']
    else:
        product_id = product['id']

    item.set_callback(callback,
                      product_id,
                      universe=product['universe'] if 'universe' in product else 'PROVIDER',
                      action_type=product['action']['actionType'] if 'action' in product else '')

    item_post_treatment(item)

    return item


def get_stream_url(plugin, product_id, token, universe='PROVIDER', **kwargs):
    params = {
        'app': 'gen8',
        'device': 'browser',
        'token': token,
        'accountTypes': 'LAND',
        'infrastructures': 'FTTH',
        'operators': 'sfr',
        'noTracking': 'false',
        'universe': universe
    }
    headers = {
        'Accept': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    content_options = urlquick.get(CONTENT_OPTIONS_URL.format(product_id),
                                   params=params,
                                   headers=headers,
                                   timeout=REQUEST_TIMEOUT).json()
    context = ''
    offer_id = ''
    for option in content_options:
        context = option['context']
        for offer in option.get('offers', []):
            if offer.get('buyable') and not any(map(lambda x: offer[x], PAID_CONTENT_INDICATORS)):
                continue
            if offer.get('offerType'):
                context = offer['offerType']
            if offer.get('offerId'):
                offer_id = offer['offerId']
            for stream in offer.get('streams', []):
                if stream['drm'] == 'WIDEVINE':
                    return stream['url'], context, offer_id
    return None, context, offer_id


@Resolver.register
def get_stream(plugin, product_id, **kwargs):
    token = get_token(plugin)
    if not token:
        return False

    video_url, context, offer_id = get_stream_url(plugin, product_id, token, **kwargs)
    stream_type = (context or '').upper()

    if not video_url:
        if 'VOD' in stream_type:
            xbmcgui.Dialog().ok(plugin.localize(30600),
                                plugin.localize(30732) % ('SFR TV', 'https://tv.sfr.fr'))

        return False

    if 'VOD' in stream_type:
        vod_play_info = get_vod_play_info(plugin, offer_id, token)
        entitlement_id = vod_play_info['entitlementId']
        custom_data = CUSTOMDATA_VOD.format(USER_AGENT, token, entitlement_id, stream_type)
    else:
        custom_data = CUSTOMDATA_REPLAY.format(USER_AGENT, token, stream_type)

    headers = {
        'User-Agent': USER_AGENT,
        'customdata': custom_data,
        'Referer': 'https://tv.sfr.fr/',
        'content-type': 'application/octet-stream'
    }

    return resolver_proxy.get_stream_with_quality(plugin,
                                                  video_url=video_url,
                                                  license_url=LICENSE_URL,
                                                  manifest_type='mpd',
                                                  headers=headers)


def get_vod_play_info(plugin, offer_id, token):
    params = {
        'app': 'gen8',
        'device': 'browser',
        'token': token,
        'operators': 'sfr',
        'infrastructures': 'FTTH',
        'accountTypes': 'LAND',
        'noTracking': 'false'
    }
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    data = {
        'offerId': offer_id,
        'macAddress': 'PC',
        'app': 'gen8',
        'device': 'browser',
        'token': token
    }
    return urlquick.post(VOD_PLAY_URL,
                         params=params,
                         headers=headers,
                         json=data,
                         max_age=-1,
                         timeout=REQUEST_TIMEOUT).json()


@Route.register(autosort=False)
def list_vod_spots(plugin, **kwargs):

    menu_structure = get_menu_structure(plugin, VOD_MENU_ID)

    for spot in menu_structure['spots']:

        if spot.get('layout') == 'poster':
            spot_content = get_spot_content(plugin, spot['id'])
            content = spot_content['tiles'][0]
            yield build_product_item(plugin, content)
            continue

        if spot.get('title'):
            label = spot['title']
        else:
            spot_content = get_spot_content(plugin, spot['id'])
            label = spot_content['title']

        item = Listitem()
        item.label = label
        item.set_callback(list_spot_contents, spot['id'])
        item_post_treatment(item)
        yield item


@Route.register(autosort=False)
def list_spot_contents(plugin, spot_id, **kwargs):
    token = get_token(plugin)
    if not token:
        yield False
        return

    spot_content = get_spot_content(plugin, spot_id, token)

    for content in spot_content['tiles']:
        yield build_product_item(plugin, content)


def get_spot_more_content(plugin, spot_id, token, page=0, size=MAX_CONTENTS):
    params = {
        'app': 'gen8',
        'device': 'browser',
        'token': token,
        'page': page,
        'size': size,
        'operators': 'sfr',
        'infrastructures': 'FTTH',
        'accountTypes': 'LAND',
        'noTracking': 'false',
    }
    headers = {
        'Accept': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    return urlquick.get(SPOT_MORE_URL.format(spot_id),
                        params=params,
                        headers=headers,
                        max_age=TOKEN_MAX_AGE,
                        timeout=REQUEST_TIMEOUT).json()


@Route.register(autosort=False)
def list_spot_more_contents(plugin, spot_id, page=0, **kwargs):
    token = get_token(plugin)
    if not token:
        yield False
        return

    spot_content = get_spot_more_content(plugin, spot_id, token, page)
    contents = spot_content['tiles']

    for content in contents:
        yield build_product_item(plugin, content)

    if len(contents) == MAX_CONTENTS:  # no "count" or "total" information
        yield Listitem.next_page(spot_id=spot_id,
                                 callback=list_spot_more_contents,
                                 page=page + 1)


def get_tile_content(plugin, tile_id, token, page=0, size=MAX_CONTENTS):
    params = {
        'app': 'gen8',
        'device': 'browser',
        'token': token,
        'page': page,
        'size': size,
        'operators': 'sfr',
        'infrastructures': 'FTTH',
        'accountTypes': 'LAND',
        'noTracking': 'false',
    }
    headers = {
        'Accept': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    return urlquick.get(TILE_CONTENT_URL.format(tile_id),
                        params=params,
                        headers=headers,
                        max_age=TOKEN_MAX_AGE,
                        timeout=REQUEST_TIMEOUT).json()


@Route.register(autosort=False)
def list_tile_contents(plugin, tile_id, page=0, **kwargs):
    token = get_token(plugin)
    if not token:
        yield False
        return

    tile_content = get_tile_content(plugin, tile_id, token, page)
    contents = tile_content['items']
    preferred_image_ratio = tile_content.get('preferredImageRatio')

    for content in contents:
        yield build_product_item(plugin, content, preferred_image_ratio)

    if len(contents) == MAX_CONTENTS:  # no "count" or "total" information
        yield Listitem.next_page(tile_id=tile_id,
                                 callback=list_tile_contents,
                                 page=page + 1)


def get_products_to_search(plugin, keyword, page=0, size=25, **kwargs):
    params = {
        'app': 'gen8',
        'device': 'browser',
        'keyword': keyword,
        'page': page,
        'size': size
    }
    headers = {
        'Accept': 'application/json',
        'Referer': 'https://tv.sfr.fr/',
        'User-Agent': USER_AGENT
    }
    search_result = urlquick.get(SEARCH_TEXT_URL,
                                 params=params,
                                 headers=headers,
                                 timeout=REQUEST_TIMEOUT).json()

    has_next_page = (search_result['count'] - ((page + 1) * size)) > 0

    return search_result['content'], page, has_next_page


@Route.register(autosort=False)
def search(plugin, search_query, **kwargs):
    products, page, has_next_page = get_products_to_search(plugin, search_query, **kwargs)

    for product in products:
        yield build_product_item(plugin, product)

    if has_next_page:
        item = Listitem.next_page(search_query=search_query,
                                  callback=search,
                                  page=page + 1)
        item.property['SpecialSort'] = 'bottom'
        yield item


def get_active_services(plugin, token):
    params = {
        'app': 'gen8',
        'device': 'browser',
        'token': token
    }
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/json',
        'Accept-language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Origin': 'https://tv.sfr.fr',
        'Referer': 'https://tv.sfr.fr/',
        'Connection': 'keep-alive'
    }
    services = urlquick.get(SERVICE_URL,
                            params=params,
                            headers=headers,
                            max_age=TOKEN_MAX_AGE,
                            timeout=REQUEST_TIMEOUT).json()
    active_services = list(filter(lambda c: c['access'], services))
    return active_services


def list_live_channels(plugin=Script):

    """
    Called by iptvmanager to retrieve a dynamic list of SFR TV channels to activate for IPTV Manager.
    Only the channels activated for the current account are yielded.
    For each channel, the information is retrieved from the "sfrtv_live" skeleton but if the channel
    is not found in it, the information is manually built.

    :param plugin: plugin (codequick.script.Script)

    :returns: A generator of the channels infos
    :rtype: :class:`types.GeneratorType`
    """

    token = get_token(plugin,
                      with_dialog=False)
    if not token:
        return

    active_services = get_active_services(plugin, token)
    channels_dict = importlib.import_module('resources.lib.skeletons.sfrtv_live').menu

    for serv in active_services:
        channel_infos = channels_dict.get(serv['serviceId'])

        if not channel_infos:
            channel_infos = {
                'resolver': '/resources/lib/providers/sfrtv:get_live_stream',
                'label': serv['name'],
                'enabled': True,
                'order': serv['zappingId']
            }
            for image in serv.get('images', []):
                if image['type'] == 'color':
                    channel_infos['thumb'] = image['url']

        channel_infos['id'] = serv['serviceId']
        yield channel_infos


@Route.register
def list_lives(plugin, **kwargs):
    token = get_token(plugin)
    if not token:
        yield False
        return

    active_services = get_active_services(plugin, token)
    tv_guide_items = list(tv_guide_menu(plugin, 'sfrtv_live'))

    for serv in sorted(active_services, key=lambda s: s['zappingId']):

        # Try to find the TV Guide Listitem from sfrtv live menu
        item = next(
            (tvg for tvg in tv_guide_items if tvg.params.item_id == serv['serviceId']),
            None
        )

        # If not found, construct manually a Listitem without TV guide
        if not item:
            item = Listitem()
            item.label = serv['name']

            for image in serv.get('images', []):
                if image.get('type') == 'color':
                    item.art['thumb'] = item.art['landscape'] = image.get('url')

            # Playcount is useless for live streams
            item.info['playcount'] = 0

            item.set_callback(get_live_stream,
                              item_id=serv['serviceId'])

        yield item


def get_live_url(plugin, service_id, token):
    active_services = get_active_services(plugin, token)

    for serv in active_services:
        if serv['serviceId'] == service_id:
            for stream in serv['streams']:
                if stream['drm'] == 'WIDEVINE':
                    # Workaround for IA bug : https://github.com/xbmc/inputstream.adaptive/issues/804
                    response = urlquick.get(stream['url'],
                                            headers={'User-Agent': USER_AGENT},
                                            max_age=-1,
                                            timeout=REQUEST_TIMEOUT)
                    live_url = response.xml().find('{urn:mpeg:dash:schema:mpd:2011}Location').text
                    return live_url
    return None


@Resolver.register
def get_live_stream(plugin, item_id, **kwargs):
    token = get_token(plugin)
    if not token:
        return False

    live_url = get_live_url(plugin, item_id, token)
    if not live_url:
        return False

    sfrtv_user_profile = get_sfrtv_user_profile(plugin, token)
    account_id = sfrtv_user_profile['siebelId']

    headers = {
        'user-agent': USER_AGENT,
        'customdata': CUSTOMDATA_LIVE.format(USER_AGENT, token, account_id),
        'origin': 'https://tv.sfr.fr',
        'referer': 'https://tv.sfr.fr/',
        'content-type': 'application/octet-stream'
    }

    return resolver_proxy.get_stream_with_quality(plugin,
                                                  video_url=live_url,
                                                  license_url=LICENSE_URL,
                                                  manifest_type='mpd',
                                                  headers=headers)
