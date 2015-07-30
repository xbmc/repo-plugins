##############################################################################
#
# Roosterteeth - Addon for Kodi
# http://www.roosterteeth.com/
#
# Coding by Skipmode A1
# 
# Credits:
#   * Dan Dar3                                   - Gametrailers kodi plugin [http://dandar3.blogspot.com]
#   * Roosterteeth                                                          [http://www.roosterteeth.com]
#   * Team KODI                                                             [http://kodi.tv/]
#   * Leonard Richardson <leonardr@segfault.org> - BeautifulSoup            [http://www.crummy.com/software/BeautifulSoup/]
#   * Kenneth Reitz                              - Requests                 [http://docs.python-requests.org/en/latest/]
#

# 
# Constants
#
#also in ..._const
__addon__       = "plugin.video.roosterteeth"
__date__        = "29 July 2015"
__version__     = "1.2.0"

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

reload(sys)  
sys.setdefaultencoding('utf8')

LIB_DIR = xbmc.translatePath( os.path.join( xbmcaddon.Addon(id=__addon__).getAddonInfo('path'), 'resources', 'lib' ) )
sys.path.append (LIB_DIR)

# Get plugin settings
DEBUG = xbmcaddon.Addon(id='plugin.video.roosterteeth').getSetting('debug')

# Parse parameters...
if len(sys.argv[2]) == 0:
    #
    # Main menu
    #
    if (DEBUG) == 'true':
        xbmc.log( "[ADDON] %s v%s (%s) is starting, ARGV = %s" % ( __addon__, __version__, __date__, repr(sys.argv) ), xbmc.LOGNOTICE )
    import roosterteeth_main as plugin
else:
    action = urlparse.parse_qs(urlparse.urlparse(sys.argv[2]).query)['action'][0]
    #
    # List
    #
    if action == 'list-episodes':
        import roosterteeth_list_episodes as plugin
    #
    # List Shows
    #
    if action == 'list-shows':
        import roosterteeth_list_shows as plugin
    #
    # Play
    #
    elif action == 'play':
        import roosterteeth_play as plugin

plugin.Main()