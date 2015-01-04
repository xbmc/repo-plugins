#################################################################################################
# Background Data Updater
#################################################################################################

import xbmc
import xbmcgui
import xbmcaddon

import json
import threading
from datetime import datetime
import urllib
from DownloadUtils import DownloadUtils
from Database import Database
from API import API

_MODE_BASICPLAY=12
__settings__ = xbmcaddon.Addon(id='plugin.video.xbmb3c')

#define our global download utils
downloadUtils = DownloadUtils()
db = Database()

class BackgroundDataUpdaterThread(threading.Thread):

    logLevel = 0
    
    def __init__(self, *args):
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        level = addonSettings.getSetting('logLevel')   
        self.logLevel = 0
        if(level != None):
            self.logLevel = int(level)
        if(self.logLevel == 2):
            self.LogCalls = True
        xbmc.log("XBMB3C BackgroundDataUpdaterThread -> Log Level:" +  str(self.logLevel))
        
        threading.Thread.__init__(self, *args)    
    
    def logMsg(self, msg, level = 1):
        if(self.logLevel >= level):
            xbmc.log("XBMB3C BackgroundDataUpdaterThread -> " + msg)
                
    def run(self):
        self.logMsg("Started")
        
        self.updateBackgroundData()
        lastRun = datetime.today()
        lastProfilePath = xbmc.translatePath('special://profile')
        
        while (xbmc.abortRequested == False):
            td = datetime.today() - lastRun
            secTotal = td.seconds
            
            profilePath = xbmc.translatePath('special://profile')
            
            updateInterval = 600
                
            if((secTotal > updateInterval or lastProfilePath != profilePath) and not xbmc.Player().isPlaying()):
                self.updateBackgroundData()
                lastRun = datetime.today()

            lastProfilePath = profilePath
            
            xbmc.sleep(30000)
                        
        self.logMsg("Exited")

    def updateItem(self, id):
        self.logMsg("updateItem Called")
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')     
        
        userid = downloadUtils.getUserId()
        
        self.logMsg("UserName : " + userName + " UserID : " + userid)        
        dataUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Recursive=true&Ids=" + id + "&Fields=Path,People,Genres,MediaStreams,Overview,ShortOverview,CriticRatingSummary,EpisodeCount,SeasonCount,Studios,CumulativeRunTimeTicks,Metascore,SeriesStudio,AirTime,DateCreated&SortOrder=Ascending&ExcludeLocationTypes=Virtual&IncludeItemTypes=Series,BoxSet,Movie&CollapseBoxSetItems=false&format=json"        
        jsonData = downloadUtils.downloadUrl(dataUrl, suppress=False, popup=1 )
        result = json.loads(jsonData)
        self.logMsg("Individual Item Json Data : " + str(result), level=2)
        result = result.get("Items")
        if(result == None):
            result = []
        item_count = 1
        for item in result:
            self.updateDB(item)

    def updateBackgroundData(self):
        self.logMsg("updateBackgroundData Called")
        db.set("itemString","")
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        mb3Host = addonSettings.getSetting('ipaddress')
        mb3Port = addonSettings.getSetting('port')    
        userName = addonSettings.getSetting('username')     
        
        userid = downloadUtils.getUserId()
        
        self.logMsg("UserName : " + userName + " UserID : " + userid)
        
        self.logMsg("Updating BackgroundData Movie List")
        WINDOW = xbmcgui.Window( 10000 )
        dataUrl = "http://" + mb3Host + ":" + mb3Port + "/mediabrowser/Users/" + userid + "/Items?Recursive=true&SortBy=SortName&Fields=Path,People,Genres,MediaStreams,Overview,ShortOverview,CriticRatingSummary,EpisodeCount,SeasonCount,Studios,CumulativeRunTimeTicks,Metascore,SeriesStudio,AirTime,DateCreated&SortOrder=Ascending&ExcludeLocationTypes=Virtual&IncludeItemTypes=Series,BoxSet,Movie&CollapseBoxSetItems=false&format=json"
         
        jsonData = downloadUtils.downloadUrl(dataUrl, suppress=False, popup=1 )
        result = json.loads(jsonData)
        self.logMsg("BackgroundData Movie Json Data : " + str(result), level=2)
        
        result = result.get("Items")
        if(result == None):
            result = []
        item_count = 1
        for item in result:
            self.updateDB(item)
        WINDOW.setProperty("BackgroundDataLoaded", "true")
    
            
    def updateDB(self, item):
        id=item.get("Id")
        userid = downloadUtils.getUserId()
        mb3Host = __settings__.getSetting('ipaddress')
        mb3Port = __settings__.getSetting('port')    
        Name=API().getName(item)
        db.set(id+".Name",Name)
        timeInfo = API().getTimeInfo(item)
        mediaStreams=API().getMediaStreams(item)
        userData=API().getUserData(item)
        people = API().getPeople(item)
        tvInfo=API().getTVInfo(item, userData)
        db.set(id+".Overview",API().getOverview(item))
        db.set(id+".OfficialRating",item.get("OfficialRating"))
        CommunityRating=item.get("CommunityRating")
        if CommunityRating != None:
            db.set(id+".CommunityRating",       str(CommunityRating))
        db.set(id+".Type",                      str(item.get("Type")).encode('utf-8'))
        db.set(id+".CriticRating",              str(item.get("CriticRating")))
        db.set(id+".ProductionYear",            str(item.get("ProductionYear")))
        db.set(id+".DateCreated",               API().getDate(item))
        db.set(id+".LocationType",              item.get("LocationType"))
        db.set(id+".PremiereDate",              str(item.get("PremiereDate")))
        db.set(id+".Video3DFormat",             item.get("Video3DFormat"))
        db.set(id+".IsFolder",                  str(item.get("IsFolder")))
        db.set(id+".RecursiveItemCount",        str(item.get("RecursiveItemCount")))
        db.set(id+".Primary",                   downloadUtils.getArtwork(item, "Primary")) 
        db.set(id+".Backdrop",                  downloadUtils.getArtwork(item, "Backdrop"))
        db.set(id+".poster",                    downloadUtils.getArtwork(item, "poster")) 
        db.set(id+".tvshow.poster",             downloadUtils.getArtwork(item, "tvshow.poster")) 
        db.set(id+".Banner",                    downloadUtils.getArtwork(item, "Banner")) 
        db.set(id+".Logo",                      downloadUtils.getArtwork(item, "Logo")) 
        db.set(id+".Disc",                      downloadUtils.getArtwork(item, "Disc")) 
        db.set(id+".Art",                       downloadUtils.getArtwork(item, "Art")) 
        db.set(id+".Thumb",                     downloadUtils.getArtwork(item, "Thumb")) 
        db.set(id+".Thumb3",                    downloadUtils.getArtwork(item, "Thumb3")) 
        db.set(id+".Primary2",                  downloadUtils.getArtwork(item, "Primary2")) 
        db.set(id+".Primary4",                  downloadUtils.getArtwork(item, "Primary4")) 
        db.set(id+".Primary3",                  downloadUtils.getArtwork(item, "Primary3")) 
        db.set(id+".Backdrop2",                 downloadUtils.getArtwork(item, "Backdrop2")) 
        db.set(id+".Backdrop3",                 downloadUtils.getArtwork(item, "Backdrop3")) 
        db.set(id+".BackdropNoIndicators",      downloadUtils.getArtwork(item, "BackdropNoIndicators"))         
        db.set(id+".Duration",                  timeInfo.get('Duration'))
        db.set(id+".CompletePercentage",        timeInfo.get('Percent'))
        db.set(id+".ResumeTime",                timeInfo.get('ResumeTime'))
        db.set(id+".TotalTime",                 timeInfo.get('TotalTime'))
        db.set(id+".Channels",                  mediaStreams.get('channels'))
        db.set(id+".VideoCodec",                mediaStreams.get('videocodec'))
        db.set(id+".AspectRatio",               mediaStreams.get('aspectratio'))
        db.set(id+".AudioCodec",                mediaStreams.get('audiocodec'))
        db.set(id+".Height",                    mediaStreams.get('height'))
        db.set(id+".Width",                     mediaStreams.get('width'))       
        db.set(id+".Director",                  people.get('Director'))
        db.set(id+".Writer",                    people.get('Writer'))
        db.set(id+".ItemType",                  item.get("Type"))
        db.set(id+".Watched",                   userData.get('Watched'))
        db.set(id+".Favorite",                  userData.get('Favorite'))
        db.set(id+".PlayCount",                 userData.get('PlayCount'))
        db.set(id+".UnplayedItemCount",         str(userData.get('UnplayedItemCount')))
        db.set(id+".Studio",                    API().getStudio(item))
        db.set(id+".Genre",                     API().getGenre(item))
        db.set(id+".WatchedURL",                'http://' + mb3Host + ':' + mb3Port + '/mediabrowser/Users/' + userid + '/PlayedItems/' + id)
        db.set(id+".FavoriteURL",               'http://' + mb3Host + ':' + mb3Port + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id)
        db.set(id+".DeleteURL",                 'http://' + mb3Host + ':' + mb3Port + '/mediabrowser/Items/' + id)
        db.set(id+".TotalSeasons",              tvInfo.get('TotalSeasons'))
        db.set(id+".TotalEpisodes",             tvInfo.get('TotalEpisodes'))
        db.set(id+".WatchedEpisodes",           tvInfo.get('WatchedEpisodes'))
        db.set(id+".UnWatchedEpisodes",         tvInfo.get('UnWatchedEpisodes'))
        db.set(id+".NumEpisodes",               tvInfo.get('NumEpisodes'))        
        db.set(id+".Season",                    tvInfo.get('Season'))        
        db.set(id+".Episode",                   tvInfo.get('Episode'))        
        db.set(id+".SeriesName",                tvInfo.get('SeriesName'))
        
        
        if(item.get("PremiereDate") != None):
            premieredatelist = (item.get("PremiereDate")).split("T")
            db.set(id+".PremiereDate",              premieredatelist[0])
        else:
            premieredate = ""

        # add resume percentage text to titles
        if (__settings__.getSetting('addResumePercent') == 'true' and Name != '' and timeInfo.get('Percent') != '0'):
            db.set(id+".Name", Name + " (" + timeInfo.get('Percent') + "%)")
