"""
Stalker API Calls
"""
from __future__ import absolute_import, division, unicode_literals

import json
import math
import requests
from .globals import G
from .auth import Auth
from .utils import Logger


class Api:
    """API calls"""

    @staticmethod
    def __call_stalker_portal(params):
        """Method to call portal"""
        retries = 0
        url = G.portal_config.portal_url
        mac_cookie = G.portal_config.mac_cookie
        referrer = G.portal_config.server_address
        auth = Auth()
        while True:
            token = auth.get_token(retries > 0)
            Logger.debug("Calling Stalker portal {} with params {}".format(url, json.dumps(params)))
            response = requests.get(url=url,
                                    headers={'Cookie': mac_cookie,
                                             'Authorization': 'Bearer ' + token,
                                             'X-User-Agent': 'Model: MAG250; Link: WiFi', 'Referrer': referrer},
                                    params=params,
                                    timeout=30
                                    )
            if response.text.find('Authorization failed') == -1 or retries == G.addon_config.max_retries:
                break
            if retries > 1:
                auth.clear_cache()
            retries += 1
        return response.json()

    @staticmethod
    def get_vod_categories():
        """Get video categories"""
        params = {'type': 'vod', 'action': 'get_categories'}
        return Api.__call_stalker_portal(params)['js']

    @staticmethod
    def get_tv_genres():
        """Get tv genres"""
        params = {'type': 'itv', 'action': 'get_genres'}
        return Api.__call_stalker_portal(params)['js']

    @staticmethod
    def remove_favorites(video_id):
        """Remove from favorites"""
        params = {'type': 'vod', 'action': 'del_fav', 'video_id': video_id}
        Api.__call_stalker_portal(params)

    @staticmethod
    def add_favorites(video_id):
        """Add to favorites"""
        params = {'type': 'vod', 'action': 'set_fav', 'video_id': video_id}
        Api.__call_stalker_portal(params)

    @staticmethod
    def get_vod_favorites(page):
        """Get favorites"""
        params = {'type': 'vod', 'action': 'get_ordered_list', 'fav': 'true', 'sortby': 'added'}
        return Api.get_listing(params, page)

    @staticmethod
    def get_tv_channels(category_id, page):
        """Get videos for a category"""
        params = {'type': 'itv', 'action': 'get_ordered_list', 'genre': category_id, 'sortby': 'number'}
        return Api.get_listing(params, page)

    @staticmethod
    def get_videos(category_id, page, search_term, fav):
        """Get videos for a category"""
        params = {'type': 'vod', 'action': 'get_ordered_list', 'category': category_id, 'sortby': 'added', 'fav': fav}
        if bool(search_term.strip()):
            params.update({'search': search_term})
        return Api.get_listing(params, page)

    @staticmethod
    def get_listing(params, page):
        """Generic method to get listing"""
        params.update({'p': str(page)})
        response = Api.__call_stalker_portal(params)['js']
        videos = response['data']
        total_items = response['total_items']
        max_page_items = response['max_page_items']
        total_pages = int(math.ceil(float(total_items) / float(max_page_items)))
        for page_no in range(int(page) + 1, min(int(page) + G.addon_config.max_page_limit, total_pages + 1)):
            params.update({'p': str(page_no)})
            response = Api.__call_stalker_portal(params)['js']
            videos += response['data']
        return {'max_page_items': max_page_items, 'total_items': total_items, 'data': videos}

    @staticmethod
    def get_vod_stream_url(video_id, series):
        """Get VOD stream url"""
        stream_url = Api.__call_stalker_portal(
            {'type': 'vod', 'action': 'create_link', 'cmd': '/media/' + video_id + '.mpg', 'series': str(series)}
        )['js']['cmd']
        Api.__call_stalker_portal({'type': 'stb', 'action': 'log', 'real_action': 'play', 'param': stream_url,
                                   'content_id': video_id})
        return stream_url

    @staticmethod
    def get_tv_stream_url(cmd):
        """Get TV Channel stream url"""
        stream_url = Api.__call_stalker_portal(
            {'type': 'itv', 'action': 'create_link', 'cmd': cmd}
        )['js']['cmd']
        return stream_url
