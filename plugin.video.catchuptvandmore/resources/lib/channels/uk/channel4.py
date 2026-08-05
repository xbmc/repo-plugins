# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# Copyright: (c) 2023-2026 team CUTVM
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More
# Partially based on Diazole's work (https://github.com/Diazole/c4-dl)


import base64
import re
import sys
import json
import time
from builtins import str

import xbmc
import xbmcgui
import xbmcplugin
from kodi_six import xbmcvfs

import requests
from codequick import Listitem, Script, Resolver, Route, utils
from codequick.support import dispatcher
import urlquick

from resources.lib.kodi_utils import get_kodi_version, get_selected_item_art, get_selected_item_label, get_selected_item_info, INPUTSTREAM_PROP
from resources.lib.menu_utils import item_post_treatment
from resources.lib.py_utils import datetime_strptime

from resources.lib import web_utils

try:
    from Crypto.Cipher import AES
except ImportError:
    from Cryptodome.Cipher import AES

try:
    from Crypto.Util.Padding import unpad
except ImportError:
    from Cryptodome.Util.Padding import unpad

CACHE_FILE = 'special://userdata/addon_data/plugin.video.catchuptvandmore/channel4_auth.json'
URL_ROOT = 'https://www.channel4.com'
AUTH_ENV = 'https://api.channel4.com'
PREDICTIVE_SEARCH_URL = "https://all4nav.channel4.com/v1/api/search"
URL_API_HOMEPAGE = 'https://www.channel4.com/api/homepage'
URL_AUTH_TOKEN = AUTH_ENV + '/online/v2/auth/token'
URL_CATEGORIES = URL_ROOT + '/categories'
URL_PROGRAMMES = URL_ROOT + '/programmes'
URL_VOD_API = AUTH_ENV + '/online/v1/vod/stream/{programme_id}?client={client}'
URL_VOD_WEB = URL_ROOT + '/vod/stream/'
URL_LICENSE = 'https://c4.eme.lp.aws.redbeemedia.com/wvlicenceproxy-service/widevine/acquire'

URL_LIVE_WEB = URL_ROOT + '/simulcast/channels/%s'

AUTH_TOKEN_HEADERS = {"authorization": "Basic eUExTHB6dGtHZUhaRDZuU2E3QzFBQUY2dkhwelZOblU6UXFFbUVnVVVVT1hUa3piNg=="}
BASIC_HEADERS = {'User-Agent': web_utils.get_random_ua()}
LICENSE_HEADERS = "User-Agent=%s&Content-Type=application/json&Referer=%s" % (web_utils.get_random_ua(), URL_ROOT)
API_CLIENT = 'amazonfire-dash'

KEYS = {
    # Keys associated with `API_CLIENT`
    'api': {
        'key': 'K2C8Q09D7HJ385AB',
        'iv': 'B3LKVU05F3IDLVME'
    },
    'web': {
        'key': 'n9cLieYkqwzNCqvi',
        'iv': 'odzcU3WdUiXLucVd'
    }
}

REQ_TIMEOUT = (3.5, 10)
DFLT_CACHE_TIME = 600

TXT_INFORMATION = 30600
TXT_ACCOUNT_REQUIRED = 30604
TXT_ENTER_UNAME = 30733
TXT_ENTER_PASSW = 30734
TXT_LOGIN_SUCCESS = 30735
TXT_LOGOUT_SUCCESS = 30736
TXT_ALREADY_LOGGED_OUT = 30737


# -----------------------------------------------------------------------------
#           AUTHENTICATION
# -----------------------------------------------------------------------------

def get_token_if_valid(channel4_auth):
    if channel4_auth and channel4_auth.get('accessToken'):
        issued_at = channel4_auth['issuedAt']
        expires_in = channel4_auth['expiresIn']
        expiration_time = (int(issued_at) / 1000) + int(expires_in)
        if expiration_time > time.time():
            return channel4_auth.get('accessToken')
    return None


def get_access_token(silent=True):
    try:
        channel4_auth = getattr(get_access_token, '_channel4_auth', None)
        if channel4_auth is None:
            channel4_auth = get_access_token._channel4_auth = load_channel4_auth()
        token = get_token_if_valid(channel4_auth)
        if token:
            return token
        refresh_token = channel4_auth.get('refreshToken')
        if refresh_token:
            token = refresh(refresh_token)
            if token:
                return token
    except Exception as e:
        if not silent and not getattr(e, 'recoverable', None):
            raise e
        else:
            Script.log('[UK-CHAN4] Failed to get an access token: %r', (e,), lvl=Script.ERROR)

    # User is not logged in.
    if not silent:
        xbmcgui.Dialog().ok(
            Script.localize(TXT_INFORMATION),
            Script.localize(TXT_ACCOUNT_REQUIRED) % ('Channel 4 (UK)', URL_ROOT + '/register'))
    return None


def refresh(refresh_token):
    """Perform a token refresh at the backend"""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    r = requests.post(URL_AUTH_TOKEN, headers=AUTH_TOKEN_HEADERS, data=data, timeout=REQ_TIMEOUT)
    try:
        res = json.loads(r.content)
        if "error" in res:
            e = RuntimeError(f'Failed to refresh token - {res["errorCode"]}: {res["errorMessage"]}')
            setattr(e, 'recoverable', r.status_code == 401)
            raise e
    except (json.JSONDecodeError, KeyError):
        r.raise_for_status()

    # noinspection unbound-local-variable
    save_channel4_auth(res)
    return res['accessToken']


def login(uname, passw):
    """Perform a login request to the backend with email and password.

    Return a dict with tokens on success, or None on a failure that could be resolved by
    re-trying with a different username, or password. Any other error will raise an exception.
    """
    data = {
        "grant_type": "password",
        "username": uname,
        "password": passw,
    }
    r = requests.post(URL_AUTH_TOKEN, headers=AUTH_TOKEN_HEADERS, data=data, timeout=REQ_TIMEOUT)
    # Both actual content and most error responses are JSON.
    try:
        res = json.loads(r.content)

        if "error" in res:
            if res['errorCode'] == 10002:
                err_message = 'Invalid email'
            else:
                err_message = res['errorMessage']
            Script.log('[UK-CHAN4] Failed to login: ' + res['errorMessage'])
            Script.notify('Channel 4 ERROR', err_message, icon=Script.NOTIFY_ERROR, display_time=7000)
            return None
    except (json.JSONDecodeError, KeyError):
        r.raise_for_status()

    save_channel4_auth(res)
    return res['accessToken']


def revoke_token(refresh_tkn):
    """Perform the usual procedure of logging out by revoking the refresh token."""
    try:
        urlquick.post(AUTH_ENV + '/online/v2/auth/revoke',
                      headers=AUTH_TOKEN_HEADERS,
                      data={'token_type_hint': 'refresh_token',
                            'token': refresh_tkn,
                            'grant_type': 'refresh_token'},
                      timeout=(3.5, 2),
                      max_age=-1)
    except requests.RequestException:
        pass


def enter_credentials(uname, passw):
    """Open the keyboard and ask the user to enter their username and password."""
    new_username = utils.keyboard(Script.localize(TXT_ENTER_UNAME), uname or '')
    if new_username:
        new_passw = utils.keyboard(Script.localize(TXT_ENTER_PASSW), passw or '', hidden=True)
    else:
        new_passw = ''
    return new_username, new_passw


@Script.register
def sign_in_account(addon):
    """Entry point for the action 'Log in to channel 4 account' in settings.

    Ask the user to enter his username and password, try to log in and inform the
    user of success or failure. On failure, keep asking for username or password
    until log in succeeds, or the user cancels the keyboard.

    """
    uname = None
    passw = None

    while True:
        uname, passw = enter_credentials(uname, passw)
        if not all((uname, passw)):
            return
        if login(uname, passw):
            xbmcgui.Dialog().ok('Channel 4', Script.localize(TXT_LOGIN_SUCCESS))
            # Rebuild the current list with add/remove mylist context menus for the new user.
            get_mylist_programmes._my_list_pgms = None
            xbmc.executebuiltin('Container.Refresh')
            return


@Script.register
def sign_out_account(_):
    """Entry point for the action 'Log out from channel 4 account' in settings."""
    auth_data = load_channel4_auth()
    refresh_tkn = auth_data.get('refreshToken')
    save_channel4_auth({})
    get_mylist_programmes._my_list_pgms = False
    if refresh_tkn:
        revoke_token(refresh_tkn)
        xbmcgui.Dialog().ok('Channel 4', Script.localize(TXT_LOGOUT_SUCCESS))
    else:
        xbmcgui.Dialog().ok('Channel 4', Script.localize(TXT_ALREADY_LOGGED_OUT))
    # Rebuild the current list without add/remove mylist context menus.
    xbmc.executebuiltin('Container.Refresh')


def load_channel4_auth():
    try:
        with xbmcvfs.File(CACHE_FILE, 'r') as f1:
            channel4_auth = f1.read()
            return json.loads(channel4_auth)
    except (OSError, json.JSONDecodeError) as err:
        Script.log(f'[UK-CHAN4] Error reading token file: {err!r}.')
        return {}


def save_channel4_auth(channel4_auth):
    # Remove redundant data.
    try:
        channel4_auth['user'] = {
            'uuid': channel4_auth['user']['uuid'],
            'displayName': channel4_auth['user']['displayName']
        }
        del channel4_auth['securityToken']
    except KeyError:
        pass
    get_access_token._channel4_auth = channel4_auth
    with xbmcvfs.File(CACHE_FILE, 'w') as f1:
        json.dump(channel4_auth, f1, ensure_ascii=False, indent=4)


def authenticated_request(method, url, silent=True, **kwargs):
    """Make a request with user authentication. Return the requests.Response object,
    or None if the user is not signed in to Channel4.

    If `silent` is False and the user is not logged in with a Channel 4 account,
    a message dialog will be shown informing the user that account login is required.

    """
    token = get_access_token(silent)
    if not token:
        return None

    headers = {
        'user-agent': web_utils.get_random_ua(),
        'authorization': 'Bearer ' + token,
    }
    headers.update(kwargs.get('headers', {}))
    kwargs['headers'] = headers
    params = kwargs.setdefault('params', {})
    params.update(client=API_CLIENT)
    kwargs.setdefault('timeout', REQ_TIMEOUT)
    kwargs.setdefault('max_age', -1)
    return urlquick.request(method, url, **kwargs)


# -----------------------------------------------------------------------------
#           My4 Utils
# -----------------------------------------------------------------------------

def get_mylist_programmes(force_refresh=False):
    """Return a set of all brand titles currently on 'My List', or False if
    the user is not signed in.

    This is used by the context menu on video items to add or remove them
    from 'My List'.
    The list is fetched on demand and cached in memory for subsequent use,
    unless the parameter `force_refresh` is True.
    """
    my_pgms = getattr(get_mylist_programmes, '_my_list_pgms', None)

    try:
        if my_pgms is None or force_refresh:
            cache_age = 0 if force_refresh else 20
            my_list_data = get_my_four('MYLIST', False, cache_age)
            if my_list_data is None:
                # Not signed in
                get_mylist_programmes._my_list_pgms = my_pgms = False
            else:
                my_pgms = set(item['brand']['websafeTitle']
                              for item in my_list_data['sliceItems']
                              if item['type'] == 'brand')
                get_mylist_programmes._my_list_pgms = my_pgms
    except (KeyError, TypeError):
        # The data structure has changed. Makes no sense to retry but prevents the whole channel from crashing,
        get_mylist_programmes._my_list_pgms = my_pgms = False
    except Exception:
        get_mylist_programmes._my_list_pgms = None
        raise
    return my_pgms


def add_my_list_context_menu(list_item, brand_name):
    """Add a context menu item to `list_item` to allow a user to add or remove
    the programme to channel 4's 'My List', depending on whether the programme
    is already on the list.

    Does not add a context menu when the user is not signed in.
    """
    cur_mylist = get_mylist_programmes()
    if cur_mylist in (False, None):
        return

    if brand_name in cur_mylist:
        list_item.context.script(edit_mylist,
                                 "Remove from Chan 4's My List",
                                 operation='remove',
                                 brand_name=brand_name)
    else:
        list_item.context.script(edit_mylist,
                                 "Add to Chan 4's My List",
                                 operation='add',
                                 brand_name=brand_name)


@Script.register
def edit_mylist(_, operation, brand_name):
    """Add to, or remove the item from My List.

    Handler for the context menu options 'Add/Remove to/from channel 4's My List'.

    :param str operation: The operation to perform, either `add` or `delete`
    :param str brand_name: The web safe title of the brand.

    """
    access_token = get_access_token(silent=False)
    if not access_token:
        return

    url = f'https://api.channel4.com/online/v1/user/favourites/{brand_name}.json'
    method = 'post' if operation == 'add' else 'delete'
    resp = authenticated_request(method, url, headers={'pragma': 'no-cache'}, silent=False)
    if resp and 200 <= resp.status_code < 300:
        get_mylist_programmes(force_refresh=True)
        xbmc.executebuiltin('Container.Refresh')


@Script.register
def remove_from_history(_, programme_id):
    """Remove a programme from the 'continue watching' or 'history' list.

    Handler for the context menu items 'Remove from watching' and 'Remove from history'.
    """
    authenticated_request('DELETE',
                          AUTH_ENV + f'/online/v1/user/history/{programme_id}.json',
                          silent=False)
    # Ensure urlquick's cache is refreshed.
    get_my_four('HISTORY', max_age=0)
    xbmc.executebuiltin('Container.Refresh')


def get_my_four(list_type, notify_login=True, max_age=20):
    """Request My4 data and return one of its lists."""
    resp = authenticated_request(method='get',
                                 url=AUTH_ENV + '/online/v1/views/my4.json',
                                 silent=not notify_login,
                                 max_age=max_age)
    if resp:
        data = json.loads(resp.content)
        for slice_item in data['sliceGroups'][0]['slices']:
            if slice_item['type'] == list_type:
                return slice_item
    return None


def report_playtime(evt, programme_id, end_credits):
    """Report the playing time of a VOD programme back to channel4 while it's playing."""
    end_time = end_credits if end_credits else evt.total_time - 20
    play_time = int(evt.play_time)
    if play_time >= end_time:
        play_time = 0
    else:
        play_time = max(1, play_time)

    result = authenticated_request('PUT',
                                   AUTH_ENV + f'/online/v1/user/history/{programme_id}/{play_time}.json',
                                   headers={'Pragma': 'no-cache',
                                            'Cache-Control': 'no-cache'},
                                   json={})
    return result is not None and play_time < end_time


# -----------------------------------------------------------------------------
#           CONTENT
# -----------------------------------------------------------------------------

@Route.register(content_type="videos")
def do_search(plugin, search_query):
    params = {
        "expand": "default",
        "q": search_query,
        "limit": 100,
        "offset": 0
    }

    resp = urlquick.get(PREDICTIVE_SEARCH_URL,
                        headers=BASIC_HEADERS,
                        params=params,
                        timeout=REQ_TIMEOUT,
                        max_age=-1)
    search_json = json.loads(resp.text)

    results = search_json.get("results", [])
    if isinstance(results, dict):
        # No results found
        xbmcgui.Dialog().ok('No Matches', results.get('summary', 'No items found'))
        yield False
        return

    for result in results:
        if result:
            brand = result["brand"]
            label = brand.get("label")
            item = Listitem()
            item.label = brand.get("title")
            thumbnail_url = brand.get("thumbnailUrl")
            thumbnail_url = web_utils.remove_params(thumbnail_url)  # Remove params lowering resolution
            item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = thumbnail_url
            url = brand.get("href")
            plot = brand.get("description")
            if label:
                plot = plot + '\n\n' + label
            item.info["plot"] = plot
            item.set_callback(list_seasons, url=url)
            add_my_list_context_menu(item, brand['websafeTitle'])
            item_post_treatment(item)
            yield item


@Route.register
def main_menu(plugin, **kwargs):
    yield Listitem.from_dict(
        callback=submenu_my4,
        label='My4'
    )
    yield Listitem.search(do_search)

    yield Listitem.from_dict(
        callback=list_categories,
        label='Categories'
    )

    try:
        resp = urlquick.get(URL_API_HOMEPAGE,
                            headers=BASIC_HEADERS,
                            timeout=REQ_TIMEOUT,
                            max_age=DFLT_CACHE_TIME)
        json_data = json.loads(resp.text)
        for slice in json_data['slices']:
            if slice:
                label = slice.get('title')
                if label:
                    yield Listitem.from_dict(
                        callback=list_slice,
                        label=label,
                        params={'slice': slice}
                    )
                else:
                    for slice_item in slice['sliceItems']:
                        item = Listitem()
                        title = slice_item.get('title')
                        item.label = title
                        item.info['title'] = f'[B][COLOR orange]{title}[/COLOR][/B]'
                        item.info['plot'] = get_slice_item_plot(slice_item)
                        item.art['thumb'] = item.art['landscape'] = slice_item["image"]["href"]
                        slice_item_type = slice_item.get('type')
                        if slice_item_type == 'brand':
                            item.info['genre'] = slice_item.get('brand', {}).get('categories', [])
                            item.art['fanart'] = get_brand_fan_art(slice_item)
                            brand_name = slice_item['brand']['websafeTitle']
                            url_item = URL_PROGRAMMES + '/' + brand_name
                            item.set_callback(list_seasons, url=url_item)
                            add_my_list_context_menu(item, brand_name)
                            item_post_treatment(item)
                            yield item
    except Exception:
        pass


@Route.register
def submenu_my4(_):
    yield Listitem.from_dict(
        callback=list_my_four,
        label='My List',
        params={'list_type': 'MYLIST'}
    )
    yield Listitem.from_dict(
        callback=list_my_four,
        label='Watching',
        params={'list_type': 'CONTINUE_WATCHING', '_cache_to_disc_': False}
    )
    yield Listitem.from_dict(
        callback=list_my_four,
        label='History',
        params={'list_type': 'HISTORY'}
    )
    yield Listitem.from_dict(
        callback=list_my_four,
        label='Recommended for You',
        params={'list_type': 'RECOMMENDATIONS'}
    )


@Route.register
def list_my_four(plugin, list_type, **_):
    plugin.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED)
    my_list_data = get_my_four(list_type)
    if not my_list_data:
        # Not logged in; yield False to prevent an error notification.
        yield False
        return
    my_list_data['sliceItems'] = [item for item in my_list_data['sliceItems'] if item['type'] != 'freeform']
    if my_list_data['sliceItems']:
        yield from list_slice(plugin, my_list_data, list_type)
    else:
        # Just show an empty list - workaround to codequick reporting all empty lists as a failure to Kodi.
        xbmcplugin.endOfDirectory(dispatcher.handle, True)
        sys.exit()


def get_slice_item_plot(slice_item):
    plot = slice_item.get('summary')
    editorial_label = slice_item.get('editorialLabel')
    if editorial_label:
        plot = plot + '\n\n' + editorial_label
    return plot


def get_brand_fan_art(slice_item):
    images = slice_item.get('brand', {}).get('images', [])
    if images:
        for image in images:
            if image.get('imageType') == 'PRIMARY_HERO' or 'Apple_TV' in image.get('title'):
                return image.get('href')
    return None


def get_media_type(programme_type):
    if programme_type == 'FM':
        return 'movie'
    if programme_type in {'FB', 'MSU', 'MST', 'SSU'}:
        return 'episode'
    return 'video'


def extract_yyyy_mm_dd_date_str(date_label):
    try:
        if date_label:
            date_str = date_label.replace("First shown: ", "").strip()
            date_obj = datetime_strptime(date_str, "%a %d %b %Y")
            return date_obj.strftime("%Y-%m-%d")
    except Exception:
        pass
    return None


def parse_api_item_episode(episode_item, parent_list=None):
    """Parse episode data obtained from an app API endpoint, which returns
    more extensive data in a different format than endpoints used by the website.

    """
    item = Listitem()
    episode_data = episode_item['episode']
    try:
        stream_info = episode_data['assetInfo']['streaming']
    except KeyError:
        # The item is no longer available.
        return None
    brand_data = episode_item['brand']

    item.label = brand_title = episode_item['title']
    episode_title = episode_data['originalTitle'] or episode_data['title']
    seriesnr = episode_data.get('seriesNumber')
    episodenr = episode_data.get('episodeNumber')
    if 'episode' not in episode_title.lower():
        episode_title = f'{episode_title} - series {seriesnr}, episode {episodenr}'
    duration = stream_info['duration']
    programme_id = episode_data['programmeId']
    brand_ws_title = brand_data['websafeTitle']
    # Currently, all episodes obtained from an API endpoint are not listed in the context of
    # their series or programme, so it's safe to add a 'View all episodes' context menu item.
    item.context.container(list_seasons, 'View all episodes', url=URL_PROGRAMMES + '/' + brand_ws_title)

    resume_data = episode_data.get('resume')
    if resume_data:
        if resume_data['completed']:
            item.info['title'] = brand_title
        else:
            resume_point = resume_data['seconds']
            minutes_left = str(int((duration - resume_point) / 60))
            item.info['title'] = f'{brand_title} - [I]{minutes_left} mins left[/I]'
            item.property.update({
                'ResumeTime': str(resume_point),
                'TotalTime': str(duration)
            })
    else:
        if episode_data.get('newSeries'):
            title_addition = 'new series'
        elif episode_data.get('newEpisode'):
            title_addition = 'new episode'
        elif episode_data.get('nextEpisode'):
            title_addition = 'next episode'
        else:
            item.info['title'] = brand_title
            title_addition = None
        if title_addition:
            item.info['title'] = f'{brand_title} - [I]{title_addition}[/I]'

    item.info['season'] = seriesnr
    item.info['episode'] = episodenr
    item.info['mediatype'] = get_media_type(brand_data.get('programmeType'))
    item.info['duration'] = duration
    item.art['thumb'] = item.art['landscape'] = episode_data['image']['href'].replace('{&resize}', '&resize=512px:*')
    item.art['fanart'] = brand_data['image']['href']
    item.set_callback(get_video, programmeId=programme_id, assetId=stream_info['assetId'])

    item.info['plot'] = episode_title + '\n\n' + episode_data['summary']
    guidance = stream_info.get('guidance')
    if guidance:
        item.info['plot'] = item.info['plot'] + '\n\n' + guidance

    date = episode_data.get('firstTXDate') or stream_info['startDate']
    item.info.date(date[:10], '%Y-%m-%d')
    item.info['genre'] = brand_data['categories']

    # Note: It does happen that items on 'history' or 'continue watching' still don't have resume data.
    #       Best to simply add this context menu to episodes based on their containing list type.
    if parent_list == 'CONTINUE_WATCHING':
        item.context.script(remove_from_history, 'Remove from watching', programme_id=programme_id)
    elif parent_list == 'HISTORY':
        item.context.script(remove_from_history, 'Remove from history', programme_id=programme_id)
    add_my_list_context_menu(item, brand_ws_title)
    item_post_treatment(item)
    return item


@Route.register
def list_categories(plugin, **kwargs):
    html_text = urlquick.get(URL_CATEGORIES,
                             headers=BASIC_HEADERS,
                             timeout=REQ_TIMEOUT,
                             max_age=DFLT_CACHE_TIME).parse()
    for script in html_text.iterfind('.//script'):
        script_text = script.text
        if script_text is not None and script_text.split()[0] == 'window.__PARAMS__':
            data = json.loads(re.sub(r'^.*?{', '{', script_text).replace("undefined", "{}"))
            initial_data = data.get('initialData', {})
            if initial_data:
                category_links = initial_data.get('categoryLinks', [])
                if category_links:
                    for category_link in category_links:
                        item = Listitem()
                        item.label = category_link.get('tagName')
                        url_item = URL_ROOT + category_link.get('href')
                        item.set_callback(list_programs, url=url_item, offset='0')
                        item_post_treatment(item)
                        yield item


@Route.register
def list_slice(plugin, slice, list_type=None, **kwargs):
    for slice_item in slice['sliceItems']:
        slice_item_type = slice_item.get('type')

        if slice_item_type == 'ip':
            continue

        if slice_item_type == 'episode':
            yield parse_api_item_episode(slice_item, list_type)
            continue

        item = Listitem()

        if slice_item_type != 'slot':
            item.label = slice_item.get('title')
            item.info['plot'] = get_slice_item_plot(slice_item)
            item.art['thumb'] = item.art['landscape'] = slice_item["image"]["href"]

        if slice_item_type == 'brand':
            item.info['genre'] = slice_item.get('brand', {}).get('categories', [])
            item.art['fanart'] = get_brand_fan_art(slice_item)
            safe_title = slice_item['brand']['websafeTitle']
            url_item = URL_PROGRAMMES + '/' + safe_title
            item.set_callback(list_seasons, url=url_item)
            add_my_list_context_menu(item, safe_title)
        elif slice_item_type == 'freeform':
            url_item = slice_item.get('url')
            if not url_item:
                continue
            item.set_callback(list_programs, url=url_item, offset='0')
        elif slice_item_type == 'slot':
            slot_tx_channel = slice_item.get('slot').get('slotTXChannel')
            item.label = slot_tx_channel
            item.set_callback(get_live_url, item_id=slot_tx_channel)
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, url, offset, **kwargs):
    """
    Build programs listing
    """
    params = {
        'json': 'true',
        'offset': offset,
        'sort': Script.setting['uk.channel4.programmes.sort.by']
    }
    resp = urlquick.get(url,
                        headers=BASIC_HEADERS,
                        params=params,
                        timeout=REQ_TIMEOUT,
                        max_age=DFLT_CACHE_TIME)
    programs = json.loads(resp.text)
    programs_number = programs['noOfShows']

    for program in programs["brands"]["items"]:
        item = Listitem()
        item.label = program["labelText"]
        item.art['thumb'] = item.art['landscape'] = item.art['fanart'] = program["imageLink"]
        item.set_callback(list_seasons, url=program["hrefLink"])
        item.info["plot"] = program["overlayText"]
        expanded_tile = program.get("expandedTile")
        if expanded_tile:
            if "summary" in expanded_tile and expanded_tile["summary"]:
                item.info["plot"] = expanded_tile["summary"]
            if "genres" in expanded_tile and expanded_tile['genres']:
                item.info['genre'] = expanded_tile["genres"]
        add_my_list_context_menu(item, program['websafeTitle'])
        item_post_treatment(item)
        yield item

    nboffset = int(offset) + len(programs["brands"]["items"])
    if nboffset < programs_number:
        item = Listitem.next_page(url=url, offset=str(nboffset))
        item.property['SpecialSort'] = 'bottom'
        yield item


@Route.register
def list_seasons(plugin, url, **kwargs):
    html_text = urlquick.get(url,
                             headers=BASIC_HEADERS,
                             timeout=REQ_TIMEOUT,
                             max_age=DFLT_CACHE_TIME).parse()

    for script in html_text.iterfind('.//script'):
        script_text = script.text
        if script_text is not None and script_text.split()[0] == 'window.__PARAMS__':
            datas = json.loads(re.sub(r'^.*?{', '{', script_text).replace("undefined", "{}"))['initialData']['brand']
            brand_name = datas['websafeTitle']
            genres = []
            if "categories" in datas and datas['categories']:
                genres = [genre["displayName"].strip() for genre in datas["categories"]]
            fanart = datas.get('images', {}).get('hero', {}).get('landscape', {}).get('src', None)
            if bool(datas['allSeriesCount']) is False or len(datas['series']) == 0:
                for episode in datas['episodes']:
                    if episode.get('assetId'):
                        item = Listitem()
                        toreplace = re.compile(r'(.*?)Episode').findall(episode['title'])
                        if bool(toreplace):
                            item.label = episode['title'].replace(toreplace[0], '') + " ({})".format(episode['originalTitle'])
                        else:
                            item.label = episode['title'] + " ({})".format(episode['originalTitle'])
                        item.info['season'] = episode.get('seriesNumber')
                        item.info['episode'] = episode.get('episodeNumber')
                        item.info['mediatype'] = get_media_type(datas.get('programmeType'))
                        item.art['thumb'] = item.art['landscape'] = episode['image']['src']
                        item.art['fanart'] = fanart
                        item.set_callback(get_video, programmeId=episode['programmeId'], assetId=episode['assetId'])
                        item.info['plot'] = episode['summary']
                        if 'guidance' in episode and episode['guidance']:
                            item.info['plot'] = item.info['plot'] + '\n\n' + episode['guidance']
                        yyyy_mm_dd_date_str = extract_yyyy_mm_dd_date_str(episode.get('dateLabel'))
                        if yyyy_mm_dd_date_str:
                            item.info.date(yyyy_mm_dd_date_str, '%Y-%m-%d')
                        if 'durationLabel' in episode and episode['durationLabel']:
                            try:
                                item.info['duration'] = int(episode['durationLabel'].split()[0]) * 60
                            except Exception:
                                pass
                        item.info['genre'] = genres
                        add_my_list_context_menu(item, brand_name)
                        item_post_treatment(item)
                        yield item
            else:
                series = datas['series']
                for season in series:
                    series_number = season['seriesNumber']
                    item = Listitem()
                    item.label = season['title']
                    if 'image16x9' in datas['images']:
                        image = datas['images']['image16x9']['src']
                    else:
                        image = datas['images']['hero']['landscape']['src']
                    item.art['thumb'] = item.art['landscape'] = image
                    item.art['fanart'] = fanart
                    item.set_callback(get_episodes_list, series, series_number, datas)
                    item.info['plot'] = season['summary']
                    item.info['genre'] = genres
                    item.info['mediatype'] = 'season'
                    item.info['season'] = series_number
                    add_my_list_context_menu(item, brand_name)
                    item_post_treatment(item)
                    yield item


@Route.register
def get_episodes_list(plugin, series, series_number, datas, **kwargs):
    genres = []
    if "categories" in datas and datas['categories']:
        genres = [genre["displayName"].strip() for genre in datas["categories"]]
    fanart = datas.get('images', {}).get('hero', {}).get('landscape', {}).get('src', None)
    brand_name = datas['websafeTitle']
    for episode in datas['episodes']:
        if episode['seriesNumber'] == series_number and episode.get('assetId'):
            item = Listitem()
            toreplace = re.compile(r'(.*?)Episode').findall(episode['title'])
            if bool(toreplace):
                item.label = episode['title'].replace(toreplace[0], '') + " ({})".format(episode['originalTitle'])
            else:
                item.label = episode['title'] + " ({})".format(episode['originalTitle'])
            item.info['season'] = episode.get('seriesNumber')
            item.info['episode'] = episode.get('episodeNumber')
            item.info['mediatype'] = get_media_type(datas.get('programmeType'))
            item.art['thumb'] = item.art['landscape'] = episode['image']['src']
            item.art['fanart'] = fanart
            item.set_callback(get_video, programmeId=episode['programmeId'], assetId=episode['assetId'])
            item.info['plot'] = episode['summary']
            if 'guidance' in episode and episode['guidance']:
                item.info['plot'] = item.info['plot'] + '\n\n' + episode['guidance']
            yyyy_mm_dd_date_str = extract_yyyy_mm_dd_date_str(episode.get('dateLabel'))
            if yyyy_mm_dd_date_str:
                item.info.date(yyyy_mm_dd_date_str, '%Y-%m-%d')
            if 'durationLabel' in episode and episode['durationLabel']:
                try:
                    item.info['duration'] = int(episode['durationLabel'].split()[0]) * 60
                except Exception:
                    pass
            item.info['genre'] = genres
            add_my_list_context_menu(item, brand_name)
            item_post_treatment(item)
            yield item


# -----------------------------------------------------------------------------
#           PLAY STREAM
# -----------------------------------------------------------------------------

@Resolver.register
def get_video(plugin, programmeId, assetId, **kwargs):
    from resources.lib.prog_mon import start_progress_monitor

    access_token = get_access_token()
    if access_token and Script.setting.get_boolean('uk.channel4.high_quality'):  # Allows higher bitrate 1080p
        client_type = 'api'
        url_video_json = URL_VOD_API.format(programme_id=programmeId, client=API_CLIENT)
        headers = {"authorization": f"Bearer {access_token}"}
    else:
        client_type = 'web'
        url_video_json = URL_VOD_WEB + str(programmeId)
        headers = None

    resp = urlquick.get(url_video_json, headers=headers, timeout=REQ_TIMEOUT, max_age=-1)

    json_video = json.loads(resp.text)
    supported_video_profiles = {'bigscreendashwv-dyn-stream-1', 'dashwv-dyn-stream-1'}
    for field in json_video['videoProfiles']:
        if field['name'] in supported_video_profiles:
            token = field['streams'][0]['token']
            url = field['streams'][0]['uri']
            break

    endcredits_time = int(json_video.get('endCredits', {}).get('squeezeIn', 0) / 1000)

    subtitle_url = ''
    if plugin.setting.get_boolean('active_subtitle'):
        supported_subtitles_formats = ['srt_009', 'sami_001']
        if get_kodi_version() >= 20:
            supported_subtitles_formats.insert(0, 'webvtt_007')
        for subtitle_format in supported_subtitles_formats:
            if subtitle_url:
                break
            for field in json_video['subtitlesAssets']:
                if field['format'] == subtitle_format:
                    subtitle_url = field['url']
                    break

    keys = KEYS[client_type]
    cipher = AES.new(bytes(keys['key'], 'UTF-8'), AES.MODE_CBC, bytes(keys['iv'], 'UTF-8'))
    decoded_token = unpad(cipher.decrypt(base64.b64decode(token)), 16, style='pkcs7').decode('UTF-8').split('|')[1]

    payload = json.dumps({
        "request_id": assetId,
        "token": decoded_token,
        "video": {
            "type": "ondemand",
            "url": url
        },
        "message": "b{SSM}"
    })

    item = Listitem()
    item.path = url
    if 'http' in subtitle_url:
        item.subtitles.append(subtitle_url)
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = '%s|%s|%s|JBlicense' % (URL_LICENSE, LICENSE_HEADERS, payload)
    plugin.register_delayed(start_progress_monitor,
                            callback=report_playtime,
                            callb_kwargs={'programme_id': programmeId, 'end_credits': endcredits_time},
                            video_url=url,
                            heartbeat_interval=60)
    return item


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    client_type = 'web'
    url_video_json = URL_LIVE_WEB % item_id
    headers = None

    resp = urlquick.get(url_video_json, headers=headers, timeout=REQ_TIMEOUT, max_age=-1)

    json_video = json.loads(resp.text)
    for field in json_video['channelInfo']['videoProfiles']:
        if field['name'] == 'dashwv-live-stream-iso-dash-sp-tl':
            token = field['streams'][0]['token']
            url = field['streams'][0]['uri']
            break

    # Attempt to expose HD resolutions
    if url and "manifest_sd.mpd" in url:
        new_url = url.replace("manifest_sd.mpd", "manifest.mpd")
        try:
            response = requests.head(new_url, allow_redirects=True, timeout=5)
            if response.status_code == 200:
                url = new_url
        except requests.RequestException as e:
            Script.log(f'[UK-CHAN4] Requesting HD live manifest failed: {e!r}')

    keys = KEYS[client_type]
    cipher = AES.new(bytes(keys['key'], 'UTF-8'), AES.MODE_CBC, bytes(keys['iv'], 'UTF-8'))
    full_decoded_token = unpad(cipher.decrypt(base64.b64decode(token)), 16, style='pkcs7').decode('UTF-8')
    decoded_token = re.compile(r'\&t\=(.*?)$').findall(full_decoded_token)[0]

    payload = json.dumps({
        "token": decoded_token,
        "video": {
            "type": "simulcast",
            "url": url
        },
        "message": "b{SSM}"
    })

    item = Listitem()
    item.path = url
    item.label = get_selected_item_label()
    item.art.update(get_selected_item_art())
    item.info.update(get_selected_item_info())
    item.property[INPUTSTREAM_PROP] = 'inputstream.adaptive'
    item.property['inputstream.adaptive.manifest_type'] = 'mpd'
    item.property['inputstream.adaptive.license_type'] = 'com.widevine.alpha'
    item.property['inputstream.adaptive.license_key'] = '%s|%s|%s|JBlicense' % (URL_LICENSE, LICENSE_HEADERS, payload)

    return item
