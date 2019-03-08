import os
import re
import requests
from urlparse import urljoin
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from resources.lib.helperobjects import helperobjects
from resources.lib.vrtplayer import metadatacollector, statichelper, actions, metadatacreator
from resources.lib.kodiwrappers import sortmethod


class VRTPlayer:

    #Url met de urls https://services.vrt.be/videoplayer/r/live.json
    _EEN_LIVESTREAM = 'https://www.vrt.be/vrtnu/kanalen/een/'
    _CANVAS_LIVESTREAM_ = 'https://www.vrt.be/vrtnu/kanalen/canvas/'
    _KETNET_LIVESTREAM = 'https://www.vrt.be/vrtnu/kanalen/ketnet/'

    _VRT_BASE = 'https://www.vrt.be/'
    _VRTNU_BASE_URL = urljoin(_VRT_BASE, '/vrtnu/')
    _VRTNU_SEARCH_URL = 'https://search.vrt.be/suggest?facets[categories]='

    def __init__(self, addon_path, kodi_wrapper, url_to_stream_service, api_helper):
        self.metadata_collector = metadatacollector.MetadataCollector()
        self._addon_path = addon_path
        self._kodi_wrapper = kodi_wrapper
        self._api_helper = api_helper
        self._url_toStream_service = url_to_stream_service


    def show_main_menu_items(self):
        menu_items = {helperobjects.TitleItem(self._kodi_wrapper.get_localized_string(32091), {'action': actions.LISTING_AZ}, False,
                                        None),
                helperobjects.TitleItem(self._kodi_wrapper.get_localized_string(32092), {'action': actions.LISTING_CATEGORIES},
                                        False, None),
                helperobjects.TitleItem(self._kodi_wrapper.get_localized_string(32100), {'action': actions.LISTING_LIVE}, False,
                                        None)}
        self._kodi_wrapper.show_listing(menu_items, sortmethod.ALPHABET)

    def show_az_menu_items(self):
        joined_url = urljoin(self._VRTNU_BASE_URL, './a-z/')
        menu_items = self.__get_az_menu_items(joined_url, {'class': 'nui-tile'}, actions.LISTING_VIDEOS,
                                     self.metadata_collector.get_az_metadata)
        self._kodi_wrapper.show_listing(menu_items, sortmethod.ALPHABET)

    def show_category_menu_items(self):
        joined_url = urljoin(self._VRTNU_BASE_URL, './categorieen/')
        menu_items = self.__get_category_menu_items(joined_url, {'class': 'nui-tile title'}, actions.LISTING_CATEGORY_VIDEOS)
        self._kodi_wrapper.show_listing(menu_items, sortmethod.ALPHABET)

    def show_video_category_episodes(self, path):
        category = path.split('/')[-2]
        joined_url = self._VRTNU_SEARCH_URL + category
        response = requests.get(joined_url)
        programs = response.json()
        menu_items = []
        for program in programs:
            title = program['title']
            plot = BeautifulSoup(program['description'], 'html.parser').text
            thumbnail = statichelper.replace_double_slashes_with_https(program['thumbnail'])

            metadata_creator = metadatacreator.MetadataCreator()
            metadata_creator.plot = plot
            video_dictionary = metadata_creator.get_video_dictionary()
            #cut vrtbase url off since it will be added again when searching for episodes (with a-z we dont have the
            #  full url)
            link_to_video = program['targetUrl'].replace('//www.vrt.be','')
            item = helperobjects.TitleItem(title, {'action': actions.LISTING_VIDEOS, 'video': link_to_video},
                                           False, thumbnail, video_dictionary)
            menu_items.append(item)
        self._kodi_wrapper.show_listing(menu_items, sortmethod.ALPHABET)

    def play(self, url):
        video = self._url_toStream_service.get_stream_from_url(url)
        if video is not None:
            self._kodi_wrapper.play(video)

    def show_livestream_items(self):
        livestream_items = {helperobjects.TitleItem(self._kodi_wrapper.get_localized_string(32101),
                                        {'action': actions.PLAY, 'video': self._EEN_LIVESTREAM},
                                        True, self.__get_media('een.png')),
                helperobjects.TitleItem(self._kodi_wrapper.get_localized_string(32102),
                                        {'action': actions.PLAY, 'video': self._CANVAS_LIVESTREAM_},
                                        True, self.__get_media('canvas.png')),
                helperobjects.TitleItem(self._kodi_wrapper.get_localized_string(32103),
                                        {'action': actions.PLAY, 'video': self._KETNET_LIVESTREAM},
                                        True, self.__get_media('ketnet.png'))
                }
        self._kodi_wrapper.show_listing(livestream_items, sortmethod.ALPHABET)

    def show_videos(self, path, season):
        title_items = self._api_helper.get_video_items(path, season)
        self._kodi_wrapper.show_listing(title_items)

    def __get_media(self, file_name):
        return os.path.join(self._addon_path, 'resources', 'media', file_name)

    def __get_category_menu_items(self, url, soupstrainer_parser_selector, routing_action, video_dictionary_action=None):
        response = requests.get(url)
        tiles = SoupStrainer('a', soupstrainer_parser_selector)
        soup = BeautifulSoup(response.content, 'html.parser', parse_only=tiles)
        listing = []
        for tile in soup.find_all(class_='nui-tile title'):
            link_to_video = tile['href']
            thumbnail, title = self.__get_category_thumbnail_and_title(tile)
            video_dictionary = None
            if video_dictionary_action is not None:
                video_dictionary = video_dictionary_action(tile)

            item = helperobjects.TitleItem(title, {'action': routing_action, 'video': link_to_video},
                                           False, thumbnail, video_dictionary)
            listing.append(item)
        return listing

    def __get_az_menu_items(self, url, soupstrainer_parser_selector, routing_action, video_dictionary_action=None):
        response = requests.get(url)
        tiles = SoupStrainer('a', soupstrainer_parser_selector)
        soup = BeautifulSoup(response.content, 'html.parser', parse_only=tiles)
        listing = []
        for tile in soup.find_all(class_= 'nui-tile'):
            link_to_video = tile['href']
            thumbnail, title = self.__get_az_thumbnail_and_title(tile)
            video_dictionary = None
            if video_dictionary_action is not None:
                video_dictionary = video_dictionary_action(tile)

            item = helperobjects.TitleItem(title, {'action': routing_action, 'video': link_to_video},
                                           False, thumbnail, video_dictionary)
            listing.append(item)
        return listing

    @staticmethod
    def __format_image_url(element):
        raw_thumbnail = element.find('img')['srcset'].split('1x,')[0]
        return statichelper.replace_double_slashes_with_https(raw_thumbnail)

    @staticmethod
    def __format_category_image_url(element):
        raw_thumbnail = element.find(class_='nui-tile--image')['data-responsive-image']
        return statichelper.replace_double_slashes_with_https(raw_thumbnail)

    @staticmethod
    def __get_az_thumbnail_and_title(element):
        thumbnail = VRTPlayer.__format_image_url(element)
        found_element = element.find(class_='nui-tile--content')
        title = ''
        if found_element is not None:
            title_element = found_element.find('h3')
            title = statichelper.replace_newlines_and_strip(title_element.text)
        return thumbnail, title

    @staticmethod
    def __get_category_thumbnail_and_title(element):
        thumbnail = VRTPlayer.__format_category_image_url(element)
        found_element = element.find('h2')
        title = ''
        if found_element is not None:
            title = statichelper.replace_newlines_and_strip(found_element.contents[0])
        return thumbnail, title
