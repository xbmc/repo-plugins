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
    This Python Module contains functions and variables that are 
    globally interesting to the ISY Browser XBMC addon.
    
    WRITTEN:    11/2012
'''
# IMPORTS
# xbmc
import xbmc
import xbmcaddon
# custom
import shared as self
import pyisy
import urls

# addon classes
events = None
browser = None

# connection to ISY controller
isy = None

# runtime parameters
__path__ = ''
__params__ = {}
__id__ = -1

# function shortcuts
translate = None
def events_enabled(): return events!=None

# common paths
__media__ = ''
__lib__ = ''

def initialize(args):
    '''
    initialize(args)
    
    DESCRIPTION:
    This function initialize the shared variable library.
    The only input to this function is the program's 
    system arguments.  There is no output.
    '''
    # check if events is available
    try:
        self.events = xbmcaddon.Addon('service.script.isyevents')
    except:
        self.events = None
        
    # get this addon
    self.browser = xbmcaddon.Addon('plugin.program.isybrowse')
    
    # get plugin information
    self.__path__ = args[0]
    self.__id__ = int(args[1])
    self.__params__ = urls.ParseUrl(args[2])['params']
    self.translate = self.browser.getLocalizedString
    
    # get common file paths
    self.__media__ = self.browser.getAddonInfo('path') + '/resources/media/'
    self.__lib__ = self.browser.getAddonInfo('path') + '/resources/lib/'
    
    # connect to isy
    username = self.browser.getSetting('username')
    password = self.browser.getSetting('password')
    host = self.browser.getSetting('host')
    port = int(self.browser.getSetting('port'))
    usehttps = self.browser.getSetting('usehttps') == 'true'
    self.isy = pyisy.open(username, password, host, port, usehttps)
    
    # verify isy opened correctly
    if self.isy.__dummy__:
        header = self.translate(35001)
        message = self.translate(35002)
        xbmc.executebuiltin('Notification(' + header + ',' + message + ', 15000)')