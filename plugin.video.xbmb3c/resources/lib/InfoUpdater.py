#################################################################################################
# Info Updater
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
import urllib

_MODE_BASICPLAY=12

class InfoUpdaterThread(threading.Thread):

    logLevel = 0
    
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')        
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)           
    
        xbmc.log("XBMB3C InfoUpdaterThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)    
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C InfoUpdaterThread -> " + msg)
    
    def run(self):
        self.logMsg("Started")
        
        self.updateInfo()
        lastRun = datetime.today()
        
        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            secTotal = td.seconds
            
            if(secTotal > 300):
                self.updateInfo()
                lastRun = datetime.today()

            xbmc.sleep(3000)
                        
        self.logMsg("Exited")
        
    def updateInfo(self):
        self.logMsg("updateInfo Called")
        
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
            self.logMsg("updateInfo urlopen : " + str(e) + " (" + userUrl + ")", level=0)
            return          
        
        userid = ""
        result = json.loads(jsonData)
        for user in result:
            if(user.get("Name") == userName):
                userid = user.get("Id")    
                break
        
        self.logMsg("updateInfo UserID : " + userid)
        
        self.logMsg("Updating info List")
        
        infoUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Fields=CollectionType&format=json"
        
        try:
            requesthandle = urllib.urlopen(infoUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()      
        except Exception, e:
            self.logMsg("updateInfo urlopen : " + str(e) + " (" + infoUrl + ")", level=0)
            return  
        
        result = json.loads(jsonData)
        
        result = result.get("Items")
        WINDOW = xbmcgui.Window( 10000 )
        if(result == None):
            result = []   

        item_count = 1
        movie_count = 0
        movie_unwatched_count = 0
        tv_count = 0
        episode_count = 0
        episode_unwatched_count = 0
        tv_unwatched_count = 0
        music_count = 0
        music_songs_count = 0
        music_songs_unplayed_count = 0
        musicvideos_count = 0
        musicvideos_unwatched_count = 0
        trailers_count = 0
        trailers_unwatched_count = 0
        photos_count = 0
        for item in result:
            collectionType = item.get("CollectionType")
            if collectionType==None:
                collectionType="unknown"
            self.logMsg("collectionType "  + collectionType)    
            if(collectionType == "movies"):
                movie_count = movie_count + item.get("RecursiveItemCount")
                movie_unwatched_count = movie_unwatched_count + item.get("RecursiveUnplayedItemCount")
                
            if(collectionType == "musicvideos"):
                musicvideos_count = musicvideos_count + item.get("RecursiveItemCount")
                musicvideos_unwatched_count = musicvideos_unwatched_count + item.get("RecursiveUnplayedItemCount")
            
            if(collectionType == "tvshows"):
                tv_count = tv_count + item.get("ChildCount")
                episode_count = episode_count + item.get("RecursiveItemCount")
                episode_unwatched_count = episode_unwatched_count + item.get("RecursiveUnplayedItemCount")
            
            if(collectionType == "music"):
                music_count = music_count + item.get("ChildCount")
                music_songs_count = music_songs_count + item.get("RecursiveItemCount")
                music_songs_unplayed_count = music_songs_unplayed_count + item.get("RecursiveUnplayedItemCount")
             
            if(collectionType == "photos"):
                photos_count = photos_count + item.get("RecursiveItemCount")
                     
            if(item.get("Name") == "Trailers"):
                trailers_count = trailers_count + item.get("RecursiveItemCount")
                trailers_unwatched_count = trailers_unwatched_count + item.get("RecursiveUnplayedItemCount")
               
        self.logMsg("MoviesCount "  + str(movie_count), level=2)
        self.logMsg("MoviesUnWatchedCount "  + str(movie_unwatched_count), level=2)
        self.logMsg("MusicVideosCount "  + str(musicvideos_count), level=2)
        self.logMsg("MusicVideosUnWatchedCount "  + str(musicvideos_unwatched_count), level=2)
        self.logMsg("TVCount "  + str(tv_count), level=2)
        self.logMsg("EpisodeCount "  + str(episode_count), level=2)
        self.logMsg("EpisodeUnWatchedCount "  + str(episode_unwatched_count), level=2)
        self.logMsg("MusicCount "  + str(music_count), level=2)
        self.logMsg("SongsCount "  + str(music_songs_count), level=2)
        self.logMsg("SongsUnPlayedCount "  + str(music_songs_unplayed_count), level=2)
        self.logMsg("TrailersCount" + str(trailers_count), level=2)
        self.logMsg("TrailersUnWatchedCount" + str(trailers_unwatched_count), level=2)
        self.logMsg("PhotosCount" + str(photos_count), level=2)
    
            #item_count = item_count + 1
        
        movie_watched_count = movie_count - movie_unwatched_count
        musicvideos_watched_count = musicvideos_count - musicvideos_unwatched_count
        episode_watched_count = episode_count - episode_unwatched_count
        music_songs_played_count = music_songs_count - music_songs_unplayed_count
        trailers_watched_count = trailers_count - trailers_unwatched_count    
        WINDOW.setProperty("MB3TotalMovies", str(movie_count))
        WINDOW.setProperty("MB3TotalUnWatchedMovies", str(movie_unwatched_count))
        WINDOW.setProperty("MB3TotalWatchedMovies", str(movie_watched_count))
        WINDOW.setProperty("MB3TotalMusicVideos", str(musicvideos_count))
        WINDOW.setProperty("MB3TotalUnWatchedMusicVideos", str(musicvideos_unwatched_count))
        WINDOW.setProperty("MB3TotalWatchedMusicVideos", str(musicvideos_watched_count))
        WINDOW.setProperty("MB3TotalTvShows", str(tv_count))
        WINDOW.setProperty("MB3TotalEpisodes", str(episode_count))
        WINDOW.setProperty("MB3TotalUnWatchedEpisodes", str(episode_unwatched_count))
        WINDOW.setProperty("MB3TotalWatchedEpisodes", str(episode_watched_count))
        WINDOW.setProperty("MB3TotalMusicAlbums", str(music_count))
        WINDOW.setProperty("MB3TotalMusicSongs", str(music_songs_count))
        WINDOW.setProperty("MB3TotalUnPlayedMusicSongs", str(music_songs_unplayed_count))
        WINDOW.setProperty("MB3TotalPlayedMusicSongs", str(music_songs_played_count))
        WINDOW.setProperty("MB3TotalTrailers", str(trailers_count))
        WINDOW.setProperty("MB3TotalUnWatchedTrailers", str(trailers_unwatched_count))
        WINDOW.setProperty("MB3TotalWatchedTrailers", str(trailers_watched_count))
        WINDOW.setProperty("MB3TotalPhotos", str(photos_count))

        self.logMsg("InfoTV start")
        infoTVUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?&IncludeItemTypes=Series&Recursive=true&SeriesStatus=Continuing&format=json"
        
        try:
            requesthandle = urllib.urlopen(infoTVUrl, proxies={})
            self.logMsg("InfoTV start open")
            jsonData = requesthandle.read()
            requesthandle.close()  
        except Exception, e:
            self.logMsg("updateInfo urlopen : " + str(e) + " (" + infoTVUrl + ")", level=0)
            return  
        
        result = json.loads(jsonData)
        self.logMsg("InfoTV Json Data : " + str(result), level=2)
        
        totalRunning = result.get("TotalRecordCount")
        self.logMsg("TotalRunningCount "  + str(totalRunning))
        WINDOW.setProperty("MB3TotalRunningTvShows", str(totalRunning))
        
        self.logMsg("InfoNextAired start")
        InfoNextAiredUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?IsUnaired=true&SortBy=PremiereDate%2CAirTime%2CSortName&SortOrder=Ascending&IncludeItemTypes=Episode&Limit=1&Recursive=true&Fields=SeriesInfo%2CUserData&format=json"
        
        try:
            requesthandle = urllib.urlopen(InfoNextAiredUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateInfo urlopen : " + str(e) + " (" + InfoNextAiredUrl + ")", level=0)
            return  
        
        result = json.loads(jsonData)
        self.logMsg("InfoNextAired Json Data : " + str(result), level=2)
        
        result = result.get("Items")
        if(result == None):
            result = []
        
        episode = ""
        for item in result:
            title = ""
            seriesName = ""
            if(item.get("SeriesName") != None):
                seriesName = item.get("SeriesName").encode('utf-8')
            
            if(item.get("Name") != None):
                title = item.get("Name").encode('utf-8')
                
            eppNumber = ""
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
               
            episode = seriesName + " - " + title + " - S" + tempSeasonNumber + "E" + tempEpisodeNumber
        
        self.logMsg("MB3NextAiredEpisode"  + episode)
        WINDOW.setProperty("MB3NextAiredEpisode", episode)
        self.logMsg("InfoNextAired end")
        
        today = datetime.today()    
        dateformat = today.strftime("%Y-%m-%d") 
        nextAiredUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?IsUnaired=true&SortBy=PremiereDate%2CAirTime%2CSortName&SortOrder=Ascending&IncludeItemTypes=Episode&Recursive=true&Fields=SeriesInfo%2CUserData&MinPremiereDate="  + str(dateformat) + "&MaxPremiereDate=" + str(dateformat) + "&format=json"
        
        try:
            requesthandle = urllib.urlopen(nextAiredUrl, proxies={})
            jsonData = requesthandle.read()
            requesthandle.close()   
        except Exception, e:
            self.logMsg("updateInfo total urlopen : " + str(e) + " (" + nextAiredUrl + ")", level=0)
            return  
        
        result = json.loads(jsonData)
        self.logMsg("InfoNextAired total url: " + nextAiredUrl)
        self.logMsg("InfoNextAired total Json Data : " + str(result), level=2)
        
        totalToday = result.get("TotalRecordCount")
        self.logMsg("MB3NextAiredTotalToday "  + str(totalToday))
        WINDOW.setProperty("MB3NextAiredTotalToday", str(totalToday))  
        
