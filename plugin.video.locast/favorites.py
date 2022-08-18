#   Copyright (C) 2021 Lunatixz
#
#
# This file is part of Locast.
#
# Locast is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Locast is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Locast.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-
import sys, os, re, json
from six.moves import urllib
from kodi_six  import xbmcaddon, xbmcgui, xbmc

# Plugin Info
ADDON_ID      = 'plugin.video.locast'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

def notificationDialog(message, header=ADDON_NAME, sound=False, time=1000, icon=ICON):
    try:    return xbmcgui.Dialog().notification(header, message, icon, time, sound)
    except: return xbmc.executebuiltin("Notification(%s, %s, %d, %s)" % (header, message, time, icon))

def getFavorites():
    return json.loads((REAL_SETTINGS.getSetting('favorites') or '{"favorites":[]}')).get('favorites',[])
     
def isFavorite(chnumber):
    return str(chnumber) in getFavorites()
     
def addFavorite(chname, chnumber, silent=False):
    favorites = getFavorites()
    if chnumber not in favorites:
        favorites.append(chnumber)
        REAL_SETTINGS.setSetting('favorites',json.dumps({"favorites":favorites}))
        if not silent: notificationDialog(LANGUAGE(49007)%(chname))
    
def delFavorite(chname, chnumber):
    favorites = getFavorites()
    if chnumber in favorites:
        favorites.pop(favorites.index(chnumber))
        REAL_SETTINGS.setSetting('favorites',json.dumps({"favorites":favorites}))
        notificationDialog(LANGUAGE(49008)%(chname))
  
class Favorites:    
    def __init__(self, sysARG=sys.argv):
        self.sysARG = sysARG
        
    def run(self): 
        params  = json.loads(urllib.parse.unquote(self.sysARG[1]))
        mode   = (params.get("mode",'')     or None)
        chname = (params.get("chname",'')   or '')
        chnum  = (params.get("chnum",'')    or '-1')
        if mode == None : return 
        if mode == 'add': addFavorite(chname,chnum)
        if mode == 'del': delFavorite(chname,chnum)
        
if __name__ == '__main__': Favorites(sys.argv).run()