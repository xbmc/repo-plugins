# -*- coding: utf-8 -*-
# system imports
from __future__ import absolute_import,unicode_literals
import os
import sys
import urllib
import xbmc # pylint: disable=import-error
import xbmcaddon # pylint: disable=import-error
import xbmcplugin # pylint: disable=import-error
# own imports
from resources.lib import helper
from resources.lib import logging
from resources.lib.mode.normallist import NormalList
try:
  # Python 2
  from urllib import unquote_plus
except ImportError:
  # Python 3
  from urllib.parse import unquote_plus

# plugin setup
PLUGIN_HANDLE = int(sys.argv[1])
PLUGIN_URL = sys.argv[0]
addon = xbmcaddon.Addon("plugin.video.svtplay")
xbmcplugin.setContent(PLUGIN_HANDLE, "tvshows")
xbmcplugin.addSortMethod(PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL)

DEFAULT_FANART = os.path.join(
  xbmc.translatePath(addon.getAddonInfo("path") + "/resources/images/"),
  "background.png")

normal_listing = NormalList(addon, PLUGIN_URL, PLUGIN_HANDLE, DEFAULT_FANART)

# Main segment of script
ARG_PARAMS = helper.getUrlParameters(sys.argv[2])
logging.log("params: {}".format(ARG_PARAMS))
ARG_MODE = ARG_PARAMS.get("mode")
ARG_URL = unquote_plus(ARG_PARAMS.get("url", ""))
ARG_PAGE = ARG_PARAMS.get("page")
if not ARG_PAGE:
  ARG_PAGE = "1"

normal_listing.route(ARG_MODE, ARG_URL, ARG_PARAMS, int(ARG_PAGE))

xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
