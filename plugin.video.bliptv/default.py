'''
    BlipTV plugin for XBMC
    Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import xbmcaddon
import xbmc
import xbmcplugin
import xbmcgui

try: import xbmcvfs
except: import xbmcvfsdummy as xbmcvfs

# plugin constants
version = "0.8.2"
plugin = "BlipTV-" + version
author = "TheCollective"
url = "www.xbmc.com"

# xbmc hooks
settings = xbmcaddon.Addon(id='plugin.video.bliptv')
language = settings.getLocalizedString
dbg = settings.getSetting("debug") == "true"
dbglevel = 3

# plugin structure 
scraper = ""
navigation = ""
downloader = ""
storage = ""
player = ""
common = ""
utils = ""

if (__name__ == "__main__" ):
    if dbg:
        print plugin + " ARGV: " + repr(sys.argv)
    else:
        print plugin

    try:
        import StorageServer
        cache = StorageServer.StorageServer("BlipTV")
    except:
        import storageserverdummy as StorageServer
        cache = StorageServer.StorageServer("BlipTV")

    import CommonFunctions as common
    common.plugin = plugin
    import BlipTVUtils as utils
    utils = utils.BlipTVUtils()
    import BlipTVStorage as storage
    storage = storage.BlipTVStorage()
    import BlipTVPlayer as player
    player = player.BlipTVPlayer()
    import SimpleDownloader as downloader
    downloader = downloader.SimpleDownloader()
    import BlipTVScraper as scraper
    scraper = scraper.BlipTVScraper()
    import BlipTVNavigation as navigation
    navigation = navigation.BlipTVNavigation()

    if (not settings.getSetting("firstrun")):
        settings.setSetting("firstrun", "1")

    if (not sys.argv[2]):
        navigation.listMenu()
    else:
        params = common.getParameters(sys.argv[2])
        get = params.get
        if (get("action")):
            navigation.executeAction(params)
        elif (get("path")):
            navigation.listMenu(params)
