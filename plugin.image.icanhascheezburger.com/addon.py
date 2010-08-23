##############################################################################
# ICanHasCheezBurger = XBMC Addon
#
# based on Comics.com - XBMC picture plugin by Dan Dar3
#
# Coding by Brian Millham <brian@millham.net>
#
# Credits:
#   * Team XBMC @ XBMC.org                                                [http://xbmc.org/]
#   * Leonard Richardson <leonardr@segfault.org>  - BeautifulSoup 3.0.7a  [http://www.crummy.com/software/BeautifulSoup/]
#   * Eric Lawrence      <e_lawrence@hotmail.com> - Fiddler Web Debugger  [http://www.fiddler2.com]
# 
# Constants
#
__plugin__  = "ICanHasCheezburger.com"
__author__  = "Brian Millham <brian@millham.net>"
__url__     = "http://github.com/bmillham/plugin.pictures.icanhascheezburger.com"
__date__    = "20 August 2010"
__version__ = "0.3"

#
# Imports
#
import os
import sys

LIB_DIR = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'lib' ) )
sys.path.append (LIB_DIR)

import xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.image.icanhascheezburger.com')
__language__ = __settings__.getLocalizedString

if ( "action=list" in sys.argv[ 2 ] ):
    import random_cheez_list as plugin
    plugin.Main()
elif ("action=30405" in sys.argv[2]):
    import current_cheez as plugin
    plugin.Main()
elif ("action=30406" in sys.argv[2]):
    import random_cheez_selection as plugin
    plugin.Main()
else:
    xbmc.log( "[PLUGIN] %s v%s (%s)" % ( __plugin__, __version__, __date__ ), xbmc.LOGNOTICE )
    import cheezburger_type_selection as plugin
    plugin.Main()
