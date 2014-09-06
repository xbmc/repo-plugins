##############################################################################
#
# Botchamania - Addon for XBMC
# http://www.botchamania.com/
#
# Coding by Skipmode A1
# 
# Credits:
#   * Botchamania                                                           [http://www.botchamania.com]
#   * Team XBMC @ XBMC.org                                                  [http://xbmc.org/]
#   * Leonard Richardson <leonardr@segfault.org> - BeautifulSoup            [http://www.crummy.com/software/BeautifulSoup/]
#   * Eric Lawrence <e_lawrence@hotmail.com>     - Fiddler Web Debugger     [http://www.fiddler2.com]
#

# 
# Constants
#
#also in ..._const
__addon__       = "plugin.video.botchamania"
__date__        = "06 september 2014"
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
DEBUG = xbmcaddon.Addon(id='plugin.video.botchamania').getSetting('debug')

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    if (DEBUG) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) is starting, ARGV = %s" % ( __addon__, __version__, __date__, repr(sys.argv) ), xbmc.LOGNOTICE )
    import botchamania_main as plugin
else:
    action = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # archive
    #
    if action == 'list-archive':
        import botchamania_list_archive as plugin
    #
    # List
    #
    elif action == 'list':
        import botchamania_list as plugin
    #
    # Play
    #
    elif action == 'play':
        import botchamania_play as plugin

plugin.Main()
