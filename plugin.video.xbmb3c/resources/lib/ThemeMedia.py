#################################################################################################
# Start of ThemeMedia Thread
# plays theme music when applicable
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
import urllib
import urllib2
import random

from Utils import PlayUtils
from DownloadUtils import DownloadUtils

#define our global download utils
downloadUtils = DownloadUtils()

class ThemeMediaThread(threading.Thread):

    playingTheme = False
    playingMovie = False
    themeId = ''
    volume = ''
    themeMusicMap = {}
    themeMoviesMap = {}
    
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')        
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)           
    
        xbmc.log("XBMB3C ThemeMediaThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)    
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C ThemeMediaThread -> " + msg)
    
    def run(self):
        self.logMsg("Started")
        self.updateThemeMedia()
        lastRun = datetime.today()
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        themeRefresh = 2
        
        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            secTotal = td.seconds
            
            if (secTotal > themeRefresh) and xbmcgui.Window(10000).getProperty("ThemeMediaMB3Disable") != "true":
                self.updateThemeMedia()
                lastRun = datetime.today()
            elif xbmcgui.Window(10000).getProperty("ThemeMediaMB3Disable") == "true":
                if not xbmc.Player().isPlaying():
                    xbmc.log("ThemeThread playback complete restarting thread")
                    xbmcgui.Window(10000).clearProperty('ThemeMediaMB3Disable')
                
            xbmc.sleep(2000)
            
        self.logMsg("Exited")

      
    def updateThemeMedia(self):
        self.logMsg("updateThemeMedia Called")
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        WINDOW = xbmcgui.Window( 10025 ) 
        newid = xbmc.getInfoLabel('ListItem.Property(ItemGUID)')
        if newid == '' and xbmcgui.getCurrentWindowId() == 10025:
           self.logMsg("updateThemeMedia Called using 10025 id"+ xbmc.getInfoLabel( "ListItem.Path" ))       
           newid =  WINDOW.getProperty("ItemGUID")
        if newid == '' and xbmcgui.getCurrentWindowId() == 10000:
           newid =  xbmcgui.Window( 10000 ) .getProperty("ItemGUID")
        
        if newid != self.themeId:
            if self.playingTheme == True:
              if  xbmc.Player().isPlaying():
                self.stop()
                xbmc.sleep(1500)
        id = xbmc.getInfoLabel('ListItem.Property(ItemGUID)')
        if id == '' and xbmcgui.getCurrentWindowId() == 10025:
           self.logMsg("updateThemeMedia Called had a sleep using 10025 id")      
           id =  WINDOW.getProperty("ItemGUID")
        if id == '' and xbmcgui.getCurrentWindowId() == 10000:
           self.logMsg("updateThemeMedia Called had a sleep using 10000 id")      
           id =  xbmcgui.Window( 10000 ).getProperty("ItemGUID")
        if id != newid:
            return
        self.logMsg("updateThemeMedia itemGUID : " + id)
        if self.isPlayingZone() and self.isChangeTheme():
            self.themeId = id 
            themeMusicUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Items/" + id + "/ThemeSongs?format=json"
            self.logMsg("updateThemeMedia themeUrl : " + themeMusicUrl)
            if themeMusicUrl not in self.themeMusicMap:
                jsonData = downloadUtils.downloadUrl(themeMusicUrl, suppress=False, popup=1 )
                themeMusic = json.loads(jsonData)     
               
                if(themeMusic == None):
                    themeMusic = []
                self.logMsg("updateThemeMedia added music theme to map : " + themeMusicUrl)    
                self.themeMusicMap[themeMusicUrl] = themeMusic
            elif themeMusicUrl in self.themeMusicMap:
                themeMusic = self.themeMusicMap.get(themeMusicUrl)
                self.logMsg("updateThemeMedia retrieved music theme from map : " + themeMusicUrl)
                
                
            themeMoviesUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Items/" + id + "/ThemeVideos?format=json"
            if themeMoviesUrl not in self.themeMoviesMap:
                jsonData = downloadUtils.downloadUrl(themeMoviesUrl, suppress=False, popup=1 )
                themeMovies = json.loads(jsonData)  
               
                if(themeMovies == None):
                    themeMovies = []
                self.logMsg("updateThemeMovie added movies theme to map : " + themeMoviesUrl)    
                self.themeMoviesMap[themeMoviesUrl] = themeMovies
            elif themeMoviesUrl in self.themeMoviesMap:
                themeMovies = self.themeMoviesMap.get(themeMoviesUrl)
                self.logMsg("updateThemeMovie retrieved movies theme from map : " + themeMoviesUrl)
            
            
            if addonSettings.getSetting('useThemeMovies') == "true" :
               themeItems = themeMovies.get("Items")
               self.playingMovie = True
               if themeItems == [] and addonSettings.getSetting('useThemeMusic') == "true" :
                   themeItems = themeMusic.get("Items")
                   self.playingMovie = False
            elif addonSettings.getSetting('useThemeMusic') == "true" :
               themeItems = themeMusic.get("Items")
               self.playingMovie = False
               
            if themeItems != []:
                themePlayUrl = PlayUtils().getPlayUrl(mb3Host + ":" + mb3Port,themeItems[0].get("Id"),themeItems[0])
                self.logMsg("updateThemeMedia themePath : " + str(themePlayUrl))
                self.playingTheme = True
                self.setVolume(60)
                if self.playingMovie == True:
                    xbmc.Player().play(themePlayUrl,windowed=True)
                else:
                    xbmc.Player().play(themePlayUrl)
                ThemeTunesStatus.setAliveState(True)
                
            elif themeItems == [] and self.playingTheme == True:
                self.stop(True)
        
        if not self.isPlayingZone() and self.playingTheme == True:
            # stop
            if  xbmc.Player().isPlaying():
                self.stop()
            self.setVolume(self.volume) 
            
        if not self.isPlayingZone() and self.playingTheme == False:
            ThemeTunesStatus.setAliveState(False)   
                
    def stop(self, forceStop = False):
        # Only stop if playing 
        if xbmc.Player().isPlaying() or forceStop == True:
            self.playingTheme = False
            cur_vol = self.getVolume()
            
            # Calculate how fast to fade the theme, this determines
            # the number of step to drop the volume in
            #numSteps = 15
            #vol_step = cur_vol / numSteps
            # do not mute completely else the mute icon shows up
            #for step in range (0,(numSteps-1)):
             #   vol = cur_vol - vol_step
              #  self.setVolume(vol)
               # cur_vol = vol
                #xbmc.sleep(200)
            xbmc.Player().stop()
            ThemeTunesStatus.setAliveState(False)
        
            self.setVolume(self.volume)
        
    # Works out if the currently displayed area on the screen is something
    # that is deemed a zone where themes should be played
    def isPlayingZone(self):
        if "plugin://plugin.video.xbmb3c" in xbmc.getInfoLabel( "ListItem.Path" ):
            return True
        if xbmcgui.getCurrentWindowId() == 10025 or xbmcgui.getCurrentWindowId() == 10000:
            return True 
        
        # Any other area is deemed to be a non play area
        return False 
    
    # Works out if we should change/start a theme
    def isChangeTheme(self):
        id = xbmc.getInfoLabel('ListItem.Property(ItemGUID)')
        WINDOW = xbmcgui.Window( 10025 )
        if id == '' and xbmcgui.getCurrentWindowId() == 10025:    
           id =  WINDOW.getProperty("ItemGUID")
        if id == '' and xbmcgui.getCurrentWindowId() == 10000:    
           id =  xbmcgui.Window( 10000 ).getProperty("ItemGUID")
        if id != "":
            if self.volume == '':
                self.volume = self.getVolume()
            # we have something to start with
            addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c') 
            if addonSettings.getSetting('useThemeMusic') == "true" or addonSettings.getSetting('useThemeMovies') == "true" :
              # cool theme music is on continue
              if id == self.themeId:
                  # same as before now do we need to restart 
                  if ((addonSettings.getSetting('loopThemeMusic') == "true"  and self.playingMovie == False) or (addonSettings.getSetting('loopThemeMovies') == "true" and self.playingMovie == True))  and xbmc.Player().isPlaying() == False:
                      self.logMsg("isChangeTheme restart true")
                      return True
              if id != self.themeId:
                  # new id return true
                  self.logMsg("isChangeTheme new id restart true")
                  return True  
              
        # still here return False
        self.logMsg("isChangeTheme restart false") 
        return False 
    
    # This will return the volume in a range of 0-100
    def getVolume(self):
        result = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Application.GetProperties", "params": { "properties": [ "volume" ] }, "id": 1}')

        json_query = json.loads(result)
        if "result" in json_query and json_query['result'].has_key('volume'):
            # Get the volume value
            volume = json_query['result']['volume']

        return volume

    # Sets the volume in the range 0-100
    def setVolume(self, newvolume):
        # Can't use the RPC version as that will display the volume dialog
        # '{"jsonrpc": "2.0", "method": "Application.SetVolume", "params": { "volume": %d }, "id": 1}'
        # xbmc.executebuiltin('XBMC.SetVolume(%d)' % newvolume, True)
        return
     
###############################################################
# Class to make it easier to see the current state of ThemeMedia
###############################################################
class ThemeTunesStatus():
    @staticmethod
    def isAlive():
        return xbmcgui.Window(10000).getProperty("ThemeMediaMB3IsAlive") == "true"

    @staticmethod
    def setAliveState(state):
        if state:
            xbmcgui.Window(10000).setProperty("ThemeMediaMB3IsAlive", "true")
        else:
            xbmcgui.Window(10000).clearProperty('ThemeMediaMB3IsAlive')

 