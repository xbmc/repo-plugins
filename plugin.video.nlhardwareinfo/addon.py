##############################################################################
#
# NlHardwareInfo - Addon for XBMC
# http://nl.hardware.info/
#
# Coding by Skipmode A1
# 
# Credits:
#   * Dan Dar3                                   - Gamespot xbmc plugin [http://dandar3.blogspot.com]
#   * NlHardwareInfo                                                    [http://nl.hardware.info]
#   * Team XBMC @ XBMC.org                                              [http://xbmc.org/]
#   * Leonard Richardson <leonardr@segfault.org> - BeautifulSoup 3.0.7a [http://www.crummy.com/software/BeautifulSoup/]
#   * Eric Lawrence <e_lawrence@hotmail.com>     - Fiddler Web Debugger [http://www.fiddler2.com]
#   * http://nl.hardware.info/
#

# 
# Constants
#
#also in ..._const
__addon__       = "plugin.video.nlhardwareinfo"
__date__        = "06 september 2014"
__version__     = "1.0.3"

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
DEBUG = xbmcaddon.Addon(id='plugin.video.nlhardwareinfo').getSetting('debug')

if (DEBUG) == 'true':
    xbmc.log( "[ADDON] %s v%s (%s) is starting, ARGV = %s" % ( __addon__, __version__, __date__, repr(sys.argv) ), xbmc.LOGNOTICE )

import nlhardwareinfo_list_play as plugin

plugin.Main()