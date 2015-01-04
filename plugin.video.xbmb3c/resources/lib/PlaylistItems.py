#################################################################################################
# Playlist items
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
import urllib
from DownloadUtils import DownloadUtils

_MODE_BASICPLAY=12
_MODE_ITEM_DETAILS=17

#define our global download utils
downloadUtils = DownloadUtils()

class PlaylistItemUpdaterThread(threading.Thread):

    logLevel = 0
    
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')        
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)           
    
        xbmc.log("XBMB3C PlaylistItemUpdaterThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)
        
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C PlaylistItemUpdaterThread -> " + msg)
        
    def run(self):
        self.logMsg("Started")
        
        self.updatePlaylistItems()
        lastRun = datetime.today()

        updateInterval = 300
        
        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            secTotal = td.seconds
            
            if(secTotal > updateInterval and not xbmc.Player().isPlaying()):
                self.updatePlaylistItems()
                lastRun = datetime.today()
            
            xbmc.sleep(3000)
                        
        self.logMsg("Exited")
        
    def updatePlaylistItems(self):
        self.logMsg("updatePlaylistItems Called")
        
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')     
        
        userid = downloadUtils.getUserId()  
       
        playlistsUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?&SortBy=SortName&Fields=Path,Genres,MediaStreams,Overview,ShortOverview,CriticRatingSummary&Recursive=true&SortOrder=Ascending&IncludeItemTypes=Playlist&mediatype=video&format=json"
   
        jsonData = downloadUtils.downloadUrl(playlistsUrl, suppress=False, popup=1 )
        result = json.loads(jsonData)
        result = result.get("Items")
        if(result == None):
            result = []
            
        WINDOW = xbmcgui.Window( 10000 )

        playlist_count = 1
        for item in result:
            title = "Missing Title"
            if(item.get("Name") != None):
                title = item.get("Name").encode('utf-8')
            item_id = item.get("Id")
            
            self.logMsg("PlaylistMB3." + str(playlist_count) + ".Title = " + title, level=2)
            WINDOW.setProperty("PlaylistMB3." + str(playlist_count) + ".Title", title)
            
            playlistUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Playlists/" + item_id + "/Items/?Fields=Path,Genres,MediaStreams,Overview,ShortOverview,CriticRatingSummary&format=json"
            jsonData = downloadUtils.downloadUrl(playlistUrl, suppress=False, popup=1 )
            result = json.loads(jsonData)
            result = result.get("Items")
            if(result == None):
                result = []
            playlist_item_count = 1    
            for item in result:
                id = item.get("Id")
                if (item.get("Type")=="Movie"):
                    title = "Missing Title"
                    if(item.get("Name") != None):
                        title = item.get("Name").encode('utf-8')
                    
                    rating = item.get("CommunityRating")
                    criticrating = item.get("CriticRating")
                    officialrating = item.get("OfficialRating")
                    criticratingsummary = ""
                    if(item.get("CriticRatingSummary") != None):
                        criticratingsummary = item.get("CriticRatingSummary").encode('utf-8')
                    plot = item.get("Overview")
                    if plot == None:
                        plot=''
                    plot=plot.encode('utf-8')
                    shortplot = item.get("ShortOverview")
                    if shortplot == None:
                        shortplot = ''
                    shortplot = shortplot.encode('utf-8')
                    year = item.get("ProductionYear")
                    if(item.get("RunTimeTicks") != None):
                        runtime = str(int(item.get("RunTimeTicks"))/(10000000*60))
                    else:
                        runtime = "0"
        
                    item_id = item.get("Id")
                    
                    thumbnail = downloadUtils.getArtwork(item, "Primary")
                    logo = downloadUtils.getArtwork(item, "Logo")
                    fanart = downloadUtils.getArtwork(item, "Backdrop")
                    medium_fanart = downloadUtils.getArtwork(item, "Backdrop3")
                    
                    if (item.get("ImageTags") != None and item.get("ImageTags").get("Thumb") != None):
                      realthumb = downloadUtils.getArtwork(item, "Thumb3")
                    else:
                      realthumb = fanart
                    
                    url =  mb3Host + ":" + mb3Port + ',;' + item_id
                    # play or show info
                    selectAction = addonSettings.getSetting('selectAction')
                    if(selectAction == "1"):
                      playUrl = "plugin://plugin.video.xbmb3c/?id=" + item_id + '&mode=' + str(_MODE_ITEM_DETAILS)
                    else:
                      playUrl = "plugin://plugin.video.xbmb3c/?url=" + url + '&mode=' + str(_MODE_BASICPLAY)  
                    
                    playUrl = playUrl.replace("\\\\","smb://")
                    playUrl = playUrl.replace("\\","/")    
        
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Title = " + title, level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Thumb = " + thumbnail, level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Path  = " + playUrl, level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(fanart)  = " + fanart, level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(clearlogo)  = " + logo, level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(poster)  = " + thumbnail, level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Rating  = " + str(rating), level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".CriticRating  = " + str(criticrating), level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".CriticRatingSummary  = " + criticratingsummary, level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Plot  = " + plot, level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Year  = " + str(year), level=2)
                    self.logMsg("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Runtime  = " + str(runtime), level=2)
                    
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Title", title)
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Thumb", thumbnail)
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Path", playUrl)
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(fanart)", fanart)
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(medium_fanart)", medium_fanart)
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(clearlogo)", logo)
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(poster)", thumbnail)
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".RealThumb", realthumb)
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Rating", str(rating))
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Mpaa", str(officialrating))
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".CriticRating", str(criticrating))
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".CriticRatingSummary", criticratingsummary)
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Plot", plot)
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".ShortPlot", shortplot)
                    
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Year", str(year))
                    WINDOW.setProperty("PlaylistMovieItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Runtime", str(runtime))
                
                if (item.get("Type")=="Episode"):
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
                    shortplot = item.get("ShortOverview")
                    if shortplot == None:
                        shortplot = ''
                    shortplot = shortplot.encode('utf-8')
                    item_id = item.get("Id")
                   
                    seriesId = item.get("SeriesId")          
                    seriesJsonData = downloadUtils.downloadUrl("http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items/" + seriesId + "?format=json", suppress=False, popup=1 )
                    seriesResult = json.loads(seriesJsonData)      
                       
                    poster = downloadUtils.getArtwork(seriesResult, "Primary3")
                    thumbnail = downloadUtils.getArtwork(item, "Primary") 
                    logo = downloadUtils.getArtwork(seriesResult, "Logo")           
                    fanart = downloadUtils.getArtwork(item, "Backdrop")
                    medium_fanart = downloadUtils.getArtwork(seriesResult, "Backdrop3")
                    banner = downloadUtils.getArtwork(item, "Banner")
                    if item.get("SeriesThumbImageTag") != None:
                      seriesthumbnail = downloadUtils.getArtwork(item, "Thumb3")
                    else:
                      seriesthumbnail = fanart
                      
                    url =  mb3Host + ":" + mb3Port + ',;' + item_id
                    playUrl = "plugin://plugin.video.xbmb3c/?url=" + url + '&mode=' + str(_MODE_BASICPLAY)
                    playUrl = playUrl.replace("\\\\","smb://")
                    playUrl = playUrl.replace("\\","/")    
        
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".EpisodeTitle = " + title, level=2)
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".ShowTitle = " + seriesName, level=2)
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".EpisodeNo = " + tempEpisodeNumber, level=2)
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".SeasonNo = " + tempSeasonNumber, level=2)
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Thumb = " + thumbnail, level=2)
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Path  = " + playUrl, level=2)
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Rating  = " + rating, level=2)
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(tvshow.fanart)  = " + fanart, level=2)
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(tvshow.clearlogo)  = " + logo, level=2)
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(tvshow.banner)  = " + banner, level=2)  
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(tvshow.poster)  = " + poster, level=2)
                    self.logMsg("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Plot  = " + plot, level=2)
                    
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".EpisodeTitle", title)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".ShowTitle", seriesName)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".EpisodeNo", tempEpisodeNumber)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".SeasonNo", tempSeasonNumber)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Thumb", thumbnail)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".SeriesThumb", seriesthumbnail)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Path", playUrl)            
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Rating", rating)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(tvshow.fanart)", fanart)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(tvshow.medium_fanart)", medium_fanart)
                    
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(tvshow.clearlogo)", logo)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(tvshow.banner)", banner)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Art(tvshow.poster)", poster)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".Plot", plot)
                    WINDOW.setProperty("PlaylistEpisodeItemMB3." + str(playlist_count) + "." + str(playlist_item_count) + ".ShortPlot", shortplot)
                
                playlist_item_count = playlist_item_count + 1
                    
            playlist_count = playlist_count + 1
        
        
        
        