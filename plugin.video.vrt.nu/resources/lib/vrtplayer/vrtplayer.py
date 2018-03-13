import os
import requests
from urlparse import urljoin
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from resources.lib.helperobjects import helperobjects
from resources.lib.vrtplayer import metadatacollector
from resources.lib.vrtplayer import statichelper
from resources.lib.vrtplayer import actions
from resources.lib.vrtplayer import metadatacreator
from resources.lib.kodiwrappers import sortmethod


class VRTPlayer:

    #Url met de urls https://services.vrt.be/videoplayer/r/live.json
    _EEN_LIVESTREAM = "https://live-w.lwc.vrtcdn.be/groupc/live/d05012c2-6a5d-49ff-a711-79b32684615b/live.isml/.m3u8"
    _CANVAS_LIVESTREAM_ = "https://live-w.lwc.vrtcdn.be/groupc/live/905b0602-9719-4d14-ae2a-a9b459630653/live.isml/.m3u8"
    _KETNET_LIVESTREAM = "https://live-w.lwc.vrtcdn.be/groupc/live/8b898c7d-adf7-4d44-ab82-b5bb3a069989/live.isml/.m3u8"
    _SPORZA_LIVESTREAM = "https://live-w.lwc.vrtcdn.be/groupa/live/bf2f7c79-1d77-4cdc-80e8-47ae024f30ba/live.isml/.m3u8"

    _VRT_BASE = "https://www.vrt.be/"
    _VRTNU_BASE_URL = urljoin(_VRT_BASE, "/vrtnu/")
    _VRTNU_SEARCH_URL = "https://search.vrt.be/suggest?facets[categories]="

    def __init__(self, addon_path, kodi_wrapper, url_to_stream_service):
        self.metadata_collector = metadatacollector.MetadataCollector()
        self._addon_path = addon_path
        self._kodi_wrapper = kodi_wrapper
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
        joined_url = urljoin(self._VRTNU_BASE_URL, "./a-z/")
        menu_items = self.__get_menu_items(joined_url, {"class": "tile"}, actions.LISTING_VIDEOS,
                                     self.metadata_collector.get_az_metadata)
        self._kodi_wrapper.show_listing(menu_items, sortmethod.ALPHABET)

    def show_category_menu_items(self):
        joined_url = urljoin(self._VRTNU_BASE_URL, "./categorieen/")
        menu_items = self.__get_menu_items(joined_url, {"class": "tile tile--category"}, actions.LISTING_CATEGORY_VIDEOS)
        self._kodi_wrapper.show_listing(menu_items, sortmethod.ALPHABET)

    def show_video_category_episodes(self, path):
        category = path.split('/')[-2]
        joined_url = self._VRTNU_SEARCH_URL + category
        response = requests.get(joined_url)
        programs = response.json()
        menu_items = []
        for program in programs:
            title = program["title"]
            plot = BeautifulSoup(program["description"], "html.parser").text
            thumbnail = statichelper.replace_double_slashes_with_https(program["thumbnail"])

            metadata_creator = metadatacreator.MetadataCreator()
            metadata_creator.plot = plot
            video_dictionary = metadata_creator.get_video_dictionary()
            #cut vrtbase url off since it will be added again when searching for episodes (with a-z we dont have the
            #  full url)
            link_to_video = statichelper.replace_double_slashes_with_https(program["targetUrl"]).replace(self._VRT_BASE,
                                                                                                         "")
            item = helperobjects.TitleItem(title, {'action': actions.LISTING_VIDEOS, 'video': link_to_video},
                                           False, thumbnail, video_dictionary)
            menu_items.append(item)
        self._kodi_wrapper.show_listing(menu_items, sortmethod.ALPHABET)

    def play_vrtnu_video(self, url):
        stream = self._url_toStream_service.get_stream_from_url(url)
        self._kodi_wrapper.play_video(stream)

    def play_livestream(self, url):
        self._kodi_wrapper.play_livestream(url)

    def show_livestream_items(self):
        livestream_items = {helperobjects.TitleItem(self._kodi_wrapper.get_localized_string(32101),
                                        {'action': actions.PLAY_LIVE, 'video': self._EEN_LIVESTREAM},
                                        True, self.__get_media("een.png")),
                helperobjects.TitleItem(self._kodi_wrapper.get_localized_string(32102),
                                        {'action': actions.PLAY_LIVE, 'video': self._CANVAS_LIVESTREAM_},
                                        True, self.__get_media("canvas.png")),
                helperobjects.TitleItem(self._kodi_wrapper.get_localized_string(32103),
                                        {'action': actions.PLAY_LIVE, 'video': self._KETNET_LIVESTREAM},
                                        True, self.__get_media("ketnet.png")),
                helperobjects.TitleItem(self._kodi_wrapper.get_localized_string(32104),
                                        {'action': actions.PLAY_LIVE, 'video': self._SPORZA_LIVESTREAM},
                                        True, self.__get_media("sporza.png"))
                }
        self._kodi_wrapper.show_listing(livestream_items, sortmethod.ALPHABET)

    def show_videos(self, path):
        url = urljoin(self._VRT_BASE, path)
        #xbmc.log(url, xbmc.LOGWARNING)
        # go to url.relevant gets redirected and go on with this url
        relevant_path = requests.get(url)
        response = requests.get(relevant_path.url)
        soup = BeautifulSoup(response.content, "html.parser")
        title_items = []
        episodes_list = soup.find(class_="episodeslist")
        option_tags = []

        if episodes_list is not None:
            option_tags.extend(episodes_list.find_all("option"))

        if len(option_tags) != 0:
            title_items.extend(self.__get_episodes(option_tags))
        else:
            episodes_list_slider = soup.find(id="episodelist__slider")
            if episodes_list_slider is not None:
                title_items.extend(self.__get_multiple_videos(soup))
            else:
                title_items.extend(self.__get_single_video(relevant_path.url, soup))
        self._kodi_wrapper.show_listing(title_items)


    def __get_episodes(self, option_tags):
        """
        This method gets all the episodes = seasons from the dropdownmenus on the vrt.nu website
        :param option_tags:
        :return:
        """
        title_items = []
        for option_tag in option_tags:
            title = statichelper.replace_newlines_and_strip(option_tag.text)
            if option_tag.has_attr('data-href'):
                path = option_tag['data-href']
                title_items.append(helperobjects.TitleItem(title, {"action" : actions.LISTING_VIDEOS, 'video':path}, False))
        return title_items

    def __get_multiple_videos(self, tiles):
        title_items = []
        episode_list = tiles.find("div", {"id": "episodelist__slider"})

        for tile in episode_list.find_all(class_="tile"):
            thumbnail = VRTPlayer.__format_image_url(tile)
            found_element = tile.find(class_="tile__title")

            if found_element is not None:
                title = statichelper.replace_newlines_and_strip(found_element.contents[0])
                broadcast_date_tag = tile.find(class_="tile__broadcastdate--mobile")

                if broadcast_date_tag is not None:
                    title = broadcast_date_tag.text + " " + title

                path = tile["href"]
                video_dictionary = self.metadata_collector.get_multiple_layout_episode_metadata(tile)
                title_items.append(helperobjects.TitleItem(title, {"action": actions.PLAY, "video": path}, True, thumbnail, video_dictionary))
        return title_items

    def __get_single_video(self, path, soup):
        title_items = []
        video_dictionary = self.metadata_collector.get_single_layout_episode_metadata(soup)
        list_item_title = soup.find(class_="content__title").text

        if "shortdate" in video_dictionary:
            list_item_title = video_dictionary["shortdate"] + " " + list_item_title

        vrt_video = soup.find(class_="vrtvideo")
        thumbnail = VRTPlayer.__format_image_url(vrt_video)
        title_items.append(helperobjects.TitleItem(list_item_title, {"action": actions.PLAY, "video": path}, True, thumbnail, video_dictionary))
        return title_items

    def __get_media(self, file_name):
        return os.path.join(self._addon_path, 'resources', 'media', file_name)

    def __get_menu_items(self, url, soupstrainer_parser_selector, routing_action, video_dictionary_action=None):
        response = requests.get(url)
        tiles = SoupStrainer('a', soupstrainer_parser_selector)
        soup = BeautifulSoup(response.content, "html.parser", parse_only=tiles)
        listing = []
        for tile in soup.find_all(class_="tile"):
            link_to_video = tile["href"]
            thumbnail, title = self.__get_thumbnail_and_title(tile)
            video_dictionary = None
            if video_dictionary_action is not None:
                video_dictionary = video_dictionary_action(tile)

            item = helperobjects.TitleItem(title, {'action': routing_action, 'video': link_to_video},
                                           False, thumbnail, video_dictionary)
            listing.append(item)
        return listing

    @staticmethod
    def __format_image_url(element):
        raw_thumbnail = element.find("img")['srcset'].split('1x,')[0]
        return statichelper.replace_double_slashes_with_https(raw_thumbnail)

    @staticmethod
    def __get_thumbnail_and_title(element):
        thumbnail = VRTPlayer.__format_image_url(element)
        found_element = element.find(class_="tile__title")
        title = ""
        if found_element is not None:
            title = statichelper.replace_newlines_and_strip(found_element.contents[0])
        return thumbnail, title


