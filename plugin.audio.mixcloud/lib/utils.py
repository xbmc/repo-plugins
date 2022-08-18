# -*- coding: utf-8 -*-

'''
@author: jackyNIX

Copyright (C) 2011-2020 jackyNIX

This file is part of KODI Mixcloud Plugin.

KODI Mixcloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

KODI Mixcloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with KODI Mixcloud Plugin.  If not, see <http://www.gnu.org/licenses/>.
'''



import os
import sys
import json
from datetime import datetime
from urllib import parse
import xbmc
import xbmcaddon
import xbmcplugin
import re
import traceback



# static variables
__addon__ = xbmcaddon.Addon('plugin.audio.mixcloud')



class Utils:
    # logging functions
    @staticmethod
    def log(message, err = None):
        if err:
            xbmc.log(msg = 'MIXCLOUD ' + message, level = xbmc.LOGERROR)
            xbmc.log(msg = 'MIXCLOUD ' + traceback.format_exc(), level = xbmc.LOGERROR)
        elif __addon__.getSetting('debug') == 'true':
            xbmc.log(msg = 'MIXCLOUD ' + message, level = xbmc.LOGINFO)



    # icons
    @staticmethod
    def getIcon(iconname):
        return xbmc.translatePath(os.path.join(__addon__.getAddonInfo('path'), 'resources', 'icons', iconname))



    @staticmethod
    def getQuery(query = ''):
        keyboard = xbmc.Keyboard(query)
        keyboard.doModal()
        if keyboard.isConfirmed():
            query = keyboard.getText()
        else:
            query = ''
        return query 



    @staticmethod
    def isValidURL(url):
        regex = re.compile(
                r'^(?:http|ftp)s?://' # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
                r'localhost|' #localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
                r'(?::\d+)?' # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return re.match(regex, url) is not None
        


    # arguments
    @staticmethod
    def encodeArguments(parameters):
        return sys.argv[0] + '?' + parse.urlencode(parameters)

    @staticmethod
    def getArguments():
        paramDict = {}
        parameters = parse.unquote(sys.argv[2])
        if parameters:
            paramPairs = parameters[1:].split('&')
            for paramsPair in paramPairs:
                paramSplits = paramsPair.split('=')
                if len(paramSplits) == 2:
                    paramDict[paramSplits[0]] = paramSplits[1]
        return paramDict



    @staticmethod
    def copyValue(sourcedata, sourcekey, targetdata, targetkey):
        if sourcekey in sourcedata and sourcedata[sourcekey]:
            targetdata[targetkey] = sourcedata[sourcekey]
            return True
        else:
            return False



    # settings
    @staticmethod
    def getSetting(name):
        return __addon__.getSetting(name)

    @staticmethod
    def setSetting(name, value):
        __addon__.setSetting(name, value)

    @staticmethod
    def getVersion():
        return __addon__.getAddonInfo('version')

    @staticmethod
    def getChangeLog():
        return __addon__.getAddonInfo('changelog').strip()