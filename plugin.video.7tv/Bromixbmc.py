import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

import urllib
import urlparse

class Addon:
    def __init__(self, addon_id, argv):
        self.Id = addon_id
        self._Instance = xbmcaddon.Addon(id=self.Id)
        self.Handle = int(argv[1])
        self.Path = xbmc.translatePath(self._Instance.getAddonInfo('path'))
        self.Name = self._Instance.getAddonInfo('name')
        self.Icon = self._Instance.getAddonInfo('icon')
        self.DataPath = xbmc.translatePath("special://profile/addon_data/"+self.Id)
        
    def getSetting(self, id):
        return self._Instance.getSetting(id)
    
    def localize(self, id):
        return self._Instance.getLocalizedString(id)

class Bromixbmc:
    def __init__(self, addon_id, argv):
        self.Addon = Addon(addon_id, argv)
        
        self.LocalizeMapping = {}
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
    
    def createUrl(self, params_dict):
        return self.BaseUrl + '?' + urllib.urlencode(params_dict)
    
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
    
    def addVideoLink(self, name, params={}, thumbnailImage="", duration="", fanart=None):
        url = self.createUrl(params)
        
        item = xbmcgui.ListItem(unicode(name), iconImage="DefaultVideo.png", thumbnailImage=thumbnailImage)
        item.setInfo(type="video", infoLabels={"title": name, "duration": duration})
        item.setProperty('IsPlayable', 'true')
        if fanart!=None:
            item.setProperty("fanart_image", fanart)
        
        return xbmcplugin.addDirectoryItem(handle=self.Addon.Handle, url=url, listitem=item)