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

import sys, xbmcaddon

# plugin constants
__version__ = "2.5.0"
__plugin__ = "YouTube" + __version__
__author__ = "TheCollective"
__url__ = "www.xbmc.com"

# xbmc hooks
__settings__ = xbmcaddon.Addon(id='plugin.video.youtube')
__language__ = __settings__.getLocalizedString
__dbg__ = __settings__.getSetting("debug") == "true"

# plugin structure
__utils__ = "" 
__core__ = ""
__scraper__ = ""
__playlist__ = ""
__navigation__ = ""
__downloader__ = ""
__storage__ = ""
__login__ = ""
__player__ = ""

if (__name__ == "__main__" ):
	import YouTubeUtils as utils
	__utils__ = utils.YouTubeUtils()
	import YouTubeLogin as login
	__login__ = login.YouTubeLogin()
	import YouTubeStorage as storage
	__storage__ = storage.YouTubeStorage()
	import YouTubeCore as core
	__core__ = core.YouTubeCore()
	import YouTubePlayer as player
	__player__ = player.YouTubePlayer()
	import YouTubeDownloader as downloader
	__downloader__ = downloader.YouTubeDownloader()
	import YouTubeScraperCore as scraper
	__scraper__ = scraper.YouTubeScraperCore()
	import YouTubePlaylistControl as playlist
	__playlist__ = playlist.YouTubePlaylistControl()
	import YouTubeNavigation as navigation
	__navigation__ = navigation.YouTubeNavigation()

	if __dbg__:
		print __plugin__ + " ARGV: " + repr(sys.argv)
	else:
		print __plugin__
	
	if ( not __settings__.getSetting( "firstrun" ) ):
		__login__.login()
		__settings__.setSetting( "firstrun", '1' )
	
	if (not sys.argv[2]):
		__navigation__.listMenu()
	else:
		params = __utils__.getParameters(sys.argv[2])
		get = params.get
		if (get("action")):
			__navigation__.executeAction(params)
		elif (get("path")):
			__navigation__.listMenu(params)