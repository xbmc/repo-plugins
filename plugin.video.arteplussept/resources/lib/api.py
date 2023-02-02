from addon import PluginInformation
from collections import OrderedDict
import requests
from xbmcswift2 import xbmc
from . import hof


# Arte hbbtv - deprecated API since 2022 prefer Arte TV API
_base_api_url = 'http://www.arte.tv/hbbtvv2/services/web/index.php'
_base_headers = {
    'user-agent': PluginInformation.name + '/' + PluginInformation.version
}
_endpoints = {
    'categories': '/EMAC/teasers/{type}/v2/{lang}',
    'category': '/EMAC/teasers/category/v2/{category_code}/{lang}',
    'subcategory': '/OPA/v3/videos/subcategory/{sub_category_code}/page/1/limit/100/{lang}',
    # 'magazines': '/OPA/v3/magazines/{lang}', # moved to arte tv api
    'collection': '/EMAC/teasers/collection/v2/{collection_id}/{lang}',
    # program details
    'video': '/OPA/v3/videos/{program_id}/{lang}',
    # program streams
    'streams': '/OPA/v3/streams/{program_id}/{kind}/{lang}',
    'daily': '/OPA/v3/programs/{date}/{lang}'
}


# Arte TV API - Used on Arte TV website
_artetv_url = 'https://api.arte.tv/api'
_artetv_rproxy_url = 'https://arte.tv/api/rproxy'
_artetv_endpoints = {
    'token': '/sso/v3/token', # POST
    'get_favorites': '/sso/v3/favorites/{lang}?page={page}&limit={limit}', # needs token in authorization header
    'add_favorite': '/sso/v3/favorites', #PUT needs token in authorization header
    'remove_favorite': '/sso/v3/favorites/{program_id}', #DELETE needs token in authorization header
    'get_last_viewed': '/sso/v3/lastvieweds/{lang}?page={page}&limit={limit}', # needs token in authorization header
    'sync_last_viewed': '/sso/v3/lastvieweds', # payload {"programId":"110342-012-A","timecode":574} for 574s i.e. 9:34
    'purge_last_viewed': '/sso/v3/lastvieweds/purge', # PATCH empty payload
    'magazines': '/sso/v3/magazines/{lang}?page={page}&limit={limit}',
    'program': '/player/v2/config/{lang}/{program_id}', # program_id can be 103520-000-A or LIVE
    'page': '/emac/v4/{lang}/{client}/pages/{category}/', #rproxy category=HOME, CIN, SER, SEARCH client=app, tv, web, orange, free
    # not yet impl. 'guide_tv': '/emac/v3/{lang}/{client}/pages/TV_GUIDE/?day={DATE}', #rproxy date=2023-01-17
}
_artetv_headers = {
    'authorization': 'I6k2z58YGO08P1X0E8A7VBOjDxr8Lecg', # required to use token endpoint
    'client': 'tv', # required for Arte TV API. values like web, app, tv, orange, free
    'accept': 'application/json'
}

# Retrieve favorites from a personal account.
def get_favorites(plugin, lang, usr, pwd):
    url = _artetv_url + _artetv_endpoints['get_favorites'].format(lang=lang, page='1', limit='50')
    return _load_json_personal_content(plugin, url, usr, pwd)

def add_favorite(plugin, usr, pwd, program_id):
    url = _artetv_url + _artetv_endpoints['add_favorite']
    headers = _add_auth_token(plugin, usr, pwd, _artetv_headers)
    data = {'programId': program_id}
    r = requests.put(url, data=data, headers=headers)
    return r.status_code

def remove_favorite(plugin, usr, pwd, program_id):
    url = _artetv_url + _artetv_endpoints['remove_favorite'].format(program_id=program_id)
    headers = _add_auth_token(plugin, usr, pwd, _artetv_headers)
    r = requests.delete(url, headers=headers)
    return r.status_code

# Retrieve content recently watched by a user.
def get_last_viewed(plugin, lang, usr, pwd):
    url = _artetv_url + _artetv_endpoints['get_last_viewed'].format(lang=lang, page='1', limit='50')
    return _load_json_personal_content(plugin, url, usr, pwd)

def sync_last_viewed(plugin, usr, pwd, program_id, time):
    url = _artetv_url + _artetv_endpoints['sync_last_viewed']
    headers = _add_auth_token(plugin, usr, pwd, _artetv_headers)
    data = {'programId': program_id, "timecode": time}
    r = requests.put(url, data=data, headers=headers)
    return r.status_code

def purge_last_viewed(plugin, usr, pwd):
    url = _artetv_url + _artetv_endpoints['purge_last_viewed']
    headers = _add_auth_token(plugin, usr, pwd, _artetv_headers)
    r = requests.patch(url, data={}, headers=headers)
    return r.status_code

def program_video(lang, program_id):
    url = _artetv_url + _artetv_endpoints['program'].format(lang=lang, program_id=program_id)
    return _load_json_full_url(url, None).get('data', {})


def categories(lang):
    url = _endpoints['categories'].format(type='categories', lang=lang)
    return _load_json(url).get('categories', {})


def home_category(name, lang):
    url = _endpoints['categories'].format(type='home', lang=lang)
    return _load_json(url).get('teasers', {}).get(name, [])


def category(category_code, lang):
    url = _endpoints['category'].format(category_code=category_code, lang=lang)
    return _load_json(url).get('category', {})


def subcategory(sub_category_code, lang):
    url = _endpoints['subcategory'].format(
        sub_category_code=sub_category_code, lang=lang)
    return _load_json(url).get('videos', {})


def collection(kind, collection_id, lang):
    url = _endpoints['collection'].format(kind=kind,
                                          collection_id=collection_id, lang=lang)
    subCollections = _load_json(url).get('subCollections', [])
    return hof.flat_map(lambda subCollections: subCollections.get('videos', []), subCollections)


def video(program_id, lang):
    url = _endpoints['video'] .format(
        program_id=program_id, lang=lang)
    return _load_json(url).get('videos', [])[0]


def streams(kind, program_id, lang):
    url = _endpoints['streams'] .format(
        kind=kind, program_id=program_id, lang=lang)
    return _load_json(url).get('videoStreams', [])


def magazines(lang):
    url = _artetv_url + _artetv_endpoints['magazines'].format(lang=lang, page='1', limit='50')
    return _load_json_full_url(url, _artetv_headers).get('data')


def daily(date, lang):
    url = _endpoints['daily'].format(date=date, lang=lang)
    return _load_json(url).get('programs', [])

# Get content to be display in a page. It can be a page for a category or the home page.
def page(lang):
    url = _artetv_rproxy_url + _artetv_endpoints['page'].format(lang=lang, category='HOME', client='tv')
    return _load_json_full_url(url, _artetv_headers).get('value', [])

# /emac/v4/{lang}/{client}/pages/SEARCH/?page={page}&query={query}
def search(lang, query, page='1'):
    url = _artetv_rproxy_url + _artetv_endpoints['page'].format(lang=lang, category='SEARCH', client='tv')
    params = {'page' : page, 'query' : query}
    return _load_json_full_url(url, _artetv_headers, params).get('value', []).get('zones', [None])[0]

# Deprecated since 2022. Prefer building url on client side
def _load_json(path, headers=_base_headers):
    url = _base_api_url + path
    return _load_json_full_url(url, headers)

def _load_json_full_url(url, headers=_base_headers, params=None):
    # https://requests.readthedocs.io/en/latest/
    r = requests.get(url, headers=headers, params=params)
    return r.json(object_pairs_hook=OrderedDict)

# Get a bearer token and add it in headers before sending the request
def _load_json_personal_content(plugin, url, usr, pwd, hdrs=_artetv_headers):
    headers = _add_auth_token(plugin, usr, pwd, hdrs)
    if not headers:
        return None
    return _load_json_full_url(url, headers).get('data', [])

# Get a bearer token and add it as HTTP header authorization
def _add_auth_token(plugin, usr, pwd, hdrs):
    tkn = token(plugin, usr, pwd)
    if not tkn:
        return None
    headers=hdrs.copy()
    headers['authorization'] = tkn['token_type'] + ' ' + tkn['access_token']
    return headers

# Log in user thanks to his/her settings and get a bearer token
# return None if:
#   - any parameter is empty
#     - silenty if both parameters are empty
#     - with a notification if one is not empty
#   - connection to arte tv failed
def token(plugin, username="", password="", headers=_artetv_headers):
    # unable to authenticate if either username or password are empty
    if not username and not password:
        plugin.notify(msg=plugin.addon.getLocalizedString(30022), image='info')
        return None
    # inform that settings are incomplete
    if not username or not password:
        msg = plugin.addon.getLocalizedString(30020) + " : " + plugin.addon.getLocalizedString(30021)
        plugin.notify(msg=msg, image='warning')
        return None

    url = _artetv_url + _artetv_endpoints['token']
    token_data = {'anonymous_token': None, 'grant_type': 'password', 'username': username, 'password': password}
    # set to web, because with tv get error client_invalid, error Client not authorized
    headers['client'] = 'web'
    try:
        # https://requests.readthedocs.io/en/latest/
        r = requests.post(url, data=token_data, headers=headers)
    except requests.exceptions.ConnectionError as err:
        # unable to auth. e.g.
        # HTTPSConnectionPool(host='api.arte.tv', port=443): Max retries exceeded with url: /api/sso/v3/token
        plugin.notify(msg=plugin.addon.getLocalizedString(30020), image='warning')
        xbmc.log('Unable to authenticate to Arte TV : {err_str}'.format(err_str=err))
        return None
    return r.json(object_pairs_hook=OrderedDict)
