'''
    YouTube plugin for XBMC
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
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
import urllib2
import cookielib
try:
    import xbmcvfs
except ImportError:
    import xbmcvfsdummy as xbmcvfs

# plugin constants
version = "4.4.4"
plugin = "YouTube-" + version
author = "TheCollective"
url = "www.xbmc.com"

# xbmc hooks
settings = xbmcaddon.Addon(id='plugin.video.youtube')
language = settings.getLocalizedString
dbg = settings.getSetting("debug") == "true"
dbglevel = 3

# plugin structure
feeds = ""
scraper = ""
playlist = ""
navigation = ""
downloader = ""
storage = ""
login = ""
player = ""
cache = ""

cookiejar = cookielib.LWPCookieJar()
cookie_handler = urllib2.HTTPCookieProcessor(cookiejar)
opener = urllib2.build_opener(cookie_handler)

if (__name__ == "__main__" ):
    if dbg:
        print plugin + " ARGV: " + repr(sys.argv)
    else:
        print plugin

    try:
        import StorageServer
        cache = StorageServer.StorageServer("YouTube")
    except:
        import storageserverdummy as StorageServer
        cache = StorageServer.StorageServer("YouTube")

    import CommonFunctions as common
    common.plugin = plugin

    import YouTubeUtils
    utils = YouTubeUtils.YouTubeUtils()
    import YouTubeStorage
    storage = YouTubeStorage.YouTubeStorage()
    import YouTubePluginSettings
    pluginsettings = YouTubePluginSettings.YouTubePluginSettings()
    import YouTubeCore
    core = YouTubeCore.YouTubeCore()
    import YouTubeLogin
    login = YouTubeLogin.YouTubeLogin()
    import YouTubeFeeds
    feeds = YouTubeFeeds.YouTubeFeeds()
    import YouTubeSubtitleControl
    subtitles = YouTubeSubtitleControl.YouTubeSubtitleControl()
    import YouTubePlayer
    player = YouTubePlayer.YouTubePlayer()
    import SimpleDownloader as downloader
    downloader = downloader.SimpleDownloader()
    import YouTubeScraper
    scraper = YouTubeScraper.YouTubeScraper()
    import YouTubePlaylistControl
    playlist = YouTubePlaylistControl.YouTubePlaylistControl()
    import YouTubeNavigation
    navigation = YouTubeNavigation.YouTubeNavigation()

    if (not settings.getSetting("firstrun")):
        login.login()
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
        else:
            print plugin + " ARGV Nothing done.. verify params " + repr(params)
