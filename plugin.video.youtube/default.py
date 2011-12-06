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

import sys, xbmc, xbmcplugin, xbmcaddon, xbmcgui, urllib2, cookielib
try: 
	import xbmcvfs
except ImportError: 
	import xbmcvfsdummy as xbmcvfs


# plugin constants
version = "2.8.0"
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
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
urllib2.install_opener(opener)

if (__name__ == "__main__" ):
	if dbg:
		print plugin + " ARGV: " + repr(sys.argv)
	else:
		print plugin
	

	try:
		import StorageServer
	except:
		import storageserverdummy as StorageServer
	cache = StorageServer.StorageServer()
	cache.table_name = "YouTube"

	import CommonFunctions
	common = CommonFunctions.CommonFunctions() 
	common.plugin = plugin
	import YouTubeUtils
	utils = YouTubeUtils.YouTubeUtils()
	import YouTubeStorage
	storage = YouTubeStorage.YouTubeStorage()
	import YouTubeCore
	core = YouTubeCore.YouTubeCore()
	import YouTubeLogin
	login = YouTubeLogin.YouTubeLogin()
	import YouTubeFeeds
	feeds = YouTubeFeeds.YouTubeFeeds()
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

	if ( not settings.getSetting( "firstrun" ) ):
		login.login()
		settings.setSetting( "firstrun", '1' )
	
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
	
