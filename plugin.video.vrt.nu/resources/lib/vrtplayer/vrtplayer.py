import os
import re
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
    _EEN_LIVESTREAM = "https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/videos/vualto_een_geo"
    _CANVAS_LIVESTREAM_ = "https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/videos/vualto_canvas_geo"
    _KETNET_LIVESTREAM = "https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/videos/vualto_ketnet_geo"
    _SPORZA_LIVESTREAM = "https://media-services-public.vrt.be/vualto-video-aggregator-web/rest/external/v1/videos/vualto_sporza_geo"

    _VRT_BASE = "https://www.vrt.be/"
    _VRTNU_BASE_URL = urljoin(_VRT_BASE, "/vrtnu/")
    _VRTNU_SEARCH_URL = "https://search.vrt.be/suggest?facets[categories]="

    def __init__(self, addon_path, kodi_wrapper, url_to_stream_service, url_to_livestream_service):
        self.metadata_collector = metadatacollector.MetadataCollector()
        self._addon_path = addon_path
        self._kodi_wrapper = kodi_wrapper
        self._url_toStream_service = url_to_stream_service
        self.url_to_livestream_service = url_to_livestream_service


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
        menu_items = self.__get_az_menu_items(joined_url, {"class": "nui-tile"}, actions.LISTING_VIDEOS,
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
        stream = self.url_to_livestream_service.get_stream_from_url(url)
        self._kodi_wrapper.play_livestream(stream)

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
        li_tags = []

        if episodes_list is not None :
            li_tags.extend(episodes_list.find_all(class_="vrt-labelnav--item"))

        episode_items = self.__get_episodes(li_tags)
        if len(li_tags) != 0 and episode_items:
            title_items.extend(episode_items)
        else:
             
            if soup.find("div", {"id": "episodes-list"}) is not None or soup.find("div", {"id": "episodes-list-wrapper"}) is not None:
                title_items.extend(self.__get_multiple_videos_episodes_list_id(soup))
            else:
                title_items.extend(self.__get_single_video(relevant_path.url, soup))
        self._kodi_wrapper.show_listing(title_items)


    def __get_episodes(self, li_tags):
        """
        This method gets all the episodes = seasons from the tabmenus on the vrt.nu website
        :param option_tags:
        :return:
        """
        title_items = []
        for li_tag in li_tags:
            a_tag = li_tag.find("a");
            title = statichelper.replace_newlines_and_strip(a_tag.text)
            if a_tag.has_attr('href'):
                path = a_tag['href']
                title_items.append(helperobjects.TitleItem(title, {"action" : actions.LISTING_VIDEOS, 'video':path}, False))
        return title_items


    #def __get_multiple_videos_episodeslist_class(self, soup):

    def __get_multiple_videos_episodes_list_id(self, soup):
        title_items = []
        #some episodes have a different episodelist using class episodelist instead of id episode-list :/
        episode_list_css = soup.find("div", {"class": "episodeslist"})
        episode_list = soup.find("div", {"id" : "episodes-list"})

        if episode_list_css is not None:
            episode_list = episode_list_css.find("div", {"id": "episodes-list-wrapper"})
        
        for tile in episode_list.find_all("li"):
            thumbnail = VRTPlayer.__format_image_url(tile)
            found_element = tile.find(class_="vrtnu-list--item-meta")

            if found_element is not None:
                h_tag = found_element.find("h2")
                title = statichelper.replace_newlines_and_strip(h_tag.text)
                broadcast_date_tag = found_element.find(class_="vrtnu-list--item-meta__mobile")

                if broadcast_date_tag is not None:
                    clean_date = VRTPlayer.__strip_date_from_unessecary_caracters(broadcast_date_tag.text)
                    title = clean_date + " " + title

                path = tile.find("a")["href"]
                video_dictionary = self.metadata_collector.get_multiple_layout_episode_metadata(tile)
                title_items.append(helperobjects.TitleItem(title, {"action": actions.PLAY, "video": path}, True, thumbnail, video_dictionary))
        return title_items

    def __get_single_video(self, path, soup):
        title_items = []
        video_dictionary = self.metadata_collector.get_single_layout_episode_metadata(soup)
        content = soup.find(class_="content2");
        list_item_title = content.find("h1").text

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

    def __get_az_menu_items(self, url, soupstrainer_parser_selector, routing_action, video_dictionary_action=None):
        response = requests.get(url)
        tiles = SoupStrainer('a', soupstrainer_parser_selector)
        soup = BeautifulSoup(response.content, "html.parser", parse_only=tiles)
        listing = []
        for tile in soup.find_all(class_= 'nui-tile'):
            link_to_video = tile["href"]
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
        raw_thumbnail = element.find("img")['srcset'].split('1x,')[0]
        return statichelper.replace_double_slashes_with_https(raw_thumbnail)

    @staticmethod
    def __get_az_thumbnail_and_title(element):
        thumbnail = VRTPlayer.__format_image_url(element)
        found_element = element.find(class_="nui-tile--content")
        title = ""
        if found_element is not None:
            title_element = found_element.find('h3')
            title = statichelper.replace_newlines_and_strip(title_element.text)
        return thumbnail, title
    
    @staticmethod
    def __get_thumbnail_and_title(element):
        thumbnail = VRTPlayer.__format_image_url(element)
        found_element = element.find(class_="tile__title")
        title = ""
        if found_element is not None:
            title = statichelper.replace_newlines_and_strip(found_element.contents[0])
        return thumbnail, title

    @staticmethod
    def __strip_date_from_unessecary_caracters(dirtyDate): 
        date = re.findall("\d+/\d+", dirtyDate)[0]  
        return date
