'''
    ISY Browser for XBMC
    Copyright (C) 2012 Ryan M. Kraus

    LICENSE:
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
    DESCRIPTION:
    This XBMC addon interfaces an ISY-99 type Home Automation Controller
    (from Universal Devices Incorporated) with XBMC.
    
    WRITTEN:    11/2012
'''

# CONSTANTS
__author__ = 'Humble Robot'
__version__ = '0.2.0'
__url__ = 'https://code.google.com/p/isy-events/'
__date__ = '4/2013'

# IMPORTS
# system
import sys
# xbmc
import xbmcaddon
# custom
lib_path = xbmcaddon.Addon('plugin.program.isybrowse' ).getAddonInfo('path') + '/resources/lib/'
sys.path.append(lib_path)
import shared
import actions
import menus

# DEBUGGING
# monitor inputs
#print '*******************' + str(sys.argv)
#print '*******************' + str(__params__)
        
# MAIN LOOP
if __name__ == "__main__":
    # initialize shared library
    shared.initialize(sys.argv)

    if shared.__params__['cmd'] != None:
        # an action was requested
        actions.DoAction(shared.__params__['addr'], shared.__params__['cmd'])
        actions.RefreshWindow()
    
    else:
        # a folder was requested
        menu = menus.main(shared.__id__, shared.__params__['browsing'], shared.events_enabled(), shared.__params__['addr'])
        menu.sendToXbmc()
        menu.show()