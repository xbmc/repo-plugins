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

import os
import sys

LIB_DIR = xbmc.translatePath( os.path.join( os.getcwd(), 'resources', 'lib' ) )
sys.path.append (LIB_DIR)

import xbmcaddon
import addonhelper

__settings__ = xbmcaddon.Addon(id='plugin.image.icanhascheezburger.com')
__language__ = __settings__.getLocalizedString

ahelper = addonhelper.AddonHelper()
home_page = "0"
home_page = __settings__.getSetting("home_page")
xbmc.log("===============================================================")
xbmc.log("Cheez started with url: %s, home: %s" % (sys.argv[2], home_page))
#home_pages = range(30211, 30229)

#home_page_index = str(home_pages.index(home_page))
def main_selection():
    import cheezburger_type_selection as plugin
    plugin.Main()

def current_selection():
    import current_cheez_selection as plugin
    plugin.Main()

def random_selection():
    import random_cheez_selection as plugin
    plugin.Main()

def current_list():
    import current_cheez_list as plugin
    xbmc.log("=====argv: '%s'" % sys.argv[2])
    if sys.argv[2] == '':
        xbmc.log("====Getting url by enum for %s" % home_page)
        url = ahelper.get_current_lol_url_by_enum(home_page)
        xbmc.log("===URL = %s" % url)
    else:
        url = ''
    xbmc.log("==Starting current list with url %s" % url)
    plugin.Main(url)

def random_list():
    import random_cheez_list as plugin
    plugin.Main()

page_map = {
 0: main_selection,
 1: current_selection,
 2: random_selection,
 3: current_list,
 4: current_list,
 5: current_list,
 6: current_list,
 7: current_list,
 8: current_list,
 9: random_list,
 10: random_list,
 11: random_list,
 12: random_list,
 13: random_list,
 14: random_list,
 15: random_list,
 16: random_list,
 17: random_list
}

page_map[int(home_page)]()



#if ( "action=list" in sys.argv[ 2 ] ):
#    if ("lol_type=current" in sys.argv[2]):
#        import current_cheez_list as plugin
#    else:
#        import random_cheez_list as plugin
#    plugin.Main()
#elif ("action=30405" in sys.argv[2] or (__settings__.getSetting("home_page") == "1" and "action=" not in sys.argv[2])):
#    #import current_cheez as plugin
#    import current_cheez_selection as plugin
#    plugin.Main()
#elif ("action=30406" in sys.argv[2] or (__settings__.getSetting("home_page") == "2" and "action=" not in sys.argv[2])):
#    import random_cheez_selection as plugin
#    plugin.Main()
#else:
#    xbmc.log( "[PLUGIN] %s v%s (%s)" % ( __plugin__, __version__, __date__ ), xbmc.LOGNOTICE )
#    import cheezburger_type_selection as plugin
#    plugin.Main()
