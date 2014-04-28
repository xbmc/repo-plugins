#################################################################################################
# In Progress Updater
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
import urllib

_MODE_BASICPLAY=12

class InProgressUpdaterThread(threading.Thread):

    logLevel = 0
    
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')        
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)           
    
        xbmc.log("XBMB3C InProgressUpdaterThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)
        
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C InProgressUpdaterThread -> " + msg)
    
    def getImageLink(self, item, type, item_id):
        imageTag = "none"
        if(item.get("ImageTags") != None and item.get("ImageTags").get(type) != None):
            imageTag = item.get("ImageTags").get(type)            
        return "http://localhost:15001/?id=" + str(item_id) + "&type=" + type + "&tag=" + imageTag        
    
    def run(self):
        self.logMsg("Started")
        
        self.updateInProgress()
        lastRun = datetime.today()

        updateInterval = 300
        
        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            secTotal = td.seconds
            
            if(secTotal > updateInterval):
                self.updateInProgress()
                lastRun = datetime.today()
            
            xbmc.sleep(3000)
                        
        self.logMsg("Exited")
        
    def updateInProgress(self):
        self.logMsg("updateInProgress Called")
        
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
            self.logMsg("updateRecent urlopen : " + str(e) + " (" + userUrl + ")", level=0)
            return

        userid = ""
        result = json.loads(jsonData)
        for user in result:
            if(user.get("Name") == userName):
                userid = user.get("Id")
                break
        
        self.logMsg("InProgress UserName : " + userName + " UserID : " + userid)
        
        self.logMsg("Updating In Progress Movie List")
        
        recentUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Limit=10&Recursive=true&SortBy=DatePlayed&SortOrder=Descending&Fields=Path,Genres,MediaStreams,Overview,CriticRatingSummary&Filters=IsResumable&IncludeItemTypes=Movie&format=json"

        try:
            requesthandle = urllib.urlopen(recentUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()              
        except Exception, e:
            self.logMsg("updateRecent urlopen : " + str(e) + " (" + recentUrl + ")", level=0)
            return    

        result = json.loads(jsonData)
        result = result.get("Items")
        if(result == None):
            result = []
            
        WINDOW = xbmcgui.Window( 10000 )

        item_count = 1
        for item in result:
            title = "Missing Title"
            if(item.get("Name") != None):
                title = item.get("Name").encode('utf-8')
            
            rating = item.get("CommunityRating")
            criticrating = item.get("CriticRating")
            criticratingsummary = ""
            if(item.get("CriticRatingSummary") != None):
                criticratingsummary = item.get("CriticRatingSummary").encode('utf-8')
            plot = item.get("Overview")
            if plot == None:
                plot=''
            plot=plot.encode('utf-8')
            year = item.get("ProductionYear")
            if(item.get("RunTimeTicks") != None):
                runtime = str(int(item.get("RunTimeTicks"))/(10000000*60))
            else:
                runtime = "0"

            userData = item.get("UserData")
            if(userData != None):                
                reasonableTicks = int(userData.get("PlaybackPositionTicks")) / 1000
                seekTime = reasonableTicks / 10000
                duration = float(runtime)
                resume = float(seekTime) / 60.0
                if (duration == 0):
                    percentage=0
                else:
                    percentage = (resume / duration) * 100.0
                perasint = int(percentage)
                title = str(perasint) + "% " + title        
                
            item_id = item.get("Id")
            thumbnail = self.getImageLink(item, "Primary", str(item_id))
            logo = self.getImageLink(item, "Logo", str(item_id))
            fanart = self.getImageLink(item, "Backdrop", str(item_id))
            
            url =  mb3Host + ":" + mb3Port + ',;' + item_id
            playUrl = "plugin://plugin.video.xbmb3c/?url=" + url + '&mode=' + str(_MODE_BASICPLAY)
            playUrl = playUrl.replace("\\\\","smb://")
            playUrl = playUrl.replace("\\","/")    

            self.logMsg("InProgressMovieMB3." + str(item_count) + ".Title = " + title, level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".Thumb = " + thumbnail, level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".Path  = " + playUrl, level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".Art(fanart)  = " + fanart, level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".Art(clearlogo)  = " + logo, level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".Art(poster)  = " + thumbnail, level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".Rating  = " + str(rating), level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".CriticRating  = " + str(criticrating), level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".CriticRatingSummary  = " + criticratingsummary, level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".Plot  = " + plot, level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".Year  = " + str(year), level=2)
            self.logMsg("InProgressMovieMB3." + str(item_count) + ".Runtime  = " + str(runtime), level=2)
            
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".Title", title)
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".Thumb", thumbnail)
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".Path", playUrl)
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".Art(fanart)", fanart)
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".Art(clearlogo)", logo)
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".Art(poster)", thumbnail)
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".Rating", str(rating))
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".CriticRating", str(criticrating))
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".CriticRatingSummary", criticratingsummary)
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".Plot", plot)
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".Year", str(year))
            WINDOW.setProperty("InProgressMovieMB3." + str(item_count) + ".Runtime", str(runtime))
            
            item_count = item_count + 1
        
        # blank any not available
        for x in range(item_count, 11):
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".Title", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".Thumb", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".Path", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".Art(fanart)", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".Art(clearlogo)", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".Art(poster)", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".Rating", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".CriticRating", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".CriticRatingSummary", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".Plot", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".Year", "")
            WINDOW.setProperty("InProgressMovieMB3." + str(x) + ".Runtime", "")
        
        
        #Updating Recent TV Show List
        self.logMsg("Updating In Progress Episode List")
        
        recentUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Limit=10&Recursive=true&SortBy=DatePlayed&SortOrder=Descending&Fields=Path,Genres,MediaStreams,Overview,CriticRatingSummary&Filters=IsResumable&IncludeItemTypes=Episode&format=json"
        
        try:
            requesthandle = urllib.urlopen(recentUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()               
        except Exception, e:
            self.logMsg("updateRecent urlopen : " + str(e) + " (" + recentUrl + ")", level=0)
            return

        result = json.loads(jsonData)
        
        result = result.get("Items")
        if(result == None):
            result = []   

        item_count = 1
        for item in result:
            title = "Missing Title"
            if(item.get("Name") != None):
                title = item.get("Name").encode('utf-8')
                
            seriesName = "Missing Name"
            if(item.get("SeriesName") != None):
                seriesName = item.get("SeriesName").encode('utf-8')   

            eppNumber = "X"
            tempEpisodeNumber = "00"
            if(item.get("IndexNumber") != None):
                eppNumber = item.get("IndexNumber")
                if eppNumber < 10:
                  tempEpisodeNumber = "0" + str(eppNumber)
                else:
                  tempEpisodeNumber = str(eppNumber)
            
            seasonNumber = item.get("ParentIndexNumber")
            if seasonNumber < 10:
              tempSeasonNumber = "0" + str(seasonNumber)
            else:
              tempSeasonNumber = str(seasonNumber)
            rating = str(item.get("CommunityRating"))
            plot = item.get("Overview")
            if plot == None:
                plot=''
            plot=plot.encode('utf-8')
            
            if(item.get("RunTimeTicks") != None):
                runtime = str(int(item.get("RunTimeTicks"))/(10000000*60))
            else:
                runtime = "0"            
            
            userData = item.get("UserData")
            if(userData != None):                
                reasonableTicks = int(userData.get("PlaybackPositionTicks")) / 1000
                seekTime = reasonableTicks / 10000
                duration = float(runtime)
                resume = float(seekTime) / 60.0
                if (duration == 0):
                    percentage=0
                else:
                    percentage = (resume / duration) * 100.0
                perasint = int(percentage)
                title = str(perasint) + "% " + title               

            item_id = item.get("Id")
           
            if item.get("Type") == "Episode" or item.get("Type") == "Season":
               series_id = item.get("SeriesId")
            
            poster = self.getImageLink(item, "Primary", str(series_id))
            thumbnail = self.getImageLink(item, "Primary", str(item_id))         
            logo = self.getImageLink(item, "Logo", str(series_id))             
            fanart = self.getImageLink(item, "Backdrop", str(series_id))
            banner = self.getImageLink(item, "Banner", str(series_id))
            
            url =  mb3Host + ":" + mb3Port + ',;' + item_id
            playUrl = "plugin://plugin.video.xbmb3c/?url=" + url + '&mode=' + str(_MODE_BASICPLAY)
            playUrl = playUrl.replace("\\\\","smb://")
            playUrl = playUrl.replace("\\","/")    

            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".EpisodeTitle = " + title, level=2)
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".ShowTitle = " + seriesName, level=2)
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".EpisodeNo = " + tempEpisodeNumber, level=2)
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".SeasonNo = " + tempSeasonNumber, level=2)
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".Thumb = " + thumbnail, level=2)
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".Path  = " + playUrl, level=2)
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".Rating  = " + rating, level=2)
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".Art(tvshow.fanart)  = " + fanart, level=2)
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".Art(tvshow.clearlogo)  = " + logo, level=2)
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".Art(tvshow.banner)  = " + banner, level=2)  
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".Art(tvshow.poster)  = " + poster, level=2)
            self.logMsg("InProgresstEpisodeMB3." + str(item_count) + ".Plot  = " + plot, level=2)
            
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".EpisodeTitle", title)
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".ShowTitle", seriesName)
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".EpisodeNo", tempEpisodeNumber)
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".SeasonNo", tempSeasonNumber)
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".Thumb", thumbnail)
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".Path", playUrl)            
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".Rating", rating)
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".Art(tvshow.fanart)", fanart)
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".Art(tvshow.clearlogo)", logo)
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".Art(tvshow.banner)", banner)
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".Art(tvshow.poster)", poster)
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(item_count) + ".Plot", plot)
            
            item_count = item_count + 1
            
        # blank any not available
        for x in range(item_count, 11):            
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".EpisodeTitle", "")
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".ShowTitle", "")
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".EpisodeNo", "")
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".SeasonNo", "")
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".Thumb", "")
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".Path", "")            
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".Rating", "")
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".Art(tvshow.fanart)", "")
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".Art(tvshow.clearlogo)", "")
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".Art(tvshow.banner)", "")
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".Art(tvshow.poster)", "")
            WINDOW.setProperty("InProgresstEpisodeMB3." + str(x) + ".Plot", "")        
        
        
        