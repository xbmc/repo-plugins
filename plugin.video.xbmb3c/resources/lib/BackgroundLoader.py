#################################################################################################
# Start of BackgroundRotationThread
# Sets a backgound property to a fan art link
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

class BackgroundRotationThread(threading.Thread):

    movie_art_links = []
    tv_art_links = []
    music_art_links = []
    global_art_links = []
    current_movie_art = 0
    current_tv_art = 0
    current_music_art = 0
    current_global_art = 0
    linksLoaded = False
    logLevel = 0
    
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')        
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)           
    
        xbmc.log("XBMB3C BackgroundRotationThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)    
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C BackgroundRotationThread -> " + msg)
    
    def run(self):
        self.logMsg("Started")
        
        try:
            self.loadLastBackground()
        except Exception, e:
            self.logMsg("loadLastBackground Exception : " + str(e), level=0)
        
        self.updateArtLinks()
        self.setBackgroundLink()
        lastRun = datetime.today()
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        backgroundRefresh = int(addonSettings.getSetting('backgroundRefresh'))
        if(backgroundRefresh < 10):
            backgroundRefresh = 10
        
        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            secTotal = td.seconds
            
            if(secTotal > backgroundRefresh):
                if(self.linksLoaded == False):
                    self.updateArtLinks()
                self.setBackgroundLink()
                lastRun = datetime.today()
                
                backgroundRefresh = int(addonSettings.getSetting('backgroundRefresh'))
                if(backgroundRefresh < 10):
                    backgroundRefresh = 10                

            xbmc.sleep(3000)
        
        try:
            self.saveLastBackground()
        except Exception, e:
            self.logMsg(str(e), level=0)  
            
        self.logMsg("Exited")

    def loadLastBackground(self):
        
        __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )         
        
        lastDataPath = __addondir__ + "LastBgLinks.json"
        dataFile = open(lastDataPath, 'r')
        jsonData = dataFile.read()
        dataFile.close()
        
        self.logMsg(jsonData)
        result = json.loads(jsonData)
        
        WINDOW = xbmcgui.Window( 10000 )
        if(result.get("global") != None):
            self.logMsg("Setting Global Last : " + str(result.get("global")), level=2)
            WINDOW.setProperty("MB3.Background.Global.FanArt", result.get("global")["url"])       

        if(result.get("movie") != None):
            self.logMsg("Setting Movie Last : " + str(result.get("movie")), level=2)
            WINDOW.setProperty("MB3.Background.Movie.FanArt", result.get("movie")["url"])      
            
        if(result.get("tv") != None):
            self.logMsg("Setting TV Last : " + str(result.get("tv")), level=2)
            WINDOW.setProperty("MB3.Background.TV.FanArt", result.get("tv")["url"])    

        if(result.get("music") != None):
            self.logMsg("Setting Music Last : " + str(result.get("music")), level=2)
            WINDOW.setProperty("MB3.Background.Music.FanArt", result.get("music")["url"])   
        
    def saveLastBackground(self):
    
        data = {}
        if(len(self.global_art_links) > 0):
            data["global"] = self.global_art_links[self.current_global_art]
        if(len(self.movie_art_links) > 0):
            data["movie"] = self.movie_art_links[self.current_movie_art]
        if(len(self.tv_art_links) > 0):
            data["tv"] = self.tv_art_links[self.current_tv_art]
        if(len(self.music_art_links) > 0):
            data["music"] = self.music_art_links[self.current_music_art]

        __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )            
            
        lastDataPath = __addondir__ + "LastBgLinks.json"
        dataFile = open(lastDataPath, 'w')
        stringdata = json.dumps(data)
        self.logMsg("Last Background Links : " + stringdata)
        dataFile.write(stringdata)
        dataFile.close()        
    
    def setBackgroundLink(self):
    
        # load the background blacklist
        __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )         
        lastDataPath = __addondir__ + "BlackListedBgLinks.json"
        
        black_list = []
        
        # load blacklist data
        try:
            dataFile = open(lastDataPath, 'r')
            jsonData = dataFile.read()
            dataFile.close()        
            black_list = json.loads(jsonData)
            self.logMsg("Loaded Background Black List : " + str(black_list))
        except:
            self.logMsg("No Background Black List found, starting with empty Black List")
            black_list = []    


        WINDOW = xbmcgui.Window( 10000 )
        
        if(len(self.movie_art_links) > 0):
            next, url = self.findNextLink(self.movie_art_links, black_list, self.current_movie_art)
            self.current_movie_art = next
            WINDOW.setProperty("MB3.Background.Movie.FanArt", url)
            self.logMsg("MB3.Background.Movie.FanArt=" + url)
        
        if(len(self.tv_art_links) > 0):
            self.logMsg("setBackgroundLink index tv_art_links " + str(self.current_tv_art + 1) + " of " + str(len(self.tv_art_links)), level=2)
            artUrl =  self.tv_art_links[self.current_tv_art]["url"]
            WINDOW.setProperty("MB3.Background.TV.FanArt", artUrl)
            self.logMsg("MB3.Background.TV.FanArt=" + artUrl)
            self.current_tv_art = self.current_tv_art + 1
            if(self.current_tv_art == len(self.tv_art_links)):
                self.current_tv_art = 0
                
        if(len(self.music_art_links) > 0):
            self.logMsg("setBackgroundLink index music_art_links " + str(self.current_music_art + 1) + " of " + str(len(self.music_art_links)), level=2)
            artUrl =  self.music_art_links[self.current_music_art]["url"] 
            WINDOW.setProperty("MB3.Background.Music.FanArt", artUrl)
            self.logMsg("MB3.Background.Music.FanArt=" + artUrl)
            self.current_music_art = self.current_music_art + 1
            if(self.current_music_art == len(self.music_art_links)):
                self.current_music_art = 0
            
        if(len(self.global_art_links) > 0):
            next, url = self.findNextLink(self.global_art_links, black_list, self.current_global_art)
            self.current_global_art = next
            WINDOW.setProperty("MB3.Background.Global.FanArt", url)
            self.logMsg("MB3.Background.Global.FanArt=" + url)
           
    def isBlackListed(self, blackList, bgInfo):
        for blocked in blackList:
            if(bgInfo["parent"] == blocked["parent"]):
                self.logMsg("Block List Parents Match On : " + str(bgInfo) + " : " + str(blocked), level=1)
                if(blocked["index"] == -1 or bgInfo["index"] == blocked["index"]):
                    self.logMsg("Item Blocked", level=1)
                    return True
        return False
           
    def findNextLink(self, linkList, blackList, startIndex):
        currentIndex = startIndex
        
        isBlacklisted = self.isBlackListed(blackList, linkList[currentIndex])
        
        while(isBlacklisted):
        
            currentIndex = currentIndex + 1
            
            if(currentIndex == len(linkList)):
                currentIndex = 0 # loop back to beginning
            if(currentIndex == startIndex):
                return (currentIndex+1, linkList[currentIndex]["url"]) # we checked everything and nothing was ok so return the first one again                

            isBlacklisted = self.isBlackListed(blackList, linkList[currentIndex])
             
        return (currentIndex+1, linkList[currentIndex]["url"])
    
    def updateArtLinks(self):
        self.logMsg("updateArtLinks Called")
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')     
        
        userUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users?format=json"
        
        try:
            requesthandle = urllib.urlopen(userUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateArtLinks urlopen : " + str(e) + " (" + userUrl + ")", level=0)
            return        
        
        userid = ""
        result = json.loads(jsonData)
        for user in result:
            if(user.get("Name") == userName):
                userid = user.get("Id")    
                break
        
        self.logMsg("updateArtLinks UserID : " + userid)
        
        moviesUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Recursive=true&IncludeItemTypes=Movie&format=json"

        try:
            requesthandle = urllib2.urlopen(moviesUrl, timeout=60)
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateArtLinks urlopen : " + str(e) + " (" + moviesUrl + ")", level=0)
            return          
        
        result = json.loads(jsonData)
        
        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            name = item.get("Name")
            if (images == None):
                images = []
            index = 0
            for backdrop in images:
              
              info = {}
              info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
              info["index"] = index
              info["parent"] = id
              info["name"] = name
              self.logMsg("BG Movie Image Info : " + str(info), level=2)
              
              if (info not in self.movie_art_links):
                  self.movie_art_links.append(info)
              index = index + 1
        
        random.shuffle(self.movie_art_links)
        self.logMsg("Background Movie Art Links : " + str(len(self.movie_art_links)))
        
        tvUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Recursive=true&IncludeItemTypes=Series&format=json"

        try:
            requesthandle = urllib2.urlopen(tvUrl, timeout=60)
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateArtLinks urlopen : " + str(e) + " (" + tvUrl + ")", level=2)
            return          
        
        result = json.loads(jsonData)        
        
        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            name = item.get("Name")
            if (images == None):
                images = []
            index = 0
            for backdrop in images:
              
              info = {}
              info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
              info["index"] = index
              info["parent"] = id
              info["name"] = name
              self.logMsg("BG TV Image Info : " + str(info), level=2)
              
              if (info not in self.tv_art_links):
                  self.tv_art_links.append(info)    
              index = index + 1
              
        random.shuffle(self.tv_art_links)
        self.logMsg("Background Tv Art Links : " + str(len(self.tv_art_links)))

        musicUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Recursive=true&IncludeItemTypes=MusicArtist&format=json"
        
        try:
            requesthandle = urllib2.urlopen(musicUrl, timeout=60)
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateArtLinks urlopen : " + str(e) + " (" + musicUrl + ")", level=0)
            return           
        
        result = json.loads(jsonData)        
        
        result = result.get("Items")
        if(result == None):
            result = []   

        for item in result:
            images = item.get("BackdropImageTags")
            id = item.get("Id")
            name = item.get("Name")
            if (images == None):
                images = []
            index = 0
            for backdrop in images:
              
              info = {}
              info["url"] = "http://localhost:15001/?id=" + str(id) + "&type=Backdrop" + "&index=" + str(index) + "&tag=" + backdrop
              info["index"] = index
              info["parent"] = id
              info["name"] = name
              self.logMsg("BG Music Image Info : " + str(info), level=2)

              if (info not in self.music_art_links):
                  self.music_art_links.append(info)
              index = index + 1

        random.shuffle(self.music_art_links)
        self.logMsg("Background Music Art Links : " + str(len(self.music_art_links)))

        self.global_art_links.extend(self.movie_art_links)
        self.global_art_links.extend(self.tv_art_links)
        self.global_art_links.extend(self.music_art_links)
        random.shuffle(self.global_art_links)
        
        self.logMsg("Background Global Art Links : " + str(len(self.global_art_links)))
        self.linksLoaded = True
        
 