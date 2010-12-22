import sys, xbmc, xbmcaddon

REMOTE_DBG = False

# plugin constants
__version__ = "1.0.0"
__plugin__ = "Vimeo-" + __version__
__author__ = "TheCollective"
__url__ = "www.xbmc.com"
__svn_url__ = ""
__svn_revision__ = "$Revision$"
__XBMC_Revision__ = "32430"
__settings__ = xbmcaddon.Addon(id='plugin.video.vimeo')
__language__ = __settings__.getLocalizedString
__dbg__ = __settings__.getSetting( "debug" ) == "true"

if (__name__ == "__main__" ):
    if __dbg__:
        print __plugin__ + " ARGV: " + repr(sys.argv)
    else:
        print __plugin__
    import VimeoNavigation as navigation
    navigator = navigation.VimeoNavigation()
    
    if ( not __settings__.getSetting( "firstrun" ) ):
        __settings__.setSetting( "firstrun", '1' )
        navigator.login()
        
    if (not sys.argv[2]):
        navigator.listMenu()
    else:
        params = navigator.getParameters(sys.argv[2])
        get = params.get
        if (get("action")):
            navigator.executeAction(params)
        elif (get("path")):
            navigator.listMenu(params)
