import json
import sys
import time
from datetime import datetime
from os import path
from urllib import quote

import xbmcaddon
import xbmcgui
import xbmcplugin


class Menu(object):
    _plugin_url = sys.argv[0]
    _handle = int(sys.argv[1])
    _addon_path = None

    def __init__(self, sort_methods):
        addon = xbmcaddon.Addon("plugin.video.nfl-teams")
        self._addon_path = addon.getAddonInfo("path")

        for method in sort_methods:
            self._add_sort_method(method)

    def _add_sort_method(self, sort_method="none"):
        if sort_method == "none":
            xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_NONE)
        elif sort_method == "alpha":
            xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_LABEL)
            xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        elif sort_method == "date":
            xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_DATE)

    def add_item(self, item):
        listitem = xbmcgui.ListItem()
        listitem.setLabel(item.get("name"))

        thumbnail = item.get("thumbnail")
        if thumbnail.startswith("resources"):
            thumbnail = path.join(self._addon_path, thumbnail)
        listitem.setThumbnailImage(thumbnail)

        fanart = path.join(self._addon_path, "resources", "images", "fanart", "{0}.jpg".format(item.get("url_params")["team"]))
        listitem.setProperty("fanart_image", fanart)

        info = {"title": item.get("name")}

        if item.get("raw_metadata"):
            info["plot"] = item.get("raw_metadata").get("description", "No description was given for the video.").encode("utf-8").replace("&hellip;", "...")
            date = self.parse_video_date(item.get("raw_metadata").get("date"))
            if date:
                info["date"] = date.strftime("%d.%m.%Y")
                info["plot"] = "Added on {0}.\n{1}".format(date.strftime("%c"), info["plot"])

        listitem.setInfo("video", info)

        url = "{0}?{1}".format(self._plugin_url, quote(json.dumps(item.get("url_params"))))
        if item.get("folder"):
            xbmcplugin.addDirectoryItem(self._handle, url, listitem, isFolder=item.get("folder"))
        else:
            xbmcplugin.addDirectoryItem(self._handle, url, listitem)

    @classmethod
    def parse_video_date(cls, date_string):
        if date_string:
            try:
                return datetime.strptime(date_string, "%m/%d/%Y %H:%M:%S")
            except TypeError:
                # Workaround for bug in XBMC: http://forum.xbmc.org/showthread.php?tid=112916
                return datetime.fromtimestamp(time.mktime(time.strptime(date_string, "%m/%d/%Y %H:%M:%S")))
        else:
            return None

    def _end_directory(self):
        xbmcplugin.endOfDirectory(self._handle)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._end_directory()
        return False
