# coding: utf-8
# 
# put.io xbmc addon
# Copyright (C) 2009  Alper Kanat <alper@put.io>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# 

import os
import sys

import xbmc
import xbmcaddon as xa

from resources.lib.common import PutIO
from resources.lib.exceptions import *
from resources.lib.gui import *

PLUGIN_ID = "plugin.video.putio"

pluginUrl = sys.argv[0]
pluginId = int(sys.argv[1])
itemId = sys.argv[2].lstrip("?")
addon = xa.Addon(PLUGIN_ID)

try:
    putio = PutIO(addon.getAddonInfo("id"))
    
    if itemId:
        item = putio.getItem(itemId)

        if item.type == "folder":
            populateDir(pluginUrl, pluginId, putio.getFolderListing(itemId))
        elif item.type == "movie":
            play(item, subtitle = putio.getSubtitle(item))
        else:
            play(item)
    else:
        populateDir(pluginUrl, pluginId, putio.getRootListing())
except PutioAuthFailureException, e:
    xbmc.executebuiltin("XBMC.Notification(%s, %s, %d, %s)" % (
        e.header,
        e.message,
        e.duration,
        os.path.join(addon.getAddonInfo("path"), "resources", "images", "error.png")
    ))
