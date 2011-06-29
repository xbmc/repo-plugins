'''
    YouTube plugin for XBMC
    Copyright (C) 2010 Tobias Ussing And Henrik Mosgaard Jensen
    
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

import sys, xbmc, xbmcaddon

# plugin constants
__version__ = "2.0.5"
__plugin__ = "YouTube-" + __version__
__author__ = "TheCollective"
__url__ = "www.xbmc.com"
__settings__ = xbmcaddon.Addon(id='plugin.video.youtube')
__language__ = __settings__.getLocalizedString
__dbg__ = __settings__.getSetting( "debug" ) == "true"

if (__name__ == "__main__" ):
    if __dbg__:
        print __plugin__ + " ARGV: " + repr(sys.argv)
    else:
        print __plugin__
    import YouTubeNavigation as navigation
    navigator = navigation.YouTubeNavigation()
    
    if ( not __settings__.getSetting( "firstrun" ) ):
        navigator.login()
        __settings__.setSetting( "firstrun", '1' )
        
    if (not sys.argv[2]):
        navigator.listMenu()
    else:
        params = navigator.getParameters(sys.argv[2])
        get = params.get
        if (get("action")):
            navigator.executeAction(params)
        elif (get("path")):
            navigator.listMenu(params)
