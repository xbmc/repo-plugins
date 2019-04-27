# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from bs4 import BeautifulSoup, SoupStrainer
import os
import requests

from resources.lib.helperobjects import helperobjects
from resources.lib.vrtplayer import actions, statichelper


class VRTPlayer:

    # URLs van https://services.vrt.be/videoplayer/r/live.json
    _EEN_LIVESTREAM = 'https://www.vrt.be/vrtnu/kanalen/een/'
    _CANVAS_LIVESTREAM = 'https://www.vrt.be/vrtnu/kanalen/canvas/'
    _KETNET_LIVESTREAM = 'https://www.vrt.be/vrtnu/kanalen/ketnet/'

    VRT_BASE = 'https://www.vrt.be/'
    VRTNU_BASE_URL = VRT_BASE + '/vrtnu'

    def __init__(self, addon_path, kodi_wrapper, stream_service, api_helper):
        self._addon_path = addon_path
        self._kodi_wrapper = kodi_wrapper
        self._proxies = self._kodi_wrapper.get_proxies()
        self._api_helper = api_helper
        self._stream_service = stream_service

    def show_main_menu_items(self):
        main_items = [
            helperobjects.TitleItem(title=self._kodi_wrapper.get_localized_string(32080),
                                    url_dict=dict(action=actions.LISTING_AZ_TVSHOWS),
                                    is_playable=False,
                                    art_dict=dict(thumb='DefaultMovieTitle.png', icon='DefaultMovieTitle.png', fanart='DefaultMovieTitle.png'),
                                    video_dict=dict(plot=self._kodi_wrapper.get_localized_string(32081))),
            helperobjects.TitleItem(title=self._kodi_wrapper.get_localized_string(32082),
                                    url_dict=dict(action=actions.LISTING_CATEGORIES),
                                    is_playable=False,
                                    art_dict=dict(thumb='DefaultGenre.png', icon='DefaultGenre.png', fanart='DefaultGenre.png'),
                                    video_dict=dict(plot=self._kodi_wrapper.get_localized_string(32083))),
            helperobjects.TitleItem(title=self._kodi_wrapper.get_localized_string(32084),
                                    url_dict=dict(action=actions.LISTING_LIVE),
                                    is_playable=False,
                                    art_dict=dict(thumb='DefaultAddonPVRClient.png', icon='DefaultAddonPVRClient.png', fanart='DefaultAddonPVRClient.png'),
                                    video_dict=dict(plot=self._kodi_wrapper.get_localized_string(32085))),
            helperobjects.TitleItem(title=self._kodi_wrapper.get_localized_string(32086),
                                    url_dict=dict(action=actions.LISTING_EPISODES, video_url='recent'),
                                    is_playable=False,
                                    art_dict=dict(thumb='DefaultYear.png', icon='DefaultYear.png', fanart='DefaultYear.png'),
                                    video_dict=dict(plot=self._kodi_wrapper.get_localized_string(32087))),
            helperobjects.TitleItem(title=self._kodi_wrapper.get_localized_string(32088),
                                    url_dict=dict(action=actions.LISTING_TVGUIDE),
                                    is_playable=False,
                                    art_dict=dict(thumb='DefaultAddonTvInfo.png', icon='DefaultAddonTvInfo.png', fanart='DefaultAddonTvInfo.png'),
                                    video_dict=dict(plot=self._kodi_wrapper.get_localized_string(32089))),
        ]
        self._kodi_wrapper.show_listing(main_items, sort='unsorted', content_type='files')

    def show_tvshow_menu_items(self, path):
        tvshow_items = self._api_helper.get_tvshow_items(path)
        self._kodi_wrapper.show_listing(tvshow_items, sort='label', content_type='tvshows')

    def show_category_menu_items(self):
        joined_url = self.VRTNU_BASE_URL + '/categorieen/'
        category_items = self.__get_category_menu_items(joined_url, {'class': 'nui-tile'}, actions.LISTING_CATEGORY_TVSHOWS)
        self._kodi_wrapper.show_listing(category_items, sort='label', content_type='files')

    def play(self, video):
        stream = self._stream_service.get_stream(video)
        if stream is not None:
            self._kodi_wrapper.play(stream)

    def show_livestream_items(self):
        livestream_items = [
            helperobjects.TitleItem(
                title=self._kodi_wrapper.get_localized_string(32101),
                url_dict=dict(action=actions.PLAY, video_url=self._EEN_LIVESTREAM),
                is_playable=True,
                art_dict=dict(thumb=self.__get_media('een.png'), icon='DefaultAddonPVRClient.png', fanart=self._api_helper.get_live_screenshot('een')),
                video_dict=dict(plot=self._kodi_wrapper.get_localized_string(32201) + '\n' + self._kodi_wrapper.get_localized_string(32102)),
            ),
            helperobjects.TitleItem(
                title=self._kodi_wrapper.get_localized_string(32111),
                url_dict=dict(action=actions.PLAY, video_url=self._CANVAS_LIVESTREAM),
                is_playable=True,
                art_dict=dict(thumb=self.__get_media('canvas.png'), icon='DefaultAddonPVRClient.png', fanart=self._api_helper.get_live_screenshot('canvas')),
                video_dict=dict(plot=self._kodi_wrapper.get_localized_string(32201) + '\n' + self._kodi_wrapper.get_localized_string(32112)),
            ),
            helperobjects.TitleItem(
                title=self._kodi_wrapper.get_localized_string(32121),
                url_dict=dict(action=actions.PLAY, video_url=self._KETNET_LIVESTREAM),
                is_playable=True,
                art_dict=dict(thumb=self.__get_media('ketnet.png'), icon='DefaultAddonPVRClient.png', fanart=self._api_helper.get_live_screenshot('ketnet')),
                video_dict=dict(plot=self._kodi_wrapper.get_localized_string(32201) + '\n' + self._kodi_wrapper.get_localized_string(32122)),
            ),
        ]
        self._kodi_wrapper.show_listing(livestream_items, content_type='videos')

    def show_episodes(self, path):
        episode_items, sort, ascending = self._api_helper.get_episode_items(path)
        self._kodi_wrapper.show_listing(episode_items, sort=sort, ascending=ascending, content_type='episodes')

    def __get_media(self, file_name):
        return os.path.join(self._addon_path, 'resources', 'media', file_name)

    def __get_category_menu_items(self, url, soupstrainer_parser_selector, routing_action, video_dict_action=None):
        response = requests.get(url, proxies=self._proxies)
        tiles = SoupStrainer('a', soupstrainer_parser_selector)
        soup = BeautifulSoup(response.content, 'html.parser', parse_only=tiles)
        listing = []
        for tile in soup.find_all(class_='nui-tile'):
            category = tile.get('href').split('/')[-2]
            thumbnail, title = self.__get_category_thumbnail_and_title(tile)
            video_dict = None
            if video_dict_action is not None:
                video_dict = video_dict_action(tile)

            listing.append(helperobjects.TitleItem(title=title,
                                                   url_dict=dict(action=routing_action, video_url=category),
                                                   is_playable=False,
                                                   art_dict=dict(thumb=thumbnail, icon='DefaultGenre.png', fanart=thumbnail),
                                                   video_dict=video_dict))
        return listing

    @staticmethod
    def __format_category_image_url(element):
        raw_thumbnail = element.find(class_='media').get('data-responsive-image', 'DefaultGenre.png')
        return statichelper.add_https_method(raw_thumbnail)

    @staticmethod
    def __get_category_thumbnail_and_title(element):
        thumbnail = VRTPlayer.__format_category_image_url(element)
        found_element = element.find('h3')
        title = ''
        if found_element is not None:
            title = statichelper.strip_newlines(found_element.contents[0])
        return thumbnail, title
