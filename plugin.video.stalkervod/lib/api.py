"""
Stalker API Calls
"""
from __future__ import absolute_import, division, unicode_literals

import json
import math
import requests
from .globals import G
from .auth import Auth
from .loggers import Logger


class Api:
    """API calls"""

    @staticmethod
    def __call_stalker_portal(params, return_response_body=True):
        """Method to call portal"""
        response = Api.__call_stalker_portal_return_response(params)
        if return_response_body:
            return response.json()
        return None

    @staticmethod
    def __call_stalker_portal_return_response(params):
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
                                             'SN': G.portal_config.serial_number,
                                             'Authorization': 'Bearer ' + token,
                                             'X-User-Agent': 'Model: MAG250; Link: WiFi', 'Referrer': referrer,
                                             'User-Agent': 'Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3'},
                                    params=params,
                                    timeout=30
                                    )
            if response.text.find('Authorization failed') == -1 or retries == G.addon_config.max_retries:
                break
            if retries > 1:
                auth.clear_cache()
            retries += 1
        return response

    @staticmethod
    def get_vod_categories():
        """Get video categories"""
        params = {'type': 'vod', 'action': 'get_categories'}
        return Api.__call_stalker_portal(params)['js']

    @staticmethod
    def get_series_categories():
        """Get video categories"""
        params = {'type': 'series', 'action': 'get_categories'}
        return Api.__call_stalker_portal(params).get('js', False)

    @staticmethod
    def get_tv_genres():
        """Get tv genres"""
        params = {'type': 'itv', 'action': 'get_genres'}
        return Api.__call_stalker_portal(params)['js']

    @staticmethod
    def remove_favorites(video_id, _type):
        """Remove from favorites"""
        if _type == 'itv':
            Api.__remove_tv_favorites(video_id)
        else:
            params = {'type': _type, 'action': 'del_fav', 'video_id': video_id}
            Api.__call_stalker_portal(params, False)

    @staticmethod
    def add_favorites(video_id, _type):
        """Add to favorites"""
        if _type == 'itv':
            Api.__add_tv_favorites(video_id)
        else:
            params = {'type': _type, 'action': 'set_fav', 'video_id': video_id}
            Api.__call_stalker_portal(params, False)

    @staticmethod
    def __add_tv_favorites(video_id):
        """Add to tv favorites"""
        params = {'type': 'itv', 'action': 'get_all_fav_channels'}
        fav_channels = Api.__call_stalker_portal(params)['js']['data']
        fav_ch = [video_id]
        for fav_channel in fav_channels:
            fav_ch.append(fav_channel['id'])
        params = {'type': 'itv', 'action': 'set_fav', 'fav_ch': ','.join(fav_ch)}
        Api.__call_stalker_portal(params, False)

    @staticmethod
    def __remove_tv_favorites(video_id):
        """Add to tv favorites"""
        params = {'type': 'itv', 'action': 'get_all_fav_channels'}
        fav_channels = Api.__call_stalker_portal(params)['js']['data']
        fav_ch = []
        for fav_channel in fav_channels:
            if video_id != fav_channel['id']:
                fav_ch.append(fav_channel['id'])
        params = {'type': 'itv', 'action': 'set_fav', 'fav_ch': ','.join(fav_ch)}
        Api.__call_stalker_portal(params, False)

    @staticmethod
    def get_vod_favorites(page):
        """Get favorites"""
        params = {'type': 'vod', 'action': 'get_ordered_list', 'fav': '1', 'sortby': 'added'}
        return Api.get_listing(params, page)

    @staticmethod
    def get_series_favorites(page):
        """Get favorites"""
        params = {'type': 'series', 'action': 'get_ordered_list', 'fav': '1', 'sortby': 'added'}
        return Api.get_listing(params, page)

    @staticmethod
    def get_tv_favorites(page):
        """Get favorites"""
        params = {'type': 'itv', 'action': 'get_ordered_list', 'fav': '1', 'sortby': 'number'}
        return Api.get_listing(params, page)

    @staticmethod
    def get_seasons(video_id):
        """Get favorites"""
        params = {'type': 'series', 'action': 'get_ordered_list', 'movie_id': video_id, 'sortby': 'added'}
        return Api.__call_stalker_portal(params)['js']

    @staticmethod
    def get_tv_channels(category_id, page, search_term, fav):
        """Get videos for a category"""
        params = {'type': 'itv', 'action': 'get_ordered_list', 'genre': category_id, 'sortby': 'number', 'fav': fav}
        if bool(search_term.strip()):
            params.update({'search': search_term})
        return Api.get_listing(params, page)

    @staticmethod
    def get_videos(category_id, page, search_term, fav):
        """Get videos for a category"""
        params = {'type': 'vod', 'action': 'get_ordered_list', 'category': category_id, 'sortby': 'added', 'fav': fav}
        if bool(search_term.strip()):
            params.update({'search': search_term})
        return Api.get_listing(params, page)

    @staticmethod
    def get_series(category_id, page, search_term, fav):
        """Get videos for a category"""
        params = {'type': 'series', 'action': 'get_ordered_list', 'category': category_id, 'sortby': 'added', 'fav': fav}
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
    def get_vod_stream_url(video_id, series, cmd, use_cmd):
        """Get VOD stream url"""
        if use_cmd == '0':
            response = Api.__get_vod_stream_url_video_id(video_id, series)
            if response.status_code != 200:
                stream_url = Api.__get_vod_stream_url_cmd(cmd, series)
            else:
                stream_url = response.json()['js']['cmd']
        else:
            stream_url = Api.__get_vod_stream_url_cmd(cmd, series)
        if stream_url.find(' ') != -1:
            stream_url = stream_url[(stream_url.find(' ') + 1):]
        # Api.__call_stalker_portal({'type': 'stb', 'action': 'log', 'real_action': 'play', 'param': stream_url, 'content_id': video_id})
        return stream_url

    @staticmethod
    def __get_vod_stream_url_cmd(cmd, series):
        """Get VOD stream url"""
        return Api.__call_stalker_portal({'type': 'vod', 'action': 'create_link', 'cmd': cmd, 'series': str(series)})['js']['cmd']

    @staticmethod
    def __get_vod_stream_url_video_id(video_id, series):
        """Get VOD stream url"""
        return Api.__call_stalker_portal_return_response({'type': 'vod', 'action': 'create_link', 'cmd': '/media/' + video_id + '.mpg', 'series': str(series)}
                                                         )

    @staticmethod
    def get_tv_stream_url(cmd):
        """Get TV Channel stream url"""
        cmd = Api.__call_stalker_portal(
            {'type': 'itv', 'action': 'create_link', 'cmd': cmd}
        )['js']['cmd']
        if cmd.find(' ') != -1:
            cmd = cmd[(cmd.find(' ') + 1):]
        return cmd
