"""Arte TV and HBB TV API communications - REST and authentication calls"""
from collections import OrderedDict
# pylint: disable=import-error
import requests
import xbmc
from resources.lib import logger
from resources.lib.utils import ADDON_USERAGENT


# Arte TV API - Used on Arte TV website
_ARTETV_URL = 'https://api.arte.tv/api'
_ARTETV_AUTH_URL = 'https://auth.arte.tv/ssologin'
ARTETV_ENDPOINTS = {
    # POST
    'token': '/sso/v3/token',
    # needs token in authorization header
    'get_favorites': '/sso/v3/favorites/{lang}',
    # PUT
    # needs token in authorization header
    'add_favorite': '/sso/v3/favorites',
    # DELETE
    # needs token in authorization header
    'remove_favorite': '/sso/v3/favorites/{program_id}',
    # PATCH empty payload
    # needs token in authorization header
    'purge_favorites': '/sso/v3/favorites/purge',
    # needs token in authorization header
    'get_last_viewed': '/sso/v3/lastvieweds/{lang}',
    # PUT
    # needs token in authorization header
    # payload {'programId':'110342-012-A','timecode':574} for 574s i.e. 9:34
    'sync_last_viewed': '/sso/v3/lastvieweds',
    # PATCH empty payload
    # needs token in authorization header
    'purge_last_viewed': '/sso/v3/lastvieweds/purge',
    # GET personal user data (email, firstName, lastName, etc.)
    # needs token in authorization header
    'personal_data': '/sso/v3/me',
    # program_id can be 103520-000-A or LIVE
    'player': '/player/v2/config/{lang}/{program_id}',
    'playlist': '/player/v2/playlist/{lang}/{collection_id}',
    'program': '/emac/v4/{lang}/web/programs/{program_id}',
    # category=HOME, CIN, SER, SEARCH client=app, tv, web, orange, free
    'page': '/emac/v4/{lang}/{client}/pages/{category}/',
    # zone_id=167d478a-b668-42a3-b88a-f01a436c7394...
    # keep path and url in a snigle place for readibility
    # page_id=SEARCH, HOME...
    'zone':
        '/emac/v4/{lang}/{client}/zones/{zone_id}/content',
    'zonepage':
        '/emac/v4/{lang}/{client}/zones/{zone_id}/content',
    # not yet impl.
    # date=2023-01-17
    # 'guide_tv': '/emac/v3/{lang}/{client}/pages/TV_GUIDE/?day={DATE}',
    # auth api
    'login': '/login',
}
LIGHT_HEADERS = {
    'user-agent': ADDON_USERAGENT
}
ARTETV_HEADERS = {
    'user-agent': ADDON_USERAGENT,
    # required to use token endpoint
    'authorization': 'I6k2z58YGO08P1X0E8A7VBOjDxr8Lecg',
    # required for Arte TV API. values like web, app, tv, orange, free
    # prefer client tv over web so that Arte adapt content to tv limiting links for instance
    'client': 'tv',
    'accept': 'application/json'
}

_ARTETV_ID_URL = 'https://id.arte.tv/auth/realms/myarte-prod/protocol/openid-connect'
DEVICE_AUTH_URL = f"{_ARTETV_ID_URL}/auth/device"
DEVICETOKEN_URL = f"{_ARTETV_ID_URL}/token"
SMART_TV_CLIENT_ID = 'smart-tv'


def get_favorites(lang, tkn, page_idx, page_size=50):
    """Retrieve favorites from a personal account."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['get_favorites'].format(lang=lang)
    params = {'page': page_idx, 'limit': page_size}
    return _load_json_personal_content('artetv_getfavorites', url, tkn, params=params)


def add_favorite(tkn, program_id, language):
    """
    Add content program_id to user favorites.
    :return: HTTP status code.
    """
    url = _ARTETV_URL + ARTETV_ENDPOINTS['add_favorite']
    headers = _add_auth_token(tkn, ARTETV_HEADERS)
    data = {'programId': program_id, 'language': language}
    reply = requests.put(url, data=data, headers=headers, timeout=10)
    logger.log_json(reply, 'artetv_addfavorite')
    return reply.status_code


def remove_favorite(tkn, program_id):
    """
    Remove content program_id from user favorites.
    :return: HTTP status code.
    """
    url = _ARTETV_URL + ARTETV_ENDPOINTS['remove_favorite'].format(program_id=program_id)
    headers = _add_auth_token(tkn, ARTETV_HEADERS)
    reply = requests.delete(url, headers=headers, timeout=10)
    logger.log_json(reply, 'artetv_removefavorite')
    return reply.status_code


def purge_favorites(tkn):
    """Flush user favorites"""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['purge_favorites']
    headers = _add_auth_token(tkn, ARTETV_HEADERS)
    reply = requests.patch(url, data={}, headers=headers, timeout=10)
    logger.log_json(reply, 'artetv_purgefavorites')
    return reply.status_code


def get_last_viewed(lang, tkn, page_idx, page_size=50):
    """Retrieve content recently watched by a user."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['get_last_viewed'].format(lang=lang)
    params = {'page': page_idx, 'limit': page_size}
    return _load_json_personal_content('artetv_lastviewed', url, tkn, params=params)


def get_last_viewed_all(lang, tkn):
    """
    Retrieve every content recently watched by a user, all pages.
    Never None. Empty list in the worst case
    """
    all_data = []
    next_page_idx = 1
    while next_page_idx:
        current_page = get_last_viewed(lang, tkn, next_page_idx)
        if current_page is not None and isinstance(current_page, dict):
            all_data = all_data + current_page.get('data', [])
        next_page_idx = _get_next_page(current_page)
    return all_data


def _get_next_page(last_viewed):
    """Return the next page idx or False, never None"""
    if last_viewed is None:
        return False
    if not isinstance(last_viewed.get('meta', False), dict):
        return False
    current_page = last_viewed.get('meta').get('page')
    if current_page < last_viewed.get('meta').get('pages'):
        return int(current_page) + 1
    return False


def sync_last_viewed(tkn, program_id, time):
    """
    Synchronize in arte profile the progress time of content being played.
    :return: HTTP status code.
    """
    url = _ARTETV_URL + ARTETV_ENDPOINTS['sync_last_viewed']
    headers = _add_auth_token(tkn, ARTETV_HEADERS)
    data = {'programId': program_id, 'timecode': time}
    reply = requests.put(url, data=data, headers=headers, timeout=10)
    logger.log_json(reply, 'artetv_synchlastviewed')
    return reply.status_code


def purge_last_viewed(tkn):
    """Flush user history"""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['purge_last_viewed']
    headers = _add_auth_token(tkn, ARTETV_HEADERS)
    reply = requests.patch(url, data={}, headers=headers, timeout=10)
    logger.log_json(reply, 'artetv_purgelastviewed')
    return reply.status_code


def get_personal_data(tkn):
    """
    Retrieve personal user data (email, firstName, lastName, etc.) from Arte API.
    Requires authenticated token.
    Returns the user data dict from API response or None if request fails.
    """
    url = _ARTETV_URL + ARTETV_ENDPOINTS['personal_data']
    reply = _load_json_personal_content('artetv_getpersonaldata', url, tkn, redact_body=True)
    if reply is not None and isinstance(reply.get('data'), list) and len(reply.get('data', [])) > 0:
        return reply['data'][0]
    return None


def player_video(lang, program_id):
    """Get the info of content program_id from Arte TV API."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['player'].format(lang=lang, program_id=program_id)
    return _load_json_full_url('artetv_player', url, None).get('data', {})


def playlist_collection(lang, collection_id):
    """Get the info of content program_id from Arte TV API."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['playlist'].format(lang=lang, collection_id=collection_id)
    return _load_json_full_url('artetv_playlist', url, None).get('data', {})


def program_video(lang, program_id):
    """Get the info of content program_id from Arte TV API."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['program'].format(lang=lang, program_id=program_id)
    return _load_json_full_url('artetv_program', url, None)


def get_parent_collection(lang, program_id):
    """
    Get parent collection of program program_id.
    Return an empty list, if nothing found.
    """
    artetv_program_stream = program_video(lang, program_id)
    if artetv_program_stream:
        for zone in artetv_program_stream.get('zones', []):
            if zone.get('content'):
                for data in zone.get('content').get('data'):
                    return data.get('parentCollections', [])
    return []


def is_of_kind(arte_item, kind):
    """Return true if arte_item is not None and of the kind provided as parameter"""
    return (arte_item and arte_item.get('kind') == kind) or False


# def collection_with_last_viewed(lang, tkn, kind, collection_id):
#     """
#     Get the info of collection collection_id and enhanced them with last_viewed details
#     e.g. progress
#     """
#     collection_items = collection(kind, collection_id, lang)
#     last_viewed_items = get_last_viewed_all(lang, tkn)
#     # nothing to do
#     if len(collection_items) < 1 or len(last_viewed_items) < 1:
#         return collection_items
#     # merge the 2 collection based on program id.
#     last_viewed_map = {}
#     for item in last_viewed_items:
#         last_viewed_map[item.get('programId')] = item
#     for idx, basic_item in enumerate(collection_items):
#         if basic_item is not None and basic_item.get('programId') is not None:
#             enhanced_item = last_viewed_map.get(basic_item.get('programId'))
#             if enhanced_item is not None:
#                 collection_items[idx] = enhanced_item
#     return collection_items


def page_content(lang, cat='HOME'):
    """Get content to be display in a page. It can be a page for a category or the home page."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['page'].format(
        lang=lang, category=cat, client='tv')
    return _load_json_full_url('artetv_home', url, ARTETV_HEADERS)


def init_search(lang, query):
    """
    Initialize a search for content in Arte TV API.
    Search will be identified by zone id then.
    """
    url = _ARTETV_URL + ARTETV_ENDPOINTS['page'].format(
        lang=lang, category='SEARCH', client='tv')
    params = {'page': '1', 'query': query}
    return _load_json_full_url(
        'artetv_initsearch', url, ARTETV_HEADERS, params).get('zones', [None])[0]


def get_search_page(lang, zone_id, page_idx, query):
    """
    Navigate in pages of a search identified by zone_id.
    """
    url = _ARTETV_URL + ARTETV_ENDPOINTS['zone'].format(
        lang=lang, client='tv', zone_id=zone_id)
    params = {
        'authorizedCountry': lang.upper(), 'page': page_idx, 'pageId': 'SEARCH',
        'query': query, 'abv': 'A', 'zoneIndexInPage': 0}
    return _load_json_full_url('artetv_getsearchpage', url, ARTETV_HEADERS, params)


def get_zone_page(lang, zone_id, page_idx):
    """
    Navigate in pages of a zone identified by zone_id.
    """
    # fix "bug" in Arte TV API of doubled zone_id. Example of wrong value:
    # a6f8c6d2-29d8-44e6-95f3-eec44d2fedaa_a6f8c6d2-29d8-44e6-95f3-eec44d2fedaa
    parts = zone_id.split('_')
    if len(parts) == 2 and parts[0] == parts[1]:
        zone_id = parts[0]
    url = _ARTETV_URL + ARTETV_ENDPOINTS['zonepage'].format(
        lang=lang, client='tv', zone_id=zone_id)
    params = {'authorizedCountry': lang.upper(), 'page': page_idx}
    return _load_json_full_url('artetv_getzonepage', url, ARTETV_HEADERS, params)


def _load_json_full_url(request_scope, url, headers=None, params=None, redact_body=False):
    if headers is None:
        headers = LIGHT_HEADERS
    # https://requests.readthedocs.io/en/latest/
    reply = requests.get(url, headers=headers, params=params, timeout=10)
    logger.log_json(reply, request_scope, redact_body)
    return reply.json(object_pairs_hook=OrderedDict)


# pylint: disable=too-many-arguments, too-many-positional-arguments
def _load_json_personal_content(request_scope, url, tkn, hdrs=None, params=None, redact_body=False):
    """Get a bearer token and add it in headers before sending the request"""
    if hdrs is None:
        hdrs = ARTETV_HEADERS
    headers = _add_auth_token(tkn, hdrs)
    if not headers:
        return None
    return _load_json_full_url(request_scope, url, headers, params, redact_body)


# Get a bearer token and add it as HTTP header authorization
def _add_auth_token(tkn, hdrs):
    if not tkn:
        return None
    headers = hdrs.copy()
    headers['authorization'] = f"{tkn['token_type']} {tkn['access_token']}"
    # web client needed to reuse token. Otherwise API rejects with
    # {"error":"invalid_client","error_description":"Client not authorized"}
    headers['client'] = 'web'
    return headers


def authenticate_in_arte(plugin, username='', password='', headers=None):
    """Return None if authentication failed and display an error notification
    Return arte reply with access and refresh tokens if authentication was successfull
    (i.e. status 200, no exception)"""
    headers = (headers or ARTETV_HEADERS).copy()
    # set client to web, because with tv get error client_invalid, error Client not authorized
    headers['client'] = 'web'

    url = _ARTETV_URL + ARTETV_ENDPOINTS['token']
    token_data = {
        'anonymous_token': None,
        'grant_type': 'password',
        'username': username,
        'password': password
    }
    xbmc.log(f"Try authenticating \"{username}\" to Arte TV", level=xbmc.LOGDEBUG)
    error = None
    reply = None
    try:
        # https://requests.readthedocs.io/en/latest/
        reply = requests.post(url, data=token_data, headers=headers, timeout=10)
        logger.log_json(reply, 'artetv_auth_password', True)
    except requests.exceptions.ConnectionError as err:
        # unable to auth. e.g.
        # HTTPSConnectionPool(host='api.arte.tv', port=443):
        # Max retries exceeded with url: /api/sso/v3/token
        error = err
    if error or not reply or reply.status_code != 200:
        err_dtls = str(error) if error else (reply.text if reply is not None else '')
        xbmc.log(f"Unable to authenticate to Arte TV : {err_dtls}", level=xbmc.LOGERROR)
        plugin.notify(msg=plugin.addon.getLocalizedString(30020), image='error')
        return None
    return reply.json(object_pairs_hook=OrderedDict)


def device_authorization_request():
    """
    Step 1 of ARTE Smart TV Device Flow:
    Request device_code + user_code from Keycloak.
    Returns dict or None.
    """
    try:
        payload = {
            "client_id": SMART_TV_CLIENT_ID,
            "scope": "openid"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        resp = requests.post(DEVICE_AUTH_URL, data=payload, headers=headers, timeout=10)
        logger.log_json(resp, 'artetv_deviceauth', True)
        if resp.status_code != 200:
            xbmc.log(f"Device authorization failed: HTTP {resp.status_code}", level=xbmc.LOGERROR)
            return None

        return resp.json()

    # pylint: disable=broad-except
    except Exception as e:
        xbmc.log(f"Device authorization exception: {e}", level=xbmc.LOGERROR)
        return None


def device_token_request(device_code):
    """
    Step 2 of ARTE Smart TV Device Flow:
    Poll token endpoint using device_code.
    Returns dict containing either:
    - access_token (success)
    - error (authorization_pending, slow_down, access_denied, expired_token)
    """
    try:
        payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code,
            "client_id": SMART_TV_CLIENT_ID
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        resp = requests.post(DEVICETOKEN_URL, data=payload, headers=headers, timeout=10)
        logger.log_json(resp, 'artetv_auth_devicetoken', True)
        return resp.json()

    # pylint: disable=broad-except
    except Exception as e:
        xbmc.log(f"Device token polling exception: {e}", level=xbmc.LOGERROR)
        return {"error": "exception"}
