"""Arte TV and HBB TV API communications - REST and authentication calls"""
from collections import OrderedDict
# pylint: disable=import-error
import requests
# pylint: disable=import-error
from xbmcswift2 import xbmc
from . import hof


# Arte hbbtv - deprecated API since 2022 prefer Arte TV API
_HBBTV_URL = 'http://www.arte.tv/hbbtvv2/services/web/index.php'
_HBBTV_HEADERS = {
    'user-agent': 'plugin.video.arteplussept/1.1.10'
}
_HBBTV_ENDPOINTS = {
    'category': '/EMAC/teasers/category/v2/{category_code}/{lang}',
    'collection': '/EMAC/teasers/collection/v2/{collection_id}/{lang}',
    # program details
    'video': '/OPA/v3/videos/{program_id}/{lang}',
    # program streams
    'streams': '/OPA/v3/streams/{program_id}/{kind}/{lang}'
}


# Arte TV API - Used on Arte TV website
_ARTETV_URL = 'https://api.arte.tv/api'
ARTETV_RPROXY_URL = 'https://arte.tv/api/rproxy'
_ARTETV_AUTH_URL = 'https://auth.arte.tv/ssologin'
ARTETV_ENDPOINTS = {
    # POST
    'token': '/sso/v3/token',
    # needs token in authorization header
    'get_favorites': '/sso/v3/favorites/{lang}?page={page}&limit={limit}',
    # PUT
    # needs token in authorization header
    'add_favorite': '/sso/v3/favorites',
    # DELETE
    # needs token in authorization header
    'remove_favorite': '/sso/v3/favorites/{program_id}',
    # needs token in authorization header
    'get_last_viewed': '/sso/v3/lastvieweds/{lang}?page={page}&limit={limit}',
    # PUT
    # needs token in authorization header
    # payload {'programId':'110342-012-A','timecode':574} for 574s i.e. 9:34
    'sync_last_viewed': '/sso/v3/lastvieweds',
    # PATCH empty payload
    # needs token in authorization header
    'purge_last_viewed': '/sso/v3/lastvieweds/purge',
    # program_id can be 103520-000-A or LIVE
    'program': '/player/v2/config/{lang}/{program_id}',
    # rproxy
    # category=HOME, CIN, SER, SEARCH client=app, tv, web, orange, free
    'page': '/emac/v4/{lang}/{client}/pages/{category}/',
    # not yet impl.
    # rproxy date=2023-01-17
    # 'guide_tv': '/emac/v3/{lang}/{client}/pages/TV_GUIDE/?day={DATE}',
    # auth api
    'custom_token': '/setCustomToken',
    # auth api
    'login': '/login',
}
ARTETV_HEADERS = {
    'user-agent': 'plugin.video.arteplussept/1.1.10',
    # required to use token endpoint
    'authorization': 'I6k2z58YGO08P1X0E8A7VBOjDxr8Lecg',
    # required for Arte TV API. values like web, app, tv, orange, free
    # prefer client tv over web so that Arte adapt content to tv limiting links for instance
    'client': 'tv',
    'accept': 'application/json'
}

def get_favorites(plugin, lang, usr, pwd):
    """Retrieve favorites from a personal account."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['get_favorites'].format(lang=lang, page='1', limit='50')
    return _load_json_personal_content(plugin, url, usr, pwd)

def add_favorite(plugin, usr, pwd, program_id):
    """Add content program_id to user favorites.
    :return: HTTP status code."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['add_favorite']
    headers = _add_auth_token(plugin, usr, pwd, ARTETV_HEADERS)
    data = {'programId': program_id}
    reply = requests.put(url, data=data, headers=headers, timeout=10)
    return reply.status_code

def remove_favorite(plugin, usr, pwd, program_id):
    """Remove content program_id from user favorites.
    :return: HTTP status code."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['remove_favorite'].format(program_id=program_id)
    headers = _add_auth_token(plugin, usr, pwd, ARTETV_HEADERS)
    reply = requests.delete(url, headers=headers, timeout=10)
    return reply.status_code

def get_last_viewed(plugin, lang, usr, pwd):
    """Retrieve content recently watched by a user."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['get_last_viewed'].format(lang=lang, page='1', limit='50')
    return _load_json_personal_content(plugin, url, usr, pwd)

def sync_last_viewed(plugin, usr, pwd, program_id, time):
    """Synchronize in arte profile the progress time of content being played.
    :return: HTTP status code."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['sync_last_viewed']
    headers = _add_auth_token(plugin, usr, pwd, ARTETV_HEADERS)
    data = {'programId': program_id, 'timecode': time}
    reply = requests.put(url, data=data, headers=headers, timeout=10)
    return reply.status_code

def purge_last_viewed(plugin, usr, pwd):
    """Flush user history"""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['purge_last_viewed']
    headers = _add_auth_token(plugin, usr, pwd, ARTETV_HEADERS)
    reply = requests.patch(url, data={}, headers=headers, timeout=10)
    return reply.status_code

def program_video(lang, program_id):
    """Get the info of content program_id from Arte TV API."""
    url = _ARTETV_URL + ARTETV_ENDPOINTS['program'].format(lang=lang, program_id=program_id)
    return _load_json_full_url(url, None).get('data', {})


def category(category_code, lang):
    """Get the info of category with category_code."""
    url = _HBBTV_ENDPOINTS['category'].format(category_code=category_code, lang=lang)
    return _load_json(url).get('category', {})


def collection(kind, collection_id, lang):
    """Get the info of collection collection_id"""
    url = _HBBTV_ENDPOINTS['collection'].format(
        kind=kind, collection_id=collection_id, lang=lang)
    sub_collections = _load_json(url).get('subCollections', [])
    return hof.flat_map(
        lambda sub_collections: sub_collections.get('videos', []),
        sub_collections)


def video(program_id, lang):
    """Get the info of content program_id from HBB TV API."""
    url = _HBBTV_ENDPOINTS['video'].format(
        program_id=program_id, lang=lang)
    return _load_json(url).get('videos', [])[0]


def streams(kind, program_id, lang):
    """Get the stream info of content program_id."""
    url = _HBBTV_ENDPOINTS['streams'].format(
        kind=kind, program_id=program_id, lang=lang)
    return _load_json(url).get('videoStreams', [])

def page_content(lang):
    """Get content to be display in a page. It can be a page for a category or the home page."""
    url = ARTETV_RPROXY_URL + ARTETV_ENDPOINTS['page'].format(
        lang=lang, category='HOME', client='tv')
    return _load_json_full_url(url, ARTETV_HEADERS).get('value', [])

def search(lang, query, page='1'):
    """Search for content in Arte TV API.
    /emac/v4/{lang}/{client}/pages/SEARCH/?page={page}&query={query}
    """
    url = ARTETV_RPROXY_URL + ARTETV_ENDPOINTS['page'].format(
        lang=lang, category='SEARCH', client='tv')
    params = {'page' : page, 'query' : query}
    return _load_json_full_url(url, ARTETV_HEADERS, params).get('value', []).get('zones', [None])[0]

def _load_json(path, headers=None):
    """Deprecated since 2022. Prefer building url on client side"""
    if headers is None:
        headers = _HBBTV_HEADERS
    url = _HBBTV_URL + path
    return _load_json_full_url(url, headers)

def _load_json_full_url(url, headers=None, params=None):
    if headers is None:
        headers = _HBBTV_HEADERS
    # https://requests.readthedocs.io/en/latest/
    reply = requests.get(url, headers=headers, params=params, timeout=10)
    return reply.json(object_pairs_hook=OrderedDict)

def _load_json_personal_content(plugin, url, usr, pwd, hdrs=None):
    """Get a bearer token and add it in headers before sending the request"""
    if hdrs is None:
        hdrs = ARTETV_HEADERS
    headers = _add_auth_token(plugin, usr, pwd, hdrs)
    if not headers:
        return None
    return _load_json_full_url(url, headers).get('data', [])

# Get a bearer token and add it as HTTP header authorization
def _add_auth_token(plugin, usr, pwd, hdrs):
    tkn = get_and_persist_token(plugin, usr, pwd)
    if not tkn:
        return None
    headers = hdrs.copy()
    headers['authorization'] = tkn['token_type'] + ' ' + tkn['access_token']
    # web client needed to reuse token. Otherwise API rejects with
    # {"error":"invalid_client","error_description":"Client not authorized"}
    headers['client'] = 'web'
    return headers


def get_and_persist_token(plugin, username='', password='', headers=None):
    """Log in user thanks to his/her settings and get a bearer token.
    Return None if:
        - any parameter is empty
        - silenty if both parameters are empty
        - with a notification if one is not empty
        - connection to arte tv failed"""
    if headers is None:
        headers = ARTETV_HEADERS
    # unable to authenticate if either username or password are empty
    if not username and not password:
        plugin.notify(msg=plugin.addon.getLocalizedString(30022), image='info')
        return None
    # inform that settings are incomplete
    if not username or not password:
        msg = f"{plugin.addon.getLocalizedString(30020)} : {plugin.addon.getLocalizedString(30021)}"
        plugin.notify(msg=msg, image='warning')
        return None

    cached_token = plugin.get_storage('token', TTL=24*60)
    token_idx = f"{username}_{hash(password)}"
    if token_idx in cached_token:
        tkn_data = cached_token[token_idx]
        xbmc.log(f"\"{username}\" already authenticated to Arte TV : {tkn_data['access_token']}")
        return tkn_data

    # set client to web, because with tv get error client_invalid, error Client not authorized
    headers['client'] = 'web'

    tokens = authenticate_in_arte(plugin, username, password, headers)
    # exit if authentication failed
    if not tokens:
        return None

    # try to persist token in arte to be allowed to reuse; otherwise token is one-shot
    if persist_token_in_arte(plugin, tokens, headers):
        # token persisted remotly are stored in kodi cache to be reused
        cached_token[token_idx] = tokens
        xbmc.log(f"\"{username}\" is successfully authenticated to Arte TV")
        xbmc.log(f"Token persisted for a day \"{tokens['access_token']}\"")
    # return persisted or unpersisted token anyway
    return tokens


def authenticate_in_arte(plugin, username='', password='', headers=None):
    """Return None if authentication failed and display an error notification
    Return arte reply with access and refresh tokens if authentication was successfull
    (i.e. status 200, no exception)"""
    if headers is None:
        headers = ARTETV_HEADERS
    url = _ARTETV_URL + ARTETV_ENDPOINTS['token']
    token_data = {
        'anonymous_token': None,
        'grant_type': 'password',
        'username': username,
        'password': password
    }
    xbmc.log(f"Try authenticating \"{username}\" to Arte TV")
    error = None
    reply = None
    try:
        # https://requests.readthedocs.io/en/latest/
        reply = requests.post(url, data=token_data, headers=headers, timeout=10)
    except requests.exceptions.ConnectionError as err:
        # unable to auth. e.g.
        # HTTPSConnectionPool(host='api.arte.tv', port=443):
        # Max retries exceeded with url: /api/sso/v3/token
        error = err
    if error or not reply or reply.status_code != 200:
        plugin.notify(msg=plugin.addon.getLocalizedString(30020), image='error')
        err_dtls = str(error) if error else (reply.text if reply is not None else '')
        xbmc.log(f"Unable to authenticate to Arte TV : {err_dtls}")
        return None
    return reply.json(object_pairs_hook=OrderedDict)

def persist_token_in_arte(plugin, tokens, headers):
    """Calls the sequence of 2 services to be able to reuse authentication token
    Return True, if token is persisted, False otherwise.
    Notify the user with a warning if persistance failed.
    """
    # constants taken from my reverse engineering
    api_key = '97598990-f0af-427b-893e-9da348d9f5a6'
    cookies = {
        'TCPID' : '123261154911117061452',
        # pylint: disable=line-too-long
        'TC_PRIVACY' : '1%40031%7C29%7C3445%40%40%401677322453596%2C1677322453596%2C1711018453596%40',
        'TC_PRIVACY_CENTER' : None
    }

    # step 1/2 : get additional cookies for step 2.
    url = _ARTETV_AUTH_URL + ARTETV_ENDPOINTS['custom_token']
    params = {
        'shouldValidateAnonymous' : False,
        'token' : tokens['access_token'],
        'apikey' : api_key,
        'isrememberme' : True
    }
    error = None
    cstm_tkn = None
    try:
        cstm_tkn = requests.get(url,params=params, headers=headers, cookies=cookies, timeout=10)
    except requests.exceptions.ConnectionError as err:
        error = err
    if error or not cstm_tkn or cstm_tkn.status_code != 200:
        plugin.notify(msg=plugin.addon.getLocalizedString(30020), image='warning')
        err_dtls = str(error) if error else (cstm_tkn.text if cstm_tkn is not None else '')
        xbmc.log(f"Unable to persist Arte TV token {tokens['access_token']}. Step 1/2: {err_dtls}")
        return False

    # step 2/2 : persist / remember token so that it can be reused
    url = _ARTETV_AUTH_URL + ARTETV_ENDPOINTS['login']
    params = {'shouldValidateAnonymous' : 'false', 'apikey' : api_key}
    cookies = hof.merge_dicts(cookies, cstm_tkn.cookies)
    login = None
    try:
        login = requests.get(url,params=params, headers=headers, cookies=cookies, timeout=10)
    except requests.exceptions.ConnectionError as err:
        error = err
    if error or not login or login.status_code != 200:
        plugin.notify(msg=plugin.addon.getLocalizedString(30020), image='warning')
        err_dtls = str(error) if error else (login.text if login is not None else '')
        xbmc.log(f"Unable to persist Arte TV token {tokens['access_token']}. Step 2/2: {err_dtls}")
        return False

    return True
