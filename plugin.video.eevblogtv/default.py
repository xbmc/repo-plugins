#   Copyright (C) 2017 Lunatixz
#
#
# This file is part of EEVBlogTV.
#
# EEVBlogTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EEVBlogTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EEVBlogTV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

import os, sys
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

# Plugin Info
ADDON_ID      = 'plugin.video.eevblogtv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH    = (REAL_SETTINGS.getAddonInfo('path').decode('utf-8'))
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')

def start():
    addDir(
        title="EEVBlog",
        url="plugin://plugin.video.youtube/user/EEVblog/")
    addDir(
        title="EEVBlog 2",
        url="plugin://plugin.video.youtube/user/eevblog2/")
    addDir(
        title="EEV Discovery",
        url="plugin://plugin.video.youtube/channel/UCkGvUEt8iQLmq3aJIMjT2qQ/")
    
def addDir(title, url):
    liz=xbmcgui.ListItem(title)
    liz.setProperty('IsPlayable', 'false')
    liz.setInfo(type="Video", infoLabels={"label":title,"title":title} )
    liz.setArt({'thumb':ICON,'fanart':FANART})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=True)
    
if __name__ == '__main__':
    start()
    xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)