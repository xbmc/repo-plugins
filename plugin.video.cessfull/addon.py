# coding: utf-8
# 
# Cessfull xbmc addon
# Copyright (C) 2014  Team Cessfull
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
# 

import os
import sys
import xbmc
import xbmcaddon as xa
import resources.lib.cessfullapi as cessfullapi

PLUGIN_ID = "plugin.video.cessfull"

pluginUrl = sys.argv[0]
pluginId = int(sys.argv[1])
itemId = sys.argv[2].lstrip("?")
addon = xa.Addon(PLUGIN_ID)

try:
    thegui = xg
except:
    import xbmcgui
    thegui = xbmcgui

try:
    thexp = xp
except:
    import xbmcplugin
    thexp = xbmcplugin


class CessfullAuthFailureException(Exception):
    def __init__(self, header, message, duration=10000, icon="error.png"):
        self.header = header
        self.message = message
        self.duration = duration
        self.icon = icon

def populateDir(pluginUrl, pluginId, listing):    
   
    for item in listing:                        
        
        screenshot = ""

        url = "%s?%s" % (pluginUrl, item.id)
        listItem = thegui.ListItem(
            item.name,
            item.name,
            screenshot,
            screenshot
        )
        
        listItem.setInfo(item.content_type, {
               'originaltitle': item.name,
               'title': item.name,
               'sorttitle':item.name
        })

        thexp.addDirectoryItem(
            pluginId,
            url,
            listItem,
            "folder" == item.content_type
        )
        
    thexp.endOfDirectory(pluginId)


def play(item, subtitle=None):
    player = xbmc.Player()
    
    screenshot = ""
    
    listItem = thegui.ListItem(
        item.name,
        item.name,
        screenshot,
        screenshot
    )
    
    listItem.setInfo('audio', {'Title': item.name})
    player.play(item.link, listItem)
    
    if subtitle:
        player.setSubtitles(subtitle)

class CessfullApiHandler(object):
    """
    Class to handle cessfull api calls for XBMC actions
    
    """
    
    wantedItemTypes = ("folder", "movie", "audio", "unknown", "file")
    subtitleTypes = ("srt", "sub")
    
    def __init__(self, pluginId):        
        self.addon = xa.Addon(pluginId)
        self.username = self.addon.getSetting("email").lower()       
        self.password = self.addon.getSetting("password")     
        if not self.username and self.password:
            raise CessfullAuthFailureException(
                self.addon.getLocalizedString(30010),
                self.addon.getLocalizedString(30011)
            )
        
        self.checktoken = cessfullapi.AuthHelper(self.username, self.password)
        self.password = self.checktoken.get_authentication_url()
        if not self.password:
            raise CessfullAuthFailureException(
                self.addon.getLocalizedString(30010),
                self.addon.getLocalizedString(30011)
            )
        self.apiclient = cessfullapi.Client(self.username, self.password)
        
    def getItem(self, itemId):
        return self.apiclient.File.GET(itemId)
    
    def getRootListing(self):
        items = []        
        for item in self.apiclient.File.list(id_parent=0):
            if item.content_type:
                if self.showable(item):
                    items.append(item)                    
        
        return items
    
    def showable(self, item):
        if hasattr(item, 'content_type'):
            if 'audio' in item.content_type:
                return True
            elif 'video' in item.content_type:
                return True
            elif "folder" in item.content_type:
                return True
            else:
                return False
        xbmc.log(item)
        return True

    def getFolderListing(self, folderId, isItemFilterActive=True):
        items = []        
        for item in self.apiclient.File.list(id_parent=folderId):
            if isItemFilterActive and not self.showable(item):
                continue
            items.append(item)        
        return items
    
    def getSubtitle(self, item):
        fileName, extension = os.path.splitext(item.name)        
        for i in self.getFolderListing(item.id_parent, False):
            if item.content_type != "folder":
                fn, ext = os.path.splitext(i.name)                
                if i.name.find(fileName) != -1 and (ext.lstrip(".") in self.subtitleTypes):
                    return i.stream_url

try:
    cessfull = CessfullApiHandler(addon.getAddonInfo("id"))
    if itemId:
        item = cessfull.getItem(itemId)
        if hasattr(item, 'content_type'):
            if item.content_type == "folder":
                populateDir(pluginUrl, pluginId, cessfull.getFolderListing(itemId))
            elif "video" in item.content_type:
                play(item, subtitle=cessfull.getSubtitle(item))
        else:            
            play(item)
    else:
        populateDir(pluginUrl, pluginId, cessfull.getRootListing())
except CessfullAuthFailureException, e:
    xbmc.executebuiltin("XBMC.Notification(%s, %s, %d, %s)" % (
        e.header,
        e.message,
        e.duration,
        os.path.join(addon.getAddonInfo("path"), "resources", "images", "error.png")
    ))
