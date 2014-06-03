#################################################################################################
# Random Info Updater
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
import urllib

_MODE_BASICPLAY=12

class RandomInfoUpdaterThread(threading.Thread):

    logLevel = 0
    
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')        
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)           
    
        xbmc.log("XBMB3C RandomInfoUpdaterThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)    
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C RandomInfoUpdaterThread -> " + msg)
            
    def getImageLink(self, item, type, item_id):
        imageTag = "none"
        if(item.get("ImageTags") != None and item.get("ImageTags").get(type) != None):
            imageTag = item.get("ImageTags").get(type)            
        return "http://localhost:15001/?id=" + str(item_id) + "&type=" + type + "&tag=" + imageTag                
    
    def run(self):
        self.logMsg("Started")
        
        self.updateRandom()
        lastRun = datetime.today()
        
        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            secTotal = td.seconds
            
            if(secTotal > 300):
                self.updateRandom()
                lastRun = datetime.today()

            xbmc.sleep(3000)
                        
        self.logMsg("Exited")
        
    def updateRandom(self):
        self.logMsg("updateRandomMovies Called")
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')     
        
        userUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users?format=json"
        self.logMsg("userUrl : " + userUrl, level=2)
        
        try:
            requesthandle = urllib.urlopen(userUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()      
        except Exception, e:
            self.logMsg("urlopen : " + str(e) + " (" + userUrl + ")", level=1)
            return           
        
        self.logMsg("jsonData : " + jsonData, level=2)
        
        result = []
        
        try:
            result = json.loads(jsonData)
        except Exception, e:
            self.logMsg("jsonload : " + str(e) + " (" + jsonData + ")", level=2)
            return              
        
        userid = ""
        for user in result:
            if(user.get("Name") == userName):
                userid = user.get("Id")    
                break
        
        self.logMsg("updateRandomMovies UserID : " + userid)
        
        self.logMsg("Updating Random Movie List")
        
        randomUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Limit=10&Recursive=true&SortBy=Random&Fields=Path,Genres,MediaStreams,Overview,CriticRatingSummary&SortOrder=Descending&Filters=IsUnplayed,IsNotFolder&IncludeItemTypes=Movie&format=json"
        
        try:
            requesthandle = urllib.urlopen(randomUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()     
        except Exception, e:
            self.logMsg("updateRandom urlopen : " + str(e) + " (" + randomUrl + ")", level=0)
            return           

        result = json.loads(jsonData)
        self.logMsg("Random Movie Json Data : " + str(result), level=2)
        
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

            item_id = item.get("Id")
            thumbnail = self.getImageLink(item, "Primary",str(item_id))
            logo = self.getImageLink(item, "Logo",str(item_id))
            fanart = self.getImageLink(item, "Backdrop",str(item_id))
            
            url =  mb3Host + ":" + mb3Port + ',;' + item_id
            playUrl = "plugin://plugin.video.xbmb3c/?url=" + url + '&mode=' + str(_MODE_BASICPLAY)
            playUrl = playUrl.replace("\\\\","smb://")
            playUrl = playUrl.replace("\\","/")    

            self.logMsg("RandomMovieMB3." + str(item_count) + ".Title = " + title, level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".Thumb = " + thumbnail, level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".Path  = " + playUrl, level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".Art(fanart)  = " + fanart, level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".Art(clearlogo)  = " + logo, level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".Art(poster)  = " + thumbnail, level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".Rating  = " + str(rating), level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".CriticRating  = " + str(criticrating), level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".CriticRatingSummary  = " + criticratingsummary, level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".Plot  = " + plot, level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".Year  = " + str(year), level=2)
            self.logMsg("RandomMovieMB3." + str(item_count) + ".Runtime  = " + str(runtime), level=2)
            
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".Title", title)
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".Thumb", thumbnail)
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".Path", playUrl)
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".Art(fanart)", fanart)
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".Art(clearlogo)", logo)
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".Art(poster)", thumbnail)
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".Rating", str(rating))
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".CriticRating", str(criticrating))
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".CriticRatingSummary", criticratingsummary)
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".Plot", plot)
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".Year", str(year))
            WINDOW.setProperty("RandomMovieMB3." + str(item_count) + ".Runtime", str(runtime))
            
            WINDOW.setProperty("RandomMovieMB3.Enabled", "true")
            
            item_count = item_count + 1
        
        self.logMsg("Updating Random TV Show List")
        
        randomUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Limit=10&Recursive=true&SortBy=Random&Fields=Path,Genres,MediaStreams,Overview&SortOrder=Descending&Filters=IsUnplayed,IsNotFolder&IsVirtualUnaired=false&IsMissing=False&IncludeItemTypes=Episode&format=json"
        
        try:
            requesthandle = urllib.urlopen(randomUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()         
        except Exception, e:
            self.logMsg("updateRandom urlopen : " + str(e) + " (" + randomUrl + ")", level=0)
            return          
        
        result = json.loads(jsonData)
        self.logMsg("Random TV Show Json Data : " + str(result), level=2)
        
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
            tempEpisodeNumber = ""
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

            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".EpisodeTitle = " + title, level=2)
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".ShowTitle = " + seriesName, level=2)
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".EpisodeNo = " + tempEpisodeNumber, level=2)
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".SeasonNo = " + tempSeasonNumber, level=2)
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".Thumb = " + thumbnail, level=2)
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".Path  = " + playUrl, level=2)
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".Rating  = " + rating, level=2)
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".Art(tvshow.fanart)  = " + fanart, level=2)
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".Art(tvshow.clearlogo)  = " + logo, level=2)
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".Art(tvshow.banner)  = " + banner, level=2)  
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".Art(tvshow.poster)  = " + poster, level=2)
            self.logMsg("RandomEpisodeMB3." + str(item_count) + ".Plot  = " + plot, level=2)
            
            
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".EpisodeTitle", title)
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".ShowTitle", seriesName)
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".EpisodeNo", tempEpisodeNumber)
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".SeasonNo", tempSeasonNumber)
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".Thumb", thumbnail)
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".Path", playUrl)            
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".Rating", rating)
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".Art(tvshow.fanart)", fanart)
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".Art(tvshow.clearlogo)", logo)
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".Art(tvshow.banner)", banner)
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".Art(tvshow.poster)", poster)
            WINDOW.setProperty("RandomEpisodeMB3." + str(item_count) + ".Plot", plot)
            
            WINDOW.setProperty("RandomEpisodeMB3.Enabled", "true")
            
            item_count = item_count + 1
            
        # update random music
        self.logMsg("Updating Random MusicList")
    
        randomUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Limit=10&Recursive=true&SortBy=Random&Fields=Path,Genres,MediaStreams,Overview&SortOrder=Descending&Filters=IsUnplayed,IsFolder&IsVirtualUnaired=false&IsMissing=False&IncludeItemTypes=MusicAlbum&format=json"
    
        try:
            requesthandle = urllib.urlopen(randomUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()     
        except Exception, e:
            self.logMsg("updateRandom urlopen : " + str(e) + " (" + randomUrl + ")", level=2)
            return  
    
        result = json.loads(jsonData)
        self.logMsg("Random MusicList Json Data : " + str(result), level=2)
    
        result = result.get("Items")
        if(result == None):
          result = []   

        item_count = 1
        for item in result:
            title = "Missing Title"
            if(item.get("Name") != None):
                title = item.get("Name").encode('utf-8')
                
            artist = "Missing Artist"
            if(item.get("AlbumArtist") != None):
                artist = item.get("AlbumArtist").encode('utf-8')   

            year = "0000"
            if(item.get("ProductionYear") != None):
              year = str(item.get("ProductionYear"))
            plot = "Missing Plot"
            if(item.get("Overview") != None):
              plot = item.get("Overview").encode('utf-8')

            item_id = item.get("Id")
           
            if item.get("Type") == "MusicAlbum":
               parentId = item.get("ParentLogoItemId")
            
            thumbnail = self.getImageLink(item, "Primary", str(item_id))
            logo = self.getImageLink(item, "Logo", str(parentId))
            fanart = self.getImageLink(item, "Backdrop", str(parentId))
            banner = self.getImageLink(item, "Banner", str(parentId))
            
            url =  mb3Host + ":" + mb3Port + ',;' + item_id
            playUrl = "plugin://plugin.video.xbmb3c/?url=" + url + '&mode=' + str(_MODE_BASICPLAY)
            playUrl = playUrl.replace("\\\\","smb://")
            playUrl = playUrl.replace("\\","/")    

            self.logMsg("RandomAlbumMB3." + str(item_count) + ".Title = " + title, level=2)
            self.logMsg("RandomAlbumMB3." + str(item_count) + ".Artist = " + artist, level=2)
            self.logMsg("RandomAlbumMB3." + str(item_count) + ".Year = " + year, level=2)
            self.logMsg("RandomAlbumMB3." + str(item_count) + ".Thumb = " + thumbnail, level=2)
            self.logMsg("RandomAlbumMB3." + str(item_count) + ".Path  = " + playUrl, level=2)
            self.logMsg("RandomAlbumMB3." + str(item_count) + ".Art(fanart)  = " + fanart, level=2)
            self.logMsg("RandomAlbumMB3." + str(item_count) + ".Art(clearlogo)  = " + logo, level=2)
            self.logMsg("RandomAlbumMB3." + str(item_count) + ".Art(banner)  = " + banner, level=2)  
            self.logMsg("RandomAlbumMB3." + str(item_count) + ".Art(poster)  = " + thumbnail, level=2)
            self.logMsg("RandomAlbumMB3." + str(item_count) + ".Plot  = " + plot, level=2)
            
            
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Title", title)
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Artist", artist)
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Year", year)
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Thumb", thumbnail)
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Path", playUrl)            
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Rating", rating)
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Art(fanart)", fanart)
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Art(clearlogo)", logo)
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Art(banner)", banner)
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Art(poster)", thumbnail)
            WINDOW.setProperty("RandomAlbumMB3." + str(item_count) + ".Plot", plot)
            
            WINDOW.setProperty("RandomAlbumMB3.Enabled", "true")
            
            item_count = item_count + 1
        
        
        