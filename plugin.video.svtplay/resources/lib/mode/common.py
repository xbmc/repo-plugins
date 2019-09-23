from __future__ import absolute_import,unicode_literals
import xbmcgui # pylint: disable=import-error
import xbmcplugin # pylint: disable=import-error

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
    # Settings
    S_HIDE_RESTRICTED_TO_SWEDEN = "hideonlysweden"
    S_HIDE_INAPPROPRIATE_FOR_CHILDREN = "inappropriateForChildren"

    def __init__(self, addon, plugin_url, plugin_handle, default_fanart):
        self.addon = addon
        self.plugin_url = plugin_url
        self.plugin_handle = plugin_handle
        self.default_fanart = default_fanart

    def add_directory_item(self, title, params, thumbnail="", folder=True, live=False, info=None):
        list_item = xbmcgui.ListItem(title)
        if live:
            list_item.setProperty("IsLive", "true")
        if not folder and params["mode"] == self.MODE_VIDEO:
            list_item.setProperty("IsPlayable", "true")
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
        if not folder and self.is_inappropriate_for_children(article):
            logging.log("Hiding content {} not appropriate for children as setting is on".format(article["title"]))
            return
        info = article["info"]
        self.add_directory_item(article["title"], params, article["thumbnail"], folder, False, info)

    def is_geo_restricted(self, program):
        return program["onlyAvailableInSweden"] and \
            helper.getSetting(self.S_HIDE_RESTRICTED_TO_SWEDEN)

    def is_inappropriate_for_children(self, video_item):
        """
        Can only be validated on video list items.
        """
        return video_item["inappropriateForChildren"] and \
            helper.getSetting(self.S_HIDE_INAPPROPRIATE_FOR_CHILDREN)

    def add_next_page_item(self, next_page, section):
        self.add_directory_item(
            "Next page", 
            {
                "page": next_page, 
                "mode": section
            }
        )