##############################################################################
#
# Tweakers - Addon for XBMC
# http://www.tweakers.net/
#
# Coding by Skipmode A1
# 
# Credits:
#   * Dan Dar3                                   - Gametrailers xbmc plugin [http://dandar3.blogspot.com]
#   * Tweakers                                                              [http://www.tweakers.net]
#   * Team XBMC @ XBMC.org                                                  [http://xbmc.org/]
#   * Leonard Richardson <leonardr@segfault.org> - BeautifulSoup            [http://www.crummy.com/software/BeautifulSoup/]
#

# 
# Constants
#
#also in ..._const
__addon__       = "plugin.video.tweakers"
__date__        = "7 july 2013"
__version__     = "1.0.1"

#
# Imports
#
import os
import re
import sys
import urllib
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

LIB_DIR = xbmc.translatePath( os.path.join( xbmcaddon.Addon(id=__addon__).getAddonInfo('path'), 'resources', 'lib' ) )
sys.path.append (LIB_DIR)

# Get plugin settings
DEBUG = xbmcaddon.Addon(id="plugin.video.tweakers").getSetting('debug')

# Parse parameters
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    if (DEBUG) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) is starting, ARGV = %s" % ( __addon__, __version__, __date__, repr(sys.argv) ), xbmc.LOGNOTICE )
    import tweakers_list as plugin
else:
    action = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list':
        import tweakers_list as plugin
    #
    # Play
    #
    elif action == 'play':
        import tweakers_play as plugin

plugin.Main()
