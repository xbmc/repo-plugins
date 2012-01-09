# main imports
import os
import sys
import xbmc
import xbmcaddon
__addon__       = xbmcaddon.Addon()
__addonid__     = __addon__.getAddonInfo('id')
__addonname__   = __addon__.getAddonInfo('name')
__author__      = __addon__.getAddonInfo('author')
__version__     = __addon__.getAddonInfo('version')
__localize__    = __addon__.getLocalizedString
__addonpath__   = __addon__.getAddonInfo('path')
#Thanks to Nuka1195 for the original Apple Trailer plug-in

# plugin constants
__useragent__ = "QuickTime/7.6.5 (qtver=7.6.5;os=Windows NT 5.1Service Pack 3)"
#__useragent__ = "iTunes/9.0.2 (Windows; Microsoft Windows XP Professional Service Pack 3 (Build 2600)) AppleWebKit/531.21.8"




if ( __name__ == "__main__" ):
    if ( not sys.argv[ 2 ] ):
        import resources.lib.trailers as plugin
        plugin.Main()
    elif ( sys.argv[ 2 ].startswith( "?category=" ) ):
        import resources.lib.trailers as plugin
        plugin.Main()
    elif ( sys.argv[ 2 ].startswith( "?showtimes=" ) ):
        import resources.lib.showtimes as showtimes
        s = showtimes.GUI( "plugin-AMTII-showtimes.xml", xbmc.translatePath(__addonpath__), "default" )
        del s
    elif ( sys.argv[ 2 ].startswith( "?couchpotato=" ) ):
        import resources.lib.couchpotato as couchpotato
        couchpotato.Main()
    elif ( sys.argv[ 2 ].startswith( "?download=" ) ):
        import resources.lib.download as download
        download.Main()
    elif ( sys.argv[ 2 ].startswith( "?settings=" ) ):
        # open settings
        __addon__.openSettings()
        # refresh listing in case settings changed
        xbmc.executebuiltin( "Container.Refresh" )
