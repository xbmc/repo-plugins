import json
import sys
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

        if item.get("info"):
            info.update(item.get("info"))

        listitem.setInfo("video", info)

        url = "{0}?{1}".format(self._plugin_url, quote(json.dumps(item.get("url_params"))))
        if item.get("folder"):
            xbmcplugin.addDirectoryItem(self._handle, url, listitem, isFolder=item.get("folder"))
        else:
            xbmcplugin.addDirectoryItem(self._handle, url, listitem)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        xbmcplugin.endOfDirectory(self._handle)
        return False
