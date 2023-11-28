"""
Stalker API Calls
"""
from __future__ import absolute_import, division, unicode_literals
import math
import requests
from .globals import G
from .auth import Auth


def __call_stalker_portal(params):
    """Method to call portal"""
    retries = 0
    _url = G.portal_config.portal_base_url + G.portal_config.context_path
    _mac_cookie = G.portal_config.mac_cookie
    _portal_url = G.portal_config.portal_url
    _auth = Auth()
    while True:
        token = _auth.get_token()
        response = requests.get(url=_url,
                                headers={'Cookie': _mac_cookie,
                                         'Authorization': 'Bearer ' + token,
                                         'X-User-Agent': 'Model: MAG250; Link: WiFi', 'Referrer': _portal_url},
                                params=params,
                                timeout=30
                                )
        if response.content.decode('utf-8') != 'Authorization failed.' or retries == G.addon_config.max_retries:
            break
        _auth.clear_cache()
        retries += 1
    return response.json()


def get_categories():
    """Get video categories"""
    params = {'type': 'vod', 'action': 'get_categories'}
    return __call_stalker_portal(params)['js']


def get_tv_genres():
    """Get tv genres"""
    params = {'type': 'itv', 'action': 'get_genres'}
    return __call_stalker_portal(params)['js']


def remove_favorites(video_id):
    """Remove from favorites"""
    params = {'type': 'vod', 'action': 'del_fav', 'video_id': video_id}
    __call_stalker_portal(params)


def add_favorites(video_id):
    """Add to favorites"""
    params = {'type': 'vod', 'action': 'set_fav', 'video_id': video_id}
    __call_stalker_portal(params)


def get_vod_favorites(page):
    """Get favorites"""
    params = {'type': 'vod', 'action': 'get_ordered_list', 'fav': 'true', 'sortby': 'added'}
    return get_listing(params, page)


def get_tv_channels(category_id, page):
    """Get videos for a category"""
    params = {'type': 'itv', 'action': 'get_ordered_list', 'genre': category_id, 'sortby': 'number'}
    return get_listing(params, page)


def get_videos(category_id, page, search_term):
    """Get videos for a category"""
    params = {'type': 'vod', 'action': 'get_ordered_list', 'category': category_id, 'sortby': 'added'}
    if bool(search_term.strip()):
        params.update({'search': search_term})
    return get_listing(params, page)


def get_listing(params, page):
    """Generic method to get listing"""
    params.update({'p': str(page)})
    response = __call_stalker_portal(params)['js']
    videos = response['data']
    total_items = response['total_items']
    max_page_items = response['max_page_items']
    total_pages = int(math.ceil(float(total_items) / float(max_page_items)))
    for page_no in range(int(page) + 1, min(int(page) + G.addon_config.max_page_limit, total_pages + 1)):
        params.update({'p': str(page_no)})
        response = __call_stalker_portal(params)['js']
        videos += response['data']
    return {'max_page_items': max_page_items, 'total_items': total_items, 'data': videos}


def get_vod_stream_url(video_id, series):
    """Get VOD stream url"""
    stream_url = __call_stalker_portal(
        {'type': 'vod', 'action': 'create_link', 'cmd': '/media/' + video_id + '.mpg', 'series': str(series)}
    )['js']['cmd']
    __call_stalker_portal({'type': 'stb', 'action': 'log', 'real_action': 'play', 'param': stream_url,
                           'content_id': video_id})
    return stream_url


def get_tv_stream_url(cmd):
    """Get TV Channel stream url"""
    stream_url = __call_stalker_portal(
        {'type': 'itv', 'action': 'create_link', 'cmd': cmd}
    )['js']['cmd']
    return stream_url
