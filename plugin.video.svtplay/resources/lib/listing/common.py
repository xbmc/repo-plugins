from __future__ import absolute_import,unicode_literals
import xbmcgui # pylint: disable=import-error
import xbmcplugin # pylint: disable=import-error

from resources.lib.playback import Playback
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

    def add_directory_item(self, title, params, thumbnail="", folder=True, live=False, info=None):
        list_item = xbmcgui.ListItem(title)
        if live:
            list_item.setProperty("IsLive", "true")
        if not folder and params["mode"] == self.MODE_VIDEO:
            list_item.setProperty("IsPlayable", "true")
            show_url = helper.episodeUrlToShowUrl(params["url"])
            if show_url:
                context_go_to_params = {
                    "mode" : self.MODE_PROGRAM,
                    "url" : show_url
                }
                urlToShow = self.plugin_url + '?' + urlencode(context_go_to_params)
                list_item.addContextMenuItems([(self.localize(30602), 'ActivateWindow(Videos,'+urlToShow+')')])            
        fanart = info.get("fanart", "") if info else self.default_fanart
        poster = info.get("poster", "") if info else ""
        if info:
            if "fanart" in info:
                del info["fanart"] # Unsupported by ListItem
            if "poster" in info:
                del info["poster"] # Unsupported by ListItem
            list_item.setInfo("video", info)
        list_item.setArt({
            "fanart": fanart,
            "poster": poster if poster else thumbnail,
            "thumb": thumbnail
        })
        url = self.plugin_url + '?' + urlencode(params)
        xbmcplugin.addDirectoryItem(self.plugin_handle, url, list_item, folder)

    def create_dir_item(self, article, mode):
        """
        Given an article and a mode; create directory item
        for the article.
        """
        params = {}
        params["mode"] = mode
        params["url"] = article["url"]
        folder = False
        if mode == self.MODE_PROGRAM:
            folder = True
        info = None
        if self.is_geo_restricted(article):
            logging.log("Hiding geo restricted item {} as setting is on".format(article["title"]))
            return
        info = article["info"]
        self.add_directory_item(article["title"], params, article["thumbnail"], folder, False, info)

    def is_geo_restricted(self, program):
        return program["onlyAvailableInSweden"] and \
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
        for episode in episodes:
            self.create_dir_item(episode, self.MODE_VIDEO)
