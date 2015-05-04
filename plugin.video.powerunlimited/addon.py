##############################################################################
#
# PowerUnlimited - Addon for XBMC
# http://www.pu.nl/
#
# Coding by Skipmode A1
# 
# Credits:
#   * Dan Dar3                                   - Gametrailers xbmc plugin [http://dandar3.blogspot.com]
#   * PowerUnlimited                                                        [http://www.pu.nl]
#   * Team XBMC @ XBMC.org                                                  [http://xbmc.org/]
#   * Leonard Richardson <leonardr@segfault.org> - BeautifulSoup            [http://www.crummy.com/software/BeautifulSoup/]
#

# 
# Constants
#
#also in ..._const
__addon__       = "plugin.video.powerunlimited"
__date__        = "04 May 2015"
__version__     = "1.0.2"

#
# Imports
#
import os
import re
import sys
import urllib, urllib2
import urlparse
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

LIB_DIR = xbmc.translatePath( os.path.join( xbmcaddon.Addon(id=__addon__).getAddonInfo('path'), 'resources', 'lib' ) )
sys.path.append (LIB_DIR)

#
# Get plugin settings
DEBUG = xbmcaddon.Addon(id='plugin.video.powerunlimited').getSetting('debug')

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    if (DEBUG) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) is starting, ARGV = %s" % ( __addon__, __version__, __date__, repr(sys.argv) ), xbmc.LOGNOTICE )
    import powerunlimited_main as plugin
else:
    action = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list':
        import powerunlimited_list as plugin
    #
    # Play
    #
    elif action == 'play':
        import powerunlimited_play as plugin

plugin.Main()
