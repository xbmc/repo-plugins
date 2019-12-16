from __future__ import absolute_import,unicode_literals
import xbmcgui # pylint: disable=import-error
import xbmcplugin # pylint: disable=import-error

from resources.lib.playback import Playback
from resources.lib.listing.listitem import PlayItem
from resources.lib import helper
from resources.lib import logging

try:
  # Python 2
  from urllib import urlencode
except ImportError:
  # Python 3
  from urllib.parse import urlencode

class Common:
    # Item types
    MODE_VIDEO = "video"
    MODE_PROGRAM = "pr"

    def __init__(self, addon, plugin_url, plugin_handle, default_fanart, settings):
        self.addon = addon
        self.localize = addon.getLocalizedString
        self.plugin_url = plugin_url
        self.plugin_handle = plugin_handle
        self.default_fanart = default_fanart
        self.playback = Playback(plugin_handle)
        self.settings = settings

    def add_directory_item(self, title, params, thumbnail="", folder=True, live=False, info=None, fanart=""):
        list_item = xbmcgui.ListItem(title)
        if live:
            list_item.setProperty("IsLive", "true")
        if not folder and params["mode"] == self.MODE_VIDEO:
            list_item.setProperty("IsPlayable", "true")
            show_url = helper.episodeUrlToShowUrl(params["id"])
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

    def create_dir_items(self, play_items):
        for play_item in play_items:
            self.create_dir_item(play_item)

    def create_dir_item(self, play_item):
        params = {}
        params["mode"] = self.MODE_PROGRAM if play_item.item_type == PlayItem.SHOW_ITEM else self.MODE_VIDEO
        params["id"] = play_item.id
        folder = False
        if play_item.item_type == PlayItem.SHOW_ITEM:
            folder = True
        info = None
        if self.is_geo_restricted(play_item):
            logging.log("Hiding geo restricted item {} as setting is on".format(play_item.title))
            return
        info = play_item.info
        fanart = play_item.fanart if play_item.item_type == PlayItem.VIDEO_ITEM else ""
        self.add_directory_item(play_item.title, params, play_item.thumbnail, folder, False, info, fanart)

    def is_geo_restricted(self, play_item):
        return play_item.geo_restricted and \
            self.settings.geo_restriction
    
    def start_video(self, video_json):
        if video_json is None:
            logging.log("ERROR: Could not get video JSON")
            return
        try:
            show_obj = helper.resolveShowJSON(video_json)
        except ValueError:
            logging.log("Could not decode JSON for {}".format(video_json))
            return
        if show_obj["videoUrl"]:
            self.playback.play_video(show_obj["videoUrl"], show_obj.get("subtitleUrl", None), self.settings.show_subtitles)
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok("SVT Play", self.localize(30100))

    def view_episodes(self, episodes):
        """
        Displays the episodes for a program
        """
        if episodes is None:
            logging.log("No episodes found")
            return
        self.create_dir_items(episodes)
