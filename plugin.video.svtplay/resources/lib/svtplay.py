from __future__ import absolute_import, unicode_literals

import os
import re
import sys

import xbmc  # pylint: disable=import-error
import xbmcaddon  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error
import xbmcplugin  # pylint: disable=import-error
from resources.lib import helper, logging
from resources.lib.api import svt
from resources.lib.api.graphql import GraphQL
from resources.lib.listing.listitem import PlayItem
from resources.lib.playback import Playback
from resources.lib.settings import Settings

try:
  # Python 2
  from urllib import quote
  from urllib import urlencode
except ImportError:
  # Python 3
  from urllib.parse import quote
  from urllib.parse import urlencode

class BlockedForChildrenException(BaseException): #pylint: disable=function-redefined
    def __init__(self):
        pass

class SvtPlay:
    # List modes
    MODE_LIVE_PROGRAMS = "live"
    MODE_LATEST = "latest"
    MODE_LATEST_NEWS = 'news'
    MODE_POPULAR = "popular"
    MODE_LAST_CHANCE = "last_chance"
    MODE_CHANNELS = "kanaler"
    MODE_A_TO_O = "a-o"
    MODE_SEARCH = "search"
    MODE_CATEGORIES = "categories"
    MODE_LETTER = "letter"
    MODE_CATEGORY = "category"
    MODE_VIDEO = "video"
    MODE_PROGRAM = "program"

    def __init__(self, plugin_handle, plugin_url):
        self.addon = xbmcaddon.Addon()
        self.localize = self.addon.getLocalizedString
        self.settings = Settings(self.addon)
        self.plugin_url = plugin_url
        self.plugin_handle = plugin_handle
        self.graphql = GraphQL()
        self.playback = Playback(plugin_handle)
        xbmcplugin.setContent(plugin_handle, "tvshows")
        xbmcplugin.addSortMethod(plugin_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(plugin_handle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(plugin_handle, xbmcplugin.SORT_METHOD_DATEADDED)
        self.default_fanart = os.path.join(
            xbmc.translatePath(self.addon.getAddonInfo("path") + "/resources/images/"),
            "background.png")
    
    def run(self, plugin_params):
        arg_params = helper.get_url_parameters(plugin_params)
        logging.log("Addon params: {}".format(arg_params))
        arg_mode = arg_params.get("mode")
        arg_id = arg_params.get("id", "")
        if self.settings.kids_mode and not arg_params:
            logging.log("Kids mode, redirecting to genre Barn")
            arg_mode = self.MODE_CATEGORY
            arg_id = "barn"

        try:
            self.navigate(arg_mode, arg_id, arg_params)
        except BlockedForChildrenException:
            dialog = xbmcgui.Dialog()
            dialog.ok("SVT Play", self.addon.getLocalizedString(30504))
            return

        cacheToDisc = True
        if not arg_params:
            # No params means top-level menu.
            # The top-level menu should not be cached as it will prevent
            # Kids mode to take effect when toggled on.
            cacheToDisc = False
        xbmcplugin.endOfDirectory(self.plugin_handle, cacheToDisc=cacheToDisc)

    def navigate(self, mode, id, params):
        if not mode:
            self.view_start()
        elif mode == self.MODE_A_TO_O:
            if self.settings.alpha_program_listing:
                self.view_alpha_directories()
            else:
                self.view_a_to_z()
        elif mode == self.MODE_CATEGORIES:
            self.view_categories()
        elif mode == self.MODE_CATEGORY:
            self.view_category(id)
        elif mode == self.MODE_PROGRAM:
            self.view_episodes(id)
        elif mode == self.MODE_VIDEO:
            self.start_video(id)
        elif mode == self.MODE_POPULAR or \
            mode == self.MODE_LATEST or \
            mode == self.MODE_LAST_CHANCE or \
            mode == self.MODE_LIVE_PROGRAMS:
            self.view_start_section(mode)
        elif mode == self.MODE_LATEST_NEWS:
            self.view_latest_news()
        elif mode == self.MODE_CHANNELS:
            self.view_channels()
        elif mode == self.MODE_LETTER:
            self.view_programs_by_letter(params.get("letter"))
        elif mode == self.MODE_SEARCH:
            self.view_search()

    def view_start(self):
        self.__add_directory_item(self.localize(30009), {"mode": self.MODE_POPULAR})
        self.__add_directory_item(self.localize(30003), {"mode": self.MODE_LATEST})
        self.__add_directory_item(self.localize(30004), {"mode": self.MODE_LATEST_NEWS})
        self.__add_directory_item(self.localize(30010), {"mode": self.MODE_LAST_CHANCE})
        self.__add_directory_item(self.localize(30002), {"mode": self.MODE_LIVE_PROGRAMS})
        self.__add_directory_item(self.localize(30008), {"mode": self.MODE_CHANNELS})
        self.__add_directory_item(self.localize(30000), {"mode": self.MODE_A_TO_O})
        self.__add_directory_item(self.localize(30001), {"mode": self.MODE_CATEGORIES})
        self.__add_directory_item(self.localize(30006), {"mode": self.MODE_SEARCH})


    def view_alpha_directories(self):
        letters = svt.getAlphas()
        if not letters:
            return
        for letter in letters:
            self.__add_directory_item(
                letter, 
                {
                    "mode": self.MODE_LETTER,
                    "letter": letter.encode("utf-8")
                }
            )

    def view_a_to_z(self):
        programs = self.graphql.getAtoO()
        self.__create_dir_items(programs)

    def view_programs_by_letter(self, letter):
        programs = self.graphql.getProgramsByLetter(letter)
        self.__create_dir_items(programs)

    def view_categories(self):
        categories = self.graphql.getGenres()
        for category in categories:
            self.__add_directory_item(
                category["title"],
                {
                    "mode": self.MODE_CATEGORY, 
                    "id": category["genre"]
                }
            )

    def view_start_section(self, section):
        items = []
        if section == self.MODE_POPULAR:
            items = self.graphql.getPopular()
        elif section == self.MODE_LATEST:
            items = self.graphql.getLatest()
        elif section == self.MODE_LAST_CHANCE:
            items = self.graphql.getLastChance()
        elif section == self.MODE_LIVE_PROGRAMS:
            items = self.graphql.getLive()
        else:
            raise ValueError("Section {} is not supported!".format(section))
        if not items:
            return
        self.__create_dir_items(items)

    def view_channels(self):
        channels = svt.getChannels()
        if not channels:
            return
        self.__create_dir_items(channels)

    def view_latest_news(self ):
        items = self.graphql.getLatestNews()
        if not items:
            return
        self.__create_dir_items(items)

    def view_category(self, genre):
        play_items = self.graphql.getProgramsForGenre(genre)
        if not play_items:
            return
        self.__create_dir_items(play_items)

    def view_episodes(self, slug):
        logging.log("View episodes for {}".format(slug))
        episodes = self.graphql.getVideoContent(slug)
        if episodes is None:
            logging.log("No episodes found")
            return
        self.__create_dir_items(episodes)

    def view_search(self):
        keyword = helper.getInputFromKeyboard(self.localize(30102))
        if keyword == "" or not keyword:
            self.view_start()
            return
        keyword = quote(keyword)
        logging.log("Search string: " + keyword)
        keyword = re.sub(r" ", "+", keyword)
        keyword = keyword.strip()
        play_items = self.graphql.getSearchResults(keyword)
        self.__create_dir_items(play_items)

    def start_video(self, video_url):
        channel_pattern = re.compile(r'^ch\-')
        logging.log("Start video for {}".format(video_url))
        if channel_pattern.search(video_url):
            video_json = svt.getVideoJSON(video_url)
        else:
            legacy_id = video_url.split("/")[2]
            video_data = self.graphql.getVideoDataForLegacyId(legacy_id)
            if self.settings.inappropriate_for_children and video_data["blockedForChildren"]:
                raise BlockedForChildrenException()
            video_json = svt.getSvtVideoJson(video_data["svtId"])
        self.__resolve_and_play_video(video_json)

    def __add_directory_item(self, title, params, thumbnail="", folder=True, live=False, info=None, fanart=""):
        list_item = xbmcgui.ListItem(title)
        if live:
            list_item.setProperty("IsLive", "true")
        if not folder and params["mode"] == self.MODE_VIDEO:
            list_item.setProperty("IsPlayable", "true")
            show_url = svt.episodeUrlToShowUrl(params["id"])
            if show_url:
                context_go_to_params = {
                    "mode" : self.MODE_PROGRAM,
                    "id" : show_url
                }
                urlToShow = self.plugin_url + '?' + urlencode(context_go_to_params)
                list_item.addContextMenuItems([(self.localize(30602), 'ActivateWindow(Videos,'+urlToShow+')')])            
        if info:
            info["playcount"] = 0
            list_item.setInfo("video", info)
        else:
            list_item.setInfo("video", { "title" : title, "playcount" : 0 })
        list_item.setArt({
            "fanart": fanart,
            "thumb": thumbnail
        })
        url = self.plugin_url + '?' + urlencode(params)
        xbmcplugin.addDirectoryItem(self.plugin_handle, url, list_item, folder)

    def __create_dir_items(self, play_items):
        for play_item in play_items:
            self.__create_dir_item(play_item)

    def __create_dir_item(self, play_item):
        params = {}
        params["mode"] = self.MODE_PROGRAM if play_item.item_type == PlayItem.SHOW_ITEM else self.MODE_VIDEO
        params["id"] = play_item.id
        folder = False
        if play_item.item_type == PlayItem.SHOW_ITEM:
            folder = True
        info = None
        if self.__is_geo_restricted(play_item):
            logging.log("Hiding geo restricted item {} as setting is on".format(play_item.title))
            return
        info = play_item.info
        fanart = play_item.fanart if play_item.item_type == PlayItem.VIDEO_ITEM else ""
        self.__add_directory_item(play_item.title, params, play_item.thumbnail, folder, False, info, fanart)

    def __is_geo_restricted(self, play_item):
        return play_item.geo_restricted and \
            self.settings.geo_restriction
    
    def __resolve_and_play_video(self, video_json):
        if video_json is None:
            logging.log("ERROR: Could not get video JSON")
            return
        try:
            show_obj = svt.resolveShowJson(video_json)
        except ValueError:
            logging.log("Could not decode JSON for {}".format(video_json))
            return
        if show_obj["videoUrl"]:
            self.playback.play_video(show_obj["videoUrl"], show_obj.get("subtitleUrl", None), self.settings.show_subtitles)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok("SVT Play", self.localize(30100))
