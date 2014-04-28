#################################################################################################
# menu item loader thread
# this loads the favourites.xml and sets the windows props for the menus to auto display in skins
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import xml.etree.ElementTree as xml
import os
import threading

class LoadMenuOptionsThread(threading.Thread):

    logLevel = 0
    
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')        
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)           
    
        xbmc.log("XBMB3C LoadMenuOptionsThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)    
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C LoadMenuOptionsThread -> " + msg) 
    
    def run(self):
        self.logMsg("LoadMenuOptionsThread Started")
               
        lastFavPath = ""
        favourites_file = os.path.join(xbmc.translatePath('special://profile'), "favourites.xml")
        self.loadMenuOptions(favourites_file)
        lastFavPath = favourites_file
        
        try:
            lastModLast = os.stat(favourites_file).st_mtime
        except:
            lastModLast = 0;
        
        while (xbmc.abortRequested == False):
            
            favourites_file = os.path.join(xbmc.translatePath('special://profile'), "favourites.xml")
            try:
                lastMod = os.stat(favourites_file).st_mtime
            except:
                lastMod = 0;
            
            if(lastFavPath != favourites_file or lastModLast != lastMod):
                self.loadMenuOptions(favourites_file)
                
            lastFavPath = favourites_file
            lastModLast = lastMod
            
            xbmc.sleep(3000)
                        
        self.logMsg("LoadMenuOptionsThread Exited")

    def loadMenuOptions(self, pathTofavourites):
               
        self.logMsg("LoadMenuOptionsThread -> Loading menu items from : " + pathTofavourites)
        WINDOW = xbmcgui.Window( 10000 )
        menuItem = 0
        
        try:
            tree = xml.parse(pathTofavourites)
            rootElement = tree.getroot()
        except Exception, e:
            self.logMsg("LoadMenuOptionsThread -> Error Parsing favourites.xml : " + str(e), level=0)
            for x in range(0, 10):
                WINDOW.setProperty("xbmb3c_menuitem_name_" + str(x), "")
                WINDOW.setProperty("xbmb3c_menuitem_action_" + str(x), "")
            return
        
        for child in rootElement.findall('favourite'):
            name = child.get('name')
            action = child.text
        
            index = action.find("plugin://plugin.video.xbmb3c") # this addon
                
            if(index > -1 and len(action) > 10):
            
                action_url = action[index:]
                endIndex = action_url.find("\"")
                action_url = action_url[:endIndex]
                
                WINDOW.setProperty("xbmb3c_menuitem_name_" + str(menuItem), name)
                WINDOW.setProperty("xbmb3c_menuitem_action_" + str(menuItem), action_url)
                self.logMsg("xbmb3c_menuitem_name_" + str(menuItem) + " : " + name)
                self.logMsg("xbmb3c_menuitem_action_" + str(menuItem) + " : " + action_url)
                
                menuItem = menuItem + 1

        for x in range(menuItem, menuItem+10):
                WINDOW.setProperty("xbmb3c_menuitem_name_" + str(x), "")
                WINDOW.setProperty("xbmb3c_menuitem_action_" + str(x), "")
                self.logMsg("xbmb3c_menuitem_name_" + str(x) + " : ")
                self.logMsg("xbmb3c_menuitem_action_" + str(x) + " : ")
                
