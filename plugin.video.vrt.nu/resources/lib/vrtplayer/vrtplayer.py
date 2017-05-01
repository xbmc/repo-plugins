import sys
import xbmc
import os
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import re
import  time
from urlparse import parse_qsl
from urlparse import urljoin
from urllib import urlencode
from bs4 import BeautifulSoup
from bs4 import SoupStrainer
from resources.lib.vrtplayer import urltostreamservice
from resources.lib.helperobjects import helperobjects
from resources.lib.vrtplayer import metadatacollector
from resources.lib.vrtplayer import statichelper
from resources.lib.vrtplayer import actions
from resources.lib.vrtplayer import metadatacreator


class VRTPlayer:

    _VRT_LIVESTREAM_URL = "http://live.stream.vrt.be/vrt_video1_live/smil:vrt_video1_live.smil/playlist.m3u8"
    _CANVAS_LIVESTREAM_ = "http://live.stream.vrt.be/vrt_video2_live/smil:vrt_video2_live.smil/playlist.m3u8"
    _KETNET_VRT = "http://live.stream.vrt.be/vrt_events3_live/smil:vrt_events3_live.smil/playlist.m3u8"

    _VRT_BASE = "https://www.vrt.be/"
    _VRTNU_BASE_URL = urljoin(_VRT_BASE, "/vrtnu/")
    _VRTNU_SEARCH_URL = "https://search.vrt.be/suggest?facets[categories]="

    def __init__(self, handle, url):
        self._handle = handle
        self._url = url
        self.metadata_collector = metadatacollector.MetadataCollector()
        self._addon = xbmcaddon.Addon()
        self._addon_path = self._addon.getAddonInfo("path")

    def show_listing(self, list_items):
        listing = []
        for title_item in list_items:
            list_item = xbmcgui.ListItem(label=title_item.title)
            url = self._url + '?' + urlencode(title_item.url_dictionary)
            list_item.setProperty('IsPlayable', str(title_item.is_playable))
            list_item.setArt({'thumb': title_item.logo})
            list_item.setInfo('video', title_item.video_dictionary)
            listing.append((url, list_item, not title_item.is_playable))
        xbmcplugin.addDirectoryItems(self._handle, listing, len(listing))
        xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.endOfDirectory(self._handle)

    def get_az_menu_items(self):
        url = urljoin(self._VRTNU_BASE_URL, "./a-z/")
        response = requests.get(url)
        tiles = SoupStrainer('a', {"class": "tile"})
        soup = BeautifulSoup(response.content, "html.parser", parse_only=tiles)
        listing = []
        for tile in soup.find_all(class_="tile"):
            link_to_video = tile["href"]
            video_dictionary = self.metadata_collector.get_az_metadata(tile)
            thumbnail, title = self.__get_thumbnail_and_title(tile)
            item = helperobjects.TitleItem(title, {'action': actions.GET_EPISODES, 'video': link_to_video}, False
                                           , thumbnail,
                                           video_dictionary)
            listing.append(item)
        return listing

    def get_category_menu_items(self):
        joined_url = urljoin(self._VRTNU_BASE_URL, "./categorieen/")
        response = requests.get(joined_url)
        tiles = SoupStrainer('a', {"class": "tile tile--category"})
        soup = BeautifulSoup(response.content, "html.parser", parse_only=tiles)
        listing = []
        for tile in soup.find_all(class_="tile"):
            link_to_video = tile["href"]
            thumbnail, title = self.__get_thumbnail_and_title(tile)
            item = helperobjects.TitleItem(title, {'action': actions.GET_CATEGORY_EPISODES, 'video': link_to_video},
            False, thumbnail)
            listing.append(item)
        return listing

    def get_video_category_episodes(self, path):
        category = path.split('/')[-2]
        joined_url = self._VRTNU_SEARCH_URL + category
        response = requests.get(joined_url)
        programs = response.json()
        listing = []
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
            item = helperobjects.TitleItem(title, {'action': actions.GET_EPISODES, 'video': link_to_video},
            False, thumbnail, video_dictionary)
            listing.append(item)
        return listing
    

    def get_main_menu_items(self):
        return {helperobjects.TitleItem(self._addon.getLocalizedString(32091), {'action': actions.LISTING_AZ}, False,
                                        None),
                helperobjects.TitleItem(self._addon.getLocalizedString(32092), {'action': actions.LISTING_CATEGORIES},
                                        False, None),
                helperobjects.TitleItem(self._addon.getLocalizedString(32100), {'action': actions.LISTING_LIVE}, False,
                                        None)}

    def get_livestream_items(self):
        return {helperobjects.TitleItem(self._addon.getLocalizedString(32101),
                                        {'action': actions.PLAY_LIVE, 'video': self._VRT_LIVESTREAM_URL},
                                        True, self.__get_media("een.png")),
                helperobjects.TitleItem(self._addon.getLocalizedString(32102),
                                        {'action': actions.PLAY_LIVE, 'video': self._CANVAS_LIVESTREAM_},
                                        True, self.__get_media("canvas.png")),
                helperobjects.TitleItem(self._addon.getLocalizedString(32103),
                                        {'action': actions.PLAY_LIVE, 'video': self._KETNET_VRT},
                                        True, self.__get_media("ketnet.png"))}

    def get_video_episodes(self, path):
        url = urljoin(self._VRT_BASE, path)
        #xbmc.log(url, xbmc.LOGWARNING)
        # go to url.relevant gets redirected and go on with this url
        relevant_path = requests.get(url)
        response = requests.get(relevant_path.url)
        soup = BeautifulSoup(response.content, "html.parser")
        listing = []
        episodes = soup.find_all(class_="tile")
        if len(episodes) != 0:
            listing.extend(self.get_multiple_videos(soup))
        else:
            li, url = self.get_single_video(relevant_path.url, soup)
            listing.append((url, li, False))

        xbmcplugin.addDirectoryItems(self._handle, listing, len(listing))
        xbmcplugin.endOfDirectory(self._handle)

    def get_multiple_videos(self, soup):
        items = []
        episode_list = soup.find("div", {"id": "episodelist__slider"})

        for tile in episode_list.find_all(class_="tile"):
            li = self.__get_item(tile, "true")
            if li is not None:
                link_to_video = tile["href"]
                video_dictionary = self.metadata_collector.get_multiple_layout_episode_metadata(tile)
                li.setInfo('video', video_dictionary)
                url = '{0}?action=play&video={1}'.format(self._url, link_to_video)
                items.append((url, li, False))
        return items

    def get_single_video(self, path, soup):
        vrt_video = soup.find(class_="vrtvideo")
        thumbnail = VRTPlayer.format_image_url(vrt_video)
        li = xbmcgui.ListItem(soup.find(class_="content__title").text)
        li.setProperty('IsPlayable', 'true')

        video_dictionary = self.metadata_collector.get_single_layout_episode_metadata(soup)

        li.setInfo('video', video_dictionary)
        li.setArt({'thumb': thumbnail})
        url = '{0}?action=play&video={1}'.format(self._url, path)
        return li, url

    def play_video(self, path):
        stream_service = urltostreamservice.UrlToStreamService(self._VRT_BASE,
                                                               self._VRTNU_BASE_URL,
                                                               self._addon)
        stream = stream_service.get_stream_from_url(path)
        if stream is not None:
            play_item = xbmcgui.ListItem(path=stream.stream_url)
            play_item.setMimeType('application/x-mpegURL')
            if stream.subtitle_url is not None:
                play_item.setSubtitles([stream.subtitle_url])
            xbmcplugin.setResolvedUrl(self._handle, True, listitem=play_item)

    def play_livestream(self, path):
        play_item = xbmcgui.ListItem(path=path)
        xbmcplugin.setResolvedUrl(self._handle, True, listitem=play_item)

    def __get_media(self, file_name):
        return os.path.join(self._addon_path, 'resources', 'media', file_name)

    @staticmethod
    def format_image_url(element):
        raw_thumbnail = element.find("img")['srcset'].split('1x,')[0]
        return statichelper.replace_double_slashes_with_https(raw_thumbnail)

    @staticmethod
    def __get_thumbnail_and_title(element):
        thumbnail = VRTPlayer.format_image_url(element)
        found_element = element.find(class_="tile__title")
        title = ""
        if found_element is not None:
            title = statichelper.replace_newlines_and_strip(found_element.contents[0])
        return thumbnail, title

    @staticmethod
    def __get_item(element, is_playable):
        thumbnail = VRTPlayer.format_image_url(element)
        found_element = element.find(class_="tile__title")
        li = None
        if found_element is not None:
            stripped = statichelper.replace_newlines_and_strip(found_element.contents[0])
            li = xbmcgui.ListItem(stripped)
            li.setProperty('IsPlayable', is_playable)
            li.setArt({'thumb': thumbnail})
        return li


