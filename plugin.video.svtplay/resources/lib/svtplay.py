from __future__ import absolute_import,unicode_literals
import os
import sys
import xbmc # pylint: disable=import-error
import xbmcaddon # pylint: disable=import-error
import xbmcplugin # pylint: disable=import-error

from resources.lib.settings import Settings
from resources.lib.listing.router import Router
from resources.lib import logging
from resources.lib import helper

class SvtPlay:

    def __init__(self, plugin_handle, plugin_url, plugin_params):
        self.addon = xbmcaddon.Addon()
        self.settings = Settings(self.addon)
        self.plugin_url = plugin_url
        self.plugin_handle = plugin_handle
        xbmcplugin.setContent(plugin_handle, "tvshows")
        xbmcplugin.addSortMethod(plugin_handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(plugin_handle, xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(plugin_handle, xbmcplugin.SORT_METHOD_DATEADDED)
        self.default_fanart = os.path.join(
            xbmc.translatePath(self.addon.getAddonInfo("path") + "/resources/images/"),
            "background.png")
        self.arg_params = helper.get_url_parameters(plugin_params)
        logging.log("Addon params: {}".format(self.arg_params))
        self.arg_mode = self.arg_params.get("mode")
        self.arg_url = self.arg_params.get("url", "")
        self.arg_page = self.arg_params.get("page")
        if not self.arg_page:
            self.arg_page = "1"
    
    def run(self):
        if self.settings.kids_mode and not self.arg_params:
            logging.log("Kids mode, redirecting to genre Barn")
            self.arg_mode = Router.MODE_CATEGORY
            self.arg_url = "barn"

        router = Router(self.addon, self.plugin_url, self.plugin_handle, self.default_fanart, self.settings)
        router.route(self.arg_mode, self.arg_url, self.arg_params, int(self.arg_page))

        cacheToDisc = True
        if not self.arg_params:
            # No params means top-level menu.
            # The top-level menu should not be cached as it will prevent
            # Kids mode to take effect when toggled on.
            cacheToDisc = False
        xbmcplugin.endOfDirectory(self.plugin_handle, cacheToDisc=cacheToDisc)
