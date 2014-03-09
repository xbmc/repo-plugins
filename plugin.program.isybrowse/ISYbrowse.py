# CONSTANTS
__author__ = 'Automicus'
__version__ = '1.0.0'
__url__ = 'http://automic.us'
__date__ = '2/2014'

# IMPORTS
# system
import sys
# xbmc
import xbmcaddon
# custom
lib_path = xbmcaddon.Addon('plugin.program.isybrowse'). \
    getAddonInfo('path') + '/resources/lib/'
sys.path.append(lib_path)
import shared
import actions
import menus

# MAIN LOOP
if __name__ == "__main__":
    # initialize shared library
    shared.initialize(sys.argv)

    if shared.__params__['cmd'] is not None:
        # an action was requested
        actions.DoAction(shared.__params__['addr'], shared.__params__['cmd'])
        actions.RefreshWindow()

    else:
        # a folder was requested
        menu = menus.main(shared.__id__, shared.__params__['browsing'],
                          shared.events_enabled(), shared.__params__['addr'])
        menu.sendToXbmc()
        menu.show()
