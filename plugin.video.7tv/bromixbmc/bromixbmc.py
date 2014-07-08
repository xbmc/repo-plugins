# -*- coding: utf-8 -*-

"""
Version 1.0.2 (2014.06.25)
- added 'getFavorites', 'addFavorite' and 'removeFavorite'
- set the encoding for the favorite routines to utf-8
- removed 'duration' and 'plot' from addVideoLink -> therefore use 'additionalInfoLabels'

Version 1.0.1 (2014.06.24)
- added support for helping with favorites
- initial release
"""

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import urllib
import urlparse
import os
import json

class Addon:
    def __init__(self, addon_id, argv):
        self.Id = addon_id
        self._Instance = xbmcaddon.Addon(id=self.Id)
        self.Handle = int(argv[1])
        self.Path = xbmc.translatePath(self._Instance.getAddonInfo('path'))
        self.Name = self._Instance.getAddonInfo('name')
        self.Icon = self._Instance.getAddonInfo('icon')
        self.DataPath = xbmc.translatePath("special://profile/addon_data/"+self.Id)
        self._FavsFile = os.path.join(self.DataPath, "favs.dat")
        if not os.path.isdir(self.DataPath):
            os.mkdir(self.DataPath)
        
    def getSetting(self, id):
        return self._Instance.getSetting(id)
    
    def localize(self, id):
        return self._Instance.getLocalizedString(id)
    
    def _loadFavs(self):
        favs = {'favs': {}}
        if self._FavsFile!=None:
            if os.path.exists(self._FavsFile):
                try:
                    file = open(self._FavsFile, 'r')
                    favs = json.loads(file.read(), encoding='utf-8')
                except:
                    pass
                
        return favs
    
    def getFavorites(self):
        favs = self._loadFavs()
        return favs.get('favs', {}).items()
    
    def addFavorite(self, id, newFav):
        favs = self._loadFavs()
        
        favs['favs'][id] = newFav
        self._storeFavs(favs)
        
    def removeFavorite(self, id):
        favs = self._loadFavs()
        fav = favs.get('favs', {}).get(id, None)
        if fav!=None:
            del favs['favs'][id]
            self._storeFavs(favs)
            
        return self.getFavorites()
    
    def _storeFavs(self, favs):
        if self._FavsFile!=None and favs!=None:
            with open(self._FavsFile, 'w') as outfile:
                json.dump(favs, outfile, sort_keys = True, indent = 4, encoding='utf-8')

class Bromixbmc:
    def __init__(self, addon_id, argv):
        self.Addon = Addon(addon_id, argv)
        
        self.BaseUrl = argv[0]
        
        # create a dictionary of the parameters
        self.Params = {}
        args = urlparse.parse_qs(argv[2][1:])
        for key in args:
            self.Params[key] = args[key][0]
    
    def getParam(self, name, default=None):
        if self.Params.has_key(name):
            return self.Params[name]
        return default
    
    def createUrl(self, params_dict=None):
        if params_dict!=None:
            return self.BaseUrl + '?' + urllib.urlencode(params_dict)
        
        # default
        return self.BaseUrl
    
    def showNotification(self, text):
        xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(self.AddonName,text, 5000, self.AddonIcon))
        
    def addDir(self, name, params={}, thumbnailImage="", fanart=None, contextMenu=None):
        url = self.createUrl(params)
        
        item = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumbnailImage)
        if fanart!=None:
            item.setProperty("fanart_image", fanart)
            
        if contextMenu!=None:
            item.addContextMenuItems(contextMenu);
            
        return xbmcplugin.addDirectoryItem(handle=self.Addon.Handle,url=url,listitem=item,isFolder=True)
    
    def addVideoLink(self, name, params={}, thumbnailImage="", fanart=None, additionalInfoLabels={}):
        url = self.createUrl(params)
        
        item = xbmcgui.ListItem(unicode(name), iconImage="DefaultVideo.png", thumbnailImage=thumbnailImage)
        
        # prepare infoLabels
        infoLabels = {'title': name}
        infoLabels.update(additionalInfoLabels)
            
        item.setInfo(type="video", infoLabels=infoLabels)
        item.setProperty('IsPlayable', 'true')
        if fanart!=None:
            item.setProperty("fanart_image", fanart)
        
        return xbmcplugin.addDirectoryItem(handle=self.Addon.Handle, url=url, listitem=item)