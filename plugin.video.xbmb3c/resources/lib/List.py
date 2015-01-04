import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

import os
import json
import threading
import sys
from datetime import datetime
import urllib
from DownloadUtils import DownloadUtils
from Database import Database
from urlparse import urlparse
from API import API


logLevel = 1
__settings__ = xbmcaddon.Addon(id='plugin.video.xbmb3c')
__addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
_MODE_GETCONTENT=0
_MODE_SEARCH=2
_MODE_SETVIEWS=3
_MODE_CAST_LIST=14
_MODE_SHOW_SEARCH=18
_MODE_BASICPLAY=12
_MODE_ITEM_DETAILS=17
CP_ADD_URL = 'XBMC.RunPlugin(plugin://plugin.video.couchpotato_manager/movies/add?title=%s)'

__cwd__ = __settings__.getAddonInfo('path')
PLUGINPATH = xbmc.translatePath( os.path.join( __cwd__) )
__language__     = __addon__.getLocalizedString

#define our global download utils
downloadUtils = DownloadUtils()
db = Database()

# EXPERIMENTAL    
class List():
    addonSettings = None
    __addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
    __addondir__    = xbmc.translatePath( __addon__.getAddonInfo('profile') ) 
    __language__     = __addon__.getLocalizedString
    
    
    def printDebug(self, msg, level = 1):
        if(logLevel >= level):
            if(logLevel == 2):
                try:
                    xbmc.log("XBMB3C " + str(level) + " -> " + inspect.stack()[1][3] + " : " + str(msg))
                except UnicodeEncodeError:
                    xbmc.log("XBMB3C " + str(level) + " -> " + inspect.stack()[1][3] + " : " + str(msg.encode('utf-8')))
            else:
                try:
                    xbmc.log("XBMB3C " + str(level) + " -> " + str(msg))
                except UnicodeEncodeError:
                    xbmc.log("XBMB3C " + str(level) + " -> " + str(msg.encode('utf-8')))
                    
    def processFast(self, url, results, progress, pluginhandle):
        cast=['None']
        self.printDebug("== ENTER: processFast ==")
        self.printDebug("Processing secondary menus")
        xbmcplugin.setContent(pluginhandle, 'movies')
        server = self.getServerFromURL(url)
        userid = downloadUtils.getUserId()
        
        detailsString = "Path,Genres,Studios,CumulativeRunTimeTicks,Metascore,SeriesStudio,AirTime,SeasonUserData"
        if(__settings__.getSetting('includeStreamInfo') == "true"):
            detailsString += ",MediaStreams"
        if(__settings__.getSetting('includePeople') == "true"):
            detailsString += ",People"
        if(__settings__.getSetting('includeOverview') == "true"):
            detailsString += ",Overview"            

        dirItems = []
        result = results.get("Items")
        if(result == None):
            result = []
        if len(result) == 1 and __settings__.getSetting('autoEnterSingle') == "true":
            if result[0].get("Type") == "Season":
                url="http://" + server + "/mediabrowser/Users/" + userid + "/items?ParentId=" + result[0].get("Id") + '&IsVirtualUnAired=false&IsMissing=false&Fields=' + detailsString + '&SortBy=SortName&format=json&ImageTypeLimit=1'
                jsonData = downloadUtils.downloadUrl(url, suppress=False, popup=1 )
                results = json.loads(jsonData)
                result=results.get("Items")
        item_count = len(result)
        current_item = 1;
        self.setWindowHeading(url, pluginhandle)
        db.set("viewType","")
        xbmcplugin.setContent(pluginhandle, 'movies') #This too
        selectAction = __settings__.getSetting('selectAction') #Play or show item        

        for item in result:
            if(progress != None):
                percentDone = (float(current_item) / float(item_count)) * 100
                progress.update(int(percentDone), __language__(30126) + str(current_item))
                current_item = current_item + 1
            id = str(item.get("Id")).encode('utf-8')
            if db.get(id + ".Name") != '':
                listItem=self.fastItem(item, pluginhandle)
            else:
                listItem=self.slowItem(item, pluginhandle)
            #Create the URL to pass to the item
            
            isFolder = item.get('IsFolder')
            if isFolder == True:
                SortByTemp = __settings__.getSetting('sortby')
                item_type=str(item.get("Type")).encode('utf-8')
                if SortByTemp == '' and not (item_type == 'Series' or item_type == 'Season' or item_type == 'BoxSet'  or item_type == 'MusicArtist'):
                    SortByTemp = 'SortName'
                if item_type=='Series' and __settings__.getSetting('flattenSeasons')=='true':
                    u = 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IncludeItemTypes=Episode&Recursive=true&IsVirtualUnAired=false&IsMissing=false&Fields=' + detailsString + '&SortBy=SortName' + '&format=json&ImageTypeLimit=1'
                else:
                    u = 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IsVirtualUnAired=false&IsMissing=false&Fields=' + detailsString + '&SortBy='+SortByTemp + '&format=json&ImageTypeLimit=1'
                if (item.get("RecursiveItemCount") != 0):
                    u = sys.argv[0] + "?url=" + urllib.quote(u) + '&mode=' + str(_MODE_GETCONTENT)
                    dirItems.append([u, listItem, isFolder])
            else:
                playDetails = server+',;'+id
                if 'mediabrowser/Videos' in playDetails:
                    if(selectAction == "1"):
                        u = sys.argv[0] + "?id=" + playDetails + "&mode=" + str(_MODE_ITEM_DETAILS)
                    else:
                        u = sys.argv[0] + "?url=" + playDetails + '&mode=' + str(_MODE_BASICPLAY)
                elif playDetails.startswith('http') or playDetails.startswith('file'):
                    u = sys.argv[0]+"?url="+urllib.quote(u)+mode
                else:
                    if(selectAction == "1"):
                        u = sys.argv[0] + "?id=" + id + "&mode=" + str(_MODE_ITEM_DETAILS)
                    else:
                        u = sys.argv[0]+"?url=" + playDetails + '&mode=' + str(_MODE_BASICPLAY)                
                dirItems.append([u, listItem, False])
        return dirItems

    def fastItem(self, item, pluginhandle):            
        isFolder = "false" #fix
        premieredate = ""
        id = item.get('Id')
        guiid = id
        details={'plot'         : db.get(id + ".Overview"),
                 }
        # Populate the extraData list
        item_type = db.get(id + ".Type")
        extraData={'itemtype'     : item_type}
        mode = _MODE_GETCONTENT
        if db.get("viewType")=="":
            self.setViewType(item, pluginhandle)      
        folder=False
 
        #Create the ListItem that will be displayed
        thumbPath=db.get(id + ".Primary")
        
        addCounts = __settings__.getSetting('addCounts') == 'true'
        
        WINDOW = xbmcgui.Window( 10000 )
        if WINDOW.getProperty("addshowname") == "true":
            if db.get(id + ".LocationType") == "Virtual":
                listItemName = db.get(id + ".PremiereDate") + " - " + db.get(id + '.SeriesName','') + " - " + "S" + db.get(id + 'Season') + "E" + db.get(id + ".Name")
                if(addCounts and db.get(id + ".RecursiveItemCount") != '' and db.get(id + "UnplayedItemCount") != ''):
                    listItemName = listItemName + " (" + str(int(db.get(id + ".RecursiveItemCount")) - int(db.get(id + ".UnplayedItemCount"))) + "/" + str(db.get(id + ".RecursiveItemCount")) + ")"
            else:
                if db.get(id + '.Season') == '':
                    season = '0'
                else:
                    season = db.get(id + '.Season')
                listItemName = db.get(id + 'SeriesName') + " - " + "S" + season + "E" + db.get(id + '.Name')
                if(addCounts and db.get(id + ".RecursiveItemCount") != '' and db.get(id + ".UnplayedItemCount") != ''):
                    listItemName = listItemName + " (" + str(int(db.get(id + ".RecursiveItemCount")) - int(db.get(id + ".UnplayedItemCount"))) + "/" + str(db.get(id + ".RecursiveItemCount")) + ")"
        else:
            listItemName = db.get(id + '.Name')
            if(addCounts and db.get(id + ".RecursiveItemCount") != 'None' and db.get(id + ".UnplayedItemCount") != ''):
                listItemName = listItemName + " (" + str(int(db.get(id + ".RecursiveItemCount")) - int(db.get(id + ".UnplayedItemCount"))) + "/" + str(db.get(id + ".RecursiveItemCount")) + ")"
        listItem = xbmcgui.ListItem(listItemName, iconImage=thumbPath, thumbnailImage=thumbPath)
        details['title'] =  listItemName
        self.printDebug("Setting thumbnail as " + thumbPath, level=2)
        
        listItem.setProperty("complete_percentage", db.get(id + "CompletePercentage"))          
       
        #Set the properties of the item, such as summary, name, season, etc
        if ( not folder):
            listItem.setProperty('TotalTime', str(db.get(id + ".Duration")))
            listItem.setProperty('ResumeTime', str(db.get(id + ".ResumeTime")))
        
        listItem.setArt({'poster':db.get(id + ".poster")})
        listItem.setArt({'tvshow.poster':db.get(id + ".tvshow.poster")})
        listItem.setArt({'clearlogo':db.get(id + ".Logo")})
        listItem.setArt({'discart':db.get(id + ".Disc")})
        listItem.setArt({'banner':db.get(id + ".Banner")})
        listItem.setArt({'clearart':db.get(id + ".Art")})
        listItem.setArt({'landscape':db.get(id + ".Thumb")})
        
        listItem.setProperty('fanart_image', db.get(id + ".Backdrop"))
        listItem.setProperty('small_poster', db.get(id + ".Primary2"))
        listItem.setProperty('tiny_poster', db.get(id + ".Primary4"))
        listItem.setProperty('medium_poster', db.get(id + ".Primary3"))
        listItem.setProperty('small_fanartimage', db.get(id + ".Backdrop2"))
        listItem.setProperty('medium_fanartimage', db.get(id + ".Backdrop3"))
        listItem.setProperty('medium_landscape', db.get(id + ".Thumb3"))
        listItem.setProperty('fanart_noindicators', db.get(id + ".BackdropNoIndicators"))
       
        menuItems = self.addContextMenu(details, extraData, folder)
        if(len(menuItems) > 0):
            listItem.addContextMenuItems( menuItems, True )
        videoInfoLabels = {}

        if(extraData.get('type') == None or extraData.get('type') == "Video"):
            videoInfoLabels.update(details)
        else:
            listItem.setInfo( type = extraData.get('type','Video'), infoLabels = details )
        
        videoInfoLabels["duration"] = db.get(id + ".Duration")

        userData=API().getUserData(item)
        videoInfoLabels["playcount"] = userData.get("PlayCount")
        if (userData.get("Favorite") == 'True'):
            videoInfoLabels["top250"] = "1"    
            
        videoInfoLabels["mpaa"] = db.get(id + ".OfficialRating")
        videoInfoLabels["rating"] = db.get(id + ".CommunityRating")
        videoInfoLabels["year"] = db.get(id + ".ProductionYear")
        videoInfoLabels["date"] = db.get(id + ".DateCreated")
        listItem.setProperty('CriticRating', db.get(id + ".CriticRating"))
        listItem.setProperty('ItemType', item_type)


        videoInfoLabels["director"] = db.get(id + ".Director")
        videoInfoLabels["writer"] = db.get(id + ".Writer")
        videoInfoLabels["studio"] = db.get(id + ".Studio")
        videoInfoLabels["genre"] = db.get(id + ".Genre")

        videoInfoLabels["premiered"] = db.get('premieredate')
        
        videoInfoLabels["episode"] = details.get('episode')
        videoInfoLabels["season"] = details.get('season') 
        listItem.setInfo('video', videoInfoLabels)

        listItem.setProperty('TotalTime', db.get(id + '.TotalTime'))
        listItem.setProperty('TotalSeasons',db.get(id + '.TotalSeasons'))
        listItem.setProperty('TotalEpisodes',db.get(id + '.TotalEpisodes'))
        listItem.setProperty('WatchedEpisodes',db.get(id + '.WatchedEpisodes'))
        listItem.setProperty('UnWatchedEpisodes',db.get(id + '.UnWatchedEpisodes'))
        listItem.setProperty('NumEpisodes',db.get(id + '.NumEpisodes'))
        
        pluginCastLink = "plugin://plugin.video.xbmb3c?mode=" + str(_MODE_CAST_LIST) + "&id=" + id
        listItem.setProperty('CastPluginLink', pluginCastLink)
        listItem.setProperty('ItemGUID', guiid)
        listItem.setProperty('id', id)
        listItem.setProperty('Video3DFormat', db.get(id + '.Video3DFormat'))

        listItem.addStreamInfo('video', 
                                    {'duration' : db.get(id + '.Duration'), 
                                     'aspect'   : db.get(id + '.AspectRatio'),
                                     'codec'    : db.get(id + '.VideoCodec'), 
                                     'width'    : db.get(id + '.Width'), 
                                     'height'   : db.get(id + '.Height')})
        listItem.addStreamInfo('audio', 
                                    {'codec'    : db.get(id + '.AudioCodec'),
                                     'channels' : db.get(id + '.Channels')})            
        menuItems = self.addContextMenu(details, userData, folder, id=id)
        if(len(menuItems) > 0):
            listItem.addContextMenuItems( menuItems, True )
        return listItem

    def slowItem(self, item, pluginhandle):            
        id = item.get('Id')
        guiid = id
        details={'plot'         : API().getOverview(item),
                 'TVShowTitle'  :  item.get("SeriesName"),
                 }
        # Populate the extraData list
        item_type = str(item.get("Type")).encode('utf-8')
        extraData={'itemtype'     : item_type}
        timeInfo = API().getTimeInfo(item)
        userData=API().getUserData(item)
        people = API().getPeople(item)
        mediaStreams=API().getMediaStreams(item)
        tvInfo=API().getTVInfo(item, userData)
        
        mode = _MODE_GETCONTENT
        if db.get("viewType")=="":
            self.setViewType(item, pluginhandle)
        folder=item.get("IsFolder")
 
        #Create the ListItem that will be displayed
        thumbPath=downloadUtils.getArtwork(item, "Primary")
        
        addCounts = __settings__.getSetting('addCounts') == 'true'
        
        WINDOW = xbmcgui.Window( 10000 )
        if WINDOW.getProperty("addshowname") == "true":
            if item.get("LocationType") == "Virtual":
                listItemName = API().getPremiereDate(item) + " - " + API().getSeriesName(item) + " - " + "S" + tvInfo.get('Season') + "E" + tvInfo.get('Episode') + " - " + API().getName(item)
                if(addCounts and item.get("RecursiveItemCount") != None and userData.get("UnplayedItemCount") != ''):
                    listItemName = listItemName + " (" + str(item.get("RecursiveItemCount") - userData.get("UnplayedItemCount")) + "/" + str(item.get("RecursiveItemCount")) + ")"
            else:
                if tvInfo.get('Season') == '':
                    season = '0'
                else:
                    season = tvInfo.get('Season')
                listItemName = API().getSeriesName(item) + " - " + "S" + season + "E" + tvInfo.get('Episode') + " - " + API().getName(item)
                if(addCounts and item.get("RecursiveItemCount") != None and userData.get("UnplayedItemCount") != ''):
                    listItemName = listItemName + " (" + str(item.get("RecursiveItemCount") - userData.get("UnplayedItemCount")) + "/" + str(item.get("RecursiveItemCount")) + ")"
        elif item.get("Type") == "Episode":
            prefix=''
            if __settings__.getSetting('addSeasonNumber') == 'true':
                prefix = "S" + tvInfo.get('Season')
                if __settings__.getSetting('addEpisodeNumber') == 'true':
                    prefix = prefix + "E"
            if __settings__.getSetting('addEpisodeNumber') == 'true':
                prefix = prefix + tvInfo.get('Episode')
            if prefix != '':
                listItemName = prefix + ' - ' + API().getName(item)
            else:
                listItemName = API().getName(item)
            guiid = item.get("SeriesId")       
        else:
            listItemName = API().getName(item)
            if(addCounts and item.get("RecursiveItemCount") != None and userData.get("UnplayedItemCount") != ''):
                listItemName = listItemName + " (" + str(item.get("RecursiveItemCount") - userData.get("UnplayedItemCount")) + "/" + str(item.get("RecursiveItemCount")) + ")"
        listItem = xbmcgui.ListItem(listItemName, iconImage=thumbPath, thumbnailImage=thumbPath)

        # add resume percentage text to titles
        if (__settings__.getSetting('addResumePercent') == 'true' and listItemName != '' and timeInfo.get('Percent') != '0'):
            listItemName = (listItemName + " (" + timeInfo.get('Percent') + "%)")

        details['title'] =  listItemName
        
        self.printDebug("Setting thumbnail as " + thumbPath, level=2)
        
        listItem.setProperty("complete_percentage", timeInfo.get("Percent"))          
       
        #Set the properties of the item, such as summary, name, season, etc
        if ( not folder):
            listItem.setProperty('TotalTime', timeInfo.get("Duration"))
            listItem.setProperty('ResumeTime', timeInfo.get("ResumeTime"))
        
        listItem.setArt({'poster':              downloadUtils.getArtwork(item, "poster")})
        listItem.setArt({'tvshow.poster':       downloadUtils.getArtwork(item, "tvshow.poster")})
        listItem.setArt({'clearlogo':           downloadUtils.getArtwork(item, "Logo")})
        listItem.setArt({'discart':             downloadUtils.getArtwork(item, "Disc")})
        listItem.setArt({'banner':              downloadUtils.getArtwork(item, "Banner")})
        listItem.setArt({'clearart':            downloadUtils.getArtwork(item, "Art")})
        listItem.setArt({'landscape':           downloadUtils.getArtwork(item, "Thumb")})
        
        listItem.setProperty('fanart_image',        downloadUtils.getArtwork(item, "Backdrop"))
        listItem.setProperty('small_poster',        downloadUtils.getArtwork(item, "Primary2"))
        listItem.setProperty('tiny_poster',         downloadUtils.getArtwork(item, "Primary4"))
        listItem.setProperty('medium_poster',       downloadUtils.getArtwork(item, "Primary3"))
        listItem.setProperty('small_fanartimage',   downloadUtils.getArtwork(item, "Backdrop2"))
        listItem.setProperty('medium_fanartimage',  downloadUtils.getArtwork(item, "Backdrop3"))
        listItem.setProperty('medium_landscape',    downloadUtils.getArtwork(item, "Thumb3"))
        listItem.setProperty('fanart_noindicators', downloadUtils.getArtwork(item, "BackdropNoIndicators"))
       
        menuItems = self.addContextMenu(details, userData, folder)
        if(len(menuItems) > 0):
            listItem.addContextMenuItems( menuItems, True )
        videoInfoLabels = {}

        if(extraData.get('type') == None or extraData.get('type') == "Video"):
            videoInfoLabels.update(details)
        else:
            listItem.setInfo( type = extraData.get('type','Video'), infoLabels = details )
        
        videoInfoLabels["duration"] = timeInfo.get('Duration')

        videoInfoLabels["playcount"] = userData.get("PlayCount")
        if (userData.get("Favorite") == 'True'):
            videoInfoLabels["top250"] = "1"    
            
        videoInfoLabels["mpaa"] = item.get("OfficialRating")
        CommunityRating=item.get("CommunityRating")
        if CommunityRating != None:
            videoInfoLabels["rating"] = CommunityRating
        videoInfoLabels["year"] = str(item.get("ProductionYear"))
        videoInfoLabels["date"] = API().getDate(item)
        listItem.setProperty('CriticRating', str(item.get("CriticRating")))
        listItem.setProperty('ItemType', item_type)


        videoInfoLabels["director"] = people.get("Director")
        videoInfoLabels["writer"] = people.get("Writer")
        videoInfoLabels["studio"] = API().getStudio(item)
        videoInfoLabels["genre"] = API().getGenre(item)
        videoInfoLabels["tracknumber"] = str(item.get("IndexNumber"))
        videoInfoLabels["premiered"] = API().getPremiereDate(item)
        videoInfoLabels["episode"] = tvInfo.get('Episode')
        videoInfoLabels["season"] = tvInfo.get('Season') 
        listItem.setInfo('video', videoInfoLabels)
        
        listItem.setProperty('TotalSeasons',tvInfo.get('TotalSeasons'))
        listItem.setProperty('TotalEpisodes',tvInfo.get('TotalEpisodes'))
        listItem.setProperty('WatchedEpisodes',tvInfo.get('WatchedEpisodes'))
        listItem.setProperty('UnWatchedEpisodes',tvInfo.get('UnWatchedEpisodes'))
        listItem.setProperty('NumEpisodes',tvInfo.get('NumEpisodes'))
        
        pluginCastLink = "plugin://plugin.video.xbmb3c?mode=" + str(_MODE_CAST_LIST) + "&id=" + id
        listItem.setProperty('CastPluginLink', pluginCastLink)
        listItem.setProperty('ItemGUID', guiid)
        listItem.setProperty('id', id)
        listItem.setProperty('Video3DFormat', item.get('Video3DFormat'))

        listItem.addStreamInfo('video', 
                                    {'duration' : timeInfo.get('totaltime'), 
                                     'aspect'   : mediaStreams.get('aspectratio'),
                                     'codec'    : mediaStreams.get('videocodec'), 
                                     'width'    : mediaStreams.get('width'), 
                                     'height'   : mediaStreams.get('height')})
        listItem.addStreamInfo('audio', 
                                    {'codec'    : mediaStreams.get('audiocodec'),
                                     'channels' : mediaStreams.get('channels')})            
        menuItems = self.addContextMenu(details, userData, folder, id=id)
        if(len(menuItems) > 0):
            listItem.addContextMenuItems( menuItems, True )
        return listItem        

    def setViewType(self, item, pluginhandle):
        if item.get("Type") == "Movie":
            xbmcplugin.setContent(pluginhandle, 'movies')
            db.set("viewType", "_MOVIES")
        elif item.get("Type") == "BoxSet":
            xbmcplugin.setContent(pluginhandle, 'movies')
            db.set("viewType", "_BOXSETS")
        elif item.get("Type") == "Series":
            xbmcplugin.setContent(pluginhandle, 'tvshows')
            db.set("viewType", "_SERIES")
        elif item.get("Type") == "Season":
            xbmcplugin.setContent(pluginhandle, 'seasons')
            db.set("viewType", "_SEASONS")
            guiid = item.get("SeriesId")
        elif item.get("Type") == "Episode":
            xbmcplugin.setContent(pluginhandle, 'episodes')
            db.set("viewType", "_EPISODES")
            guiid = item.get("SeriesId")
        elif item.get("Type") == "MusicArtist":
            xbmcplugin.setContent(pluginhandle, 'artists')
            db.set("viewType", "_MUSICARTISTS")
        elif item.get("Type") == "MusicAlbum":
            xbmcplugin.setContent(pluginhandle, 'albums')
            db.set("viewType", "_MUSICTALBUMS")
        elif item.get("Type") == "Audio":
            xbmcplugin.setContent(pluginhandle, 'songs')
            db.set("viewType", "_MUSICTRACKS")
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_TRACKNUM)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_NONE)
        else:
            db.set("viewType", "_MOVIES")
        if item.get("Type") == "Episode" and db.get("allowSort") != "false":
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_EPISODE)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_GENRE)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
        elif item.get("Type") != "Audio" and db.get("allowSort") != "false":
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_GENRE)
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)        
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_DATE)                
        else:
            xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_NONE)    
            
    def processDirectory(self, url, results, progress, pluginhandle):
        self.printDebug("== ENTER: processDirectory ==")
        parsed = urlparse(url)
        parsed = urlparse(url)
        parsedserver,parsedport=parsed.netloc.split(':')
        userid = downloadUtils.getUserId()
        self.printDebug("Processing secondary menus")
        xbmcplugin.setContent(pluginhandle, 'movies')

        server = self.getServerFromURL(url)
        
        detailsString = "Path,Genres,Studios,CumulativeRunTimeTicks,SeasonUserData"
        if(__settings__.getSetting('includeStreamInfo') == "true"):
            detailsString += ",MediaStreams"
        if(__settings__.getSetting('includePeople') == "true"):
            detailsString += ",People"
        if(__settings__.getSetting('includeOverview') == "true"):
            detailsString += ",Overview"            

        dirItems = []
        result = results.get("Items")
        if(result == None):
            result = []
        if len(result) == 1 and __settings__.getSetting('autoEnterSingle') == "true":
            if result[0].get("Type") == "Season":
                url="http://" + server + "/mediabrowser/Users/" + userid + "/items?ParentId=" + result[0].get("Id") + '&IsVirtualUnAired=false&IsMissing=false&Fields=' + detailsString + '&SortBy=SortName&format=json&ImageTypeLimit=1'
                jsonData = downloadUtils.downloadUrl(url, suppress=False, popup=1 )
                results = json.loads(jsonData)
                result=results.get("Items")
        item_count = len(result)
        current_item = 1;
        self.setWindowHeading(url, pluginhandle)
        viewTypeSet=False
    
        for item in result:
        
            if(progress != None):
                percentDone = (float(current_item) / float(item_count)) * 100
                progress.update(int(percentDone), __language__(30126) + str(current_item))
                current_item = current_item + 1
            
            if(item.get("Name") != None):
                tempTitle = item.get("Name").encode('utf-8')
            else:
                tempTitle = "Missing Title"
                
            id = str(item.get("Id")).encode('utf-8')
            guiid = id
            isFolder = item.get("IsFolder")
           
            item_type = str(item.get("Type")).encode('utf-8')
                  
            tempEpisode = ""
            if (item.get("IndexNumber") != None):
                episodeNum = item.get("IndexNumber")
                if episodeNum < 10:
                    tempEpisode = "0" + str(episodeNum)
                else:
                    tempEpisode = str(episodeNum)
                    
            tempSeason = ""
            if (str(item.get("ParentIndexNumber")) != None):
                tempSeason = str(item.get("ParentIndexNumber"))
                if item.get("ParentIndexNumber") < 10:
                    tempSeason = "0" + tempSeason
          
            
            if viewTypeSet==False:
                if item.get("Type") == "Movie":
                    xbmcplugin.setContent(pluginhandle, 'movies')
                    db.set("viewType", "_MOVIES")
                elif item.get("Type") == "BoxSet":
                    xbmcplugin.setContent(pluginhandle, 'movies')
                    db.set("viewType", "_BOXSETS")
                elif item.get("Type") == "Series":
                    xbmcplugin.setContent(pluginhandle, 'tvshows')
                    db.set("viewType", "_SERIES")
                elif item.get("Type") == "Season":
                    xbmcplugin.setContent(pluginhandle, 'seasons')
                    db.set("viewType", "_SEASONS")
                    guiid = item.get("SeriesId")
                elif item.get("Type") == "Episode":
                    xbmcplugin.setContent(pluginhandle, 'episodes')
                    db.set("viewType", "_EPISODES")
                    guiid = item.get("SeriesId")
                elif item.get("Type") == "MusicArtist":
                    xbmcplugin.setContent(pluginhandle, 'artists')
                    db.set("viewType", "_MUSICARTISTS")
                elif item.get("Type") == "MusicAlbum":
                    xbmcplugin.setContent(pluginhandle, 'albums')
                    db.set("viewType", "_MUSICTALBUMS")
                elif item.get("Type") == "Audio":
                    xbmcplugin.setContent(pluginhandle, 'songs')
                    db.set("viewType", "_MUSICTRACKS")
                else:
                    db.set("viewType", "_MOVIES")
                if item.get("Type") == "Episode" and db.get("allowSort") != "false":
                    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
                    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
                    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_GENRE)
                    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)
                elif db.get("allowSort") != "false":
                    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE)
                    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_YEAR)
                    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_GENRE)
                    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_VIDEO_RATING)                
                else:
                    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_NONE)                       
                viewTypeSet=True
                
            if item.get("Type") == "Episode":
                prefix=''
                if __settings__.getSetting('addSeasonNumber') == 'true':
                    prefix = "S" + str(tempSeason)
                    if __settings__.getSetting('addEpisodeNumber') == 'true':
                        prefix = prefix + "E"
                if __settings__.getSetting('addEpisodeNumber') == 'true':
                    prefix = prefix + str(tempEpisode)
                if prefix != '':
                    tempTitle = prefix + ' - ' + tempTitle
                guiid = item.get("SeriesId")                

                
            if(item.get("PremiereDate") != None):
                premieredatelist = (item.get("PremiereDate")).split("T")
                premieredate = premieredatelist[0]
            else:
                premieredate = ""
            
            # add the premiered date for Upcoming TV    
            if item.get("LocationType") == "Virtual":
                airtime = item.get("AirTime")
                tempTitle = tempTitle + ' - ' + str(premieredate) + ' - ' + str(airtime)     

            #Add show name to special TV collections RAL, NextUp etc
            WINDOW = xbmcgui.Window( 10000 )
            if (WINDOW.getProperty("addshowname") == "true" and item.get("SeriesName") != None):
                tempTitle=item.get("SeriesName").encode('utf-8') + " - " + tempTitle
            else:
                tempTitle=tempTitle

            mediaStreams = API().getMediaStreams(item)
            people = API().getPeople(item)
                        
            timeInfo = API().getTimeInfo(item)
            userData = API().getUserData(item)
            PlaybackPositionTicks = '100'
            favorite = "False"

            # Populate the details list
            details={'title'        : tempTitle,
                     'plot'         : item.get("Overview"),
                     'episode'      : tempEpisode,
                     'playcount'    : userData.get('PlayCount'),
                     'TVShowTitle'  :  item.get("SeriesName"),
                     'season'       : tempSeason,
                     'Video3DFormat' : item.get("Video3DFormat"),
                     }
                     
            try:
                tempDuration = str(int(item.get("RunTimeTicks", "0"))/(10000000*60))
                RunTimeTicks = str(item.get("RunTimeTicks", "0"))
            except TypeError:
                try:
                    tempDuration = str(int(item.get("CumulativeRunTimeTicks"))/(10000000*60))
                    RunTimeTicks = str(item.get("CumulativeRunTimeTicks"))
                except TypeError:
                    tempDuration = "0"
                    RunTimeTicks = "0"
            TotalSeasons     = 0 if item.get("ChildCount")==None else item.get("ChildCount")
            TotalEpisodes    = 0 if item.get("RecursiveItemCount")==None else item.get("RecursiveItemCount")
            WatchedEpisodes  = 0 if userData.get("UnplayedItemCount")==None else TotalEpisodes-userData.get("UnplayedItemCount")
            UnWatchedEpisodes = 0 if userData.get("UnplayedItemCount")==None else userData.get("UnplayedItemCount")
            NumEpisodes      = TotalEpisodes
            # Populate the extraData list
            extraData={'thumb'        : downloadUtils.getArtwork(item, "Primary") ,
                       'fanart_image' : downloadUtils.getArtwork(item, "Backdrop") ,
                       'poster'       : downloadUtils.getArtwork(item, "poster") , 
                       'tvshow.poster': downloadUtils.getArtwork(item, "tvshow.poster") ,
                       'banner'       : downloadUtils.getArtwork(item, "Banner") ,
                       'clearlogo'    : downloadUtils.getArtwork(item, "Logo") ,
                       'discart'      : downloadUtils.getArtwork(item, "Disc") ,
                       'clearart'     : downloadUtils.getArtwork(item, "Art") ,
                       'landscape'    : downloadUtils.getArtwork(item, "Thumb") ,
                       'medium_landscape': downloadUtils.getArtwork(item, "Thumb3") ,
                       'small_poster' : downloadUtils.getArtwork(item, "Primary2") ,
                       'tiny_poster' : downloadUtils.getArtwork(item, "Primary4") ,
                       'medium_poster': downloadUtils.getArtwork(item, "Primary3") ,
                       'small_fanartimage' : downloadUtils.getArtwork(item, "Backdrop2") ,
                       'medium_fanartimage' : downloadUtils.getArtwork(item, "Backdrop3") ,
                       'fanart_noindicators' : downloadUtils.getArtwork(item, "BackdropNoIndicators") ,                    
                       'id'           : id ,
                       'guiid'        : guiid ,
                       'mpaa'         : item.get("OfficialRating"),
                       'rating'       : item.get("CommunityRating"),
                       'criticrating' : item.get("CriticRating"), 
                       'year'         : item.get("ProductionYear"),
                       'locationtype' : item.get("LocationType"),
                       'premieredate' : premieredate,
                       'studio'       : API().getStudio(item),
                       'genre'        : API().getGenre(item),
                       'playcount'    : userData.get('PlayCount'),
                       'director'     : people.get('Director'),
                       'writer'       : people.get('Writer'),
                       'channels'     : mediaStreams.get('channels'),
                       'videocodec'   : mediaStreams.get('videocodec'),
                       'aspectratio'  : mediaStreams.get('aspectratio'),
                       'audiocodec'   : mediaStreams.get('audiocodec'),
                       'height'       : mediaStreams.get('height'),
                       'width'        : mediaStreams.get('width'),
                       'cast'         : people.get('Cast'),
                       'favorite'     : userData.get('Favorite'),
                       'watchedurl'   : 'http://' + server + '/mediabrowser/Users/'+ userid + '/PlayedItems/' + id,
                       'favoriteurl'  : 'http://' + server + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id,
                       'deleteurl'    : 'http://' + server + '/mediabrowser/Items/' + id,                   
                       'parenturl'    : url,
                       'resumetime'   : timeInfo.get('ResumeTime'),
                       'totaltime'    : timeInfo.get('Duration'),
                       'duration'     : timeInfo.get('Duration'),
                       'RecursiveItemCount' : item.get("RecursiveItemCount"),
                       'UnplayedItemCount' : userData.get("UnplayedItemCount"),
                       'TotalSeasons' : str(TotalSeasons),
                       'TotalEpisodes': str(TotalEpisodes),
                       'WatchedEpisodes': str(WatchedEpisodes),
                       'UnWatchedEpisodes': str(UnWatchedEpisodes),
                       'NumEpisodes'  : str(NumEpisodes),
                       'itemtype'     : item_type}
                       
                       
                       
            if extraData['thumb'] == '':
                extraData['thumb'] = extraData['fanart_image']

            extraData['mode'] = _MODE_GETCONTENT
            
            if isFolder == True:
                SortByTemp = __settings__.getSetting('sortby')
                if SortByTemp == '' and not (item_type == 'Series' or item_type == 'Season' or item_type == 'BoxSet' or item_type == 'MusicAlbum' or item_type == 'MusicArtist'):
                    SortByTemp = 'SortName'
                if item_type=='Series' and __settings__.getSetting('flattenSeasons')=='true':
                    u = 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IncludeItemTypes=Episode&Recursive=true&IsVirtualUnAired=false&IsMissing=false&Fields=' + detailsString + '&SortBy=SortName'+'&format=json&ImageTypeLimit=1'
                else:
                    u = 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IsVirtualUnAired=false&IsMissing=false&Fields=' + detailsString + '&SortBy='+SortByTemp+'&format=json&ImageTypeLimit=1'
                if (item.get("RecursiveItemCount") != 0):
                    dirItems.append(self.addGUIItem(u, details, extraData))
            else:
                u = server+',;'+id
                dirItems.append(self.addGUIItem(u, details, extraData, folder=False))
        return dirItems

    def processSearch(self, url, results, progress, pluginhandle):
        cast=['None']
        self.printDebug("== ENTER: processSearch ==")
        parsed = urlparse(url)
        parsedserver,parsedport=parsed.netloc.split(':')
        userid = downloadUtils.getUserId()
        xbmcplugin.setContent(pluginhandle, 'movies')
        detailsString = "Path,Genres,Studios,CumulativeRunTimeTicks"
        if(__settings__.getSetting('includeStreamInfo') == "true"):
            detailsString += ",MediaStreams"
        if(__settings__.getSetting('includePeople') == "true"):
            detailsString += ",People"
        if(__settings__.getSetting('includeOverview') == "true"):
            detailsString += ",Overview"            
        server = self.getServerFromURL(url)
        self.setWindowHeading(url, pluginhandle)
        
        dirItems = []
        result = results.get("SearchHints")
        if(result == None):
            result = []

        item_count = len(result)
        current_item = 1;
            
        for item in result:
            id=str(item.get("ItemId")).encode('utf-8')
            type=item.get("Type").encode('utf-8')
            
            if(progress != None):
                percentDone = (float(current_item) / float(item_count)) * 100
                progress.update(int(percentDone), __language__(30126) + str(current_item))
                current_item = current_item + 1
            
            if(item.get("Name") != None):
                tempTitle = item.get("Name")
                tempTitle=tempTitle.encode('utf-8')
            else:
                tempTitle = "Missing Title"
                
            if type=="Series" or type=="MusicArtist" or type=="MusicAlbum" or type=="Folder":
                isFolder = True
            else:
                isFolder = False
            item_type = str(type).encode('utf-8')
            
            tempEpisode = ""
            if (item.get("IndexNumber") != None):
                episodeNum = item.get("IndexNumber")
                if episodeNum < 10:
                    tempEpisode = "0" + str(episodeNum)
                else:
                    tempEpisode = str(episodeNum)
                    
            tempSeason = ""
            if (str(item.get("ParentIndexNumber")) != None):
                tempSeason = str(item.get("ParentIndexNumber"))
          
            if type == "Episode" and __settings__.getSetting('addEpisodeNumber') == 'true':
                tempTitle = str(tempEpisode) + ' - ' + tempTitle

            #Add show name to special TV collections RAL, NextUp etc
            WINDOW = xbmcgui.Window( 10000 )
            if type==None:
                type=''
            if item.get("Series")!=None:
                series=item.get("Series").encode('utf-8')
                tempTitle=type + ": " + series + " - " + tempTitle
            else:
                tempTitle=type + ": " +tempTitle
            # Populate the details list
            details={'title'        : tempTitle,
                     'episode'      : tempEpisode,
                     'TVShowTitle'  : item.get("Series"),
                     'season'       : tempSeason
                     }
                     
            try:
                tempDuration = str(int(item.get("RunTimeTicks", "0"))/(10000000*60))
                RunTimeTicks = str(item.get("RunTimeTicks", "0"))
            except TypeError:
                try:
                    tempDuration = str(int(item.get("CumulativeRunTimeTicks"))/(10000000*60))
                    RunTimeTicks = str(item.get("CumulativeRunTimeTicks"))
                except TypeError:
                    tempDuration = "0"
                    RunTimeTicks = "0"

            # Populate the extraData list
            extraData={'thumb'        : downloadUtils.getArtwork(item, "Primary")  ,
                       'fanart_image' : downloadUtils.getArtwork(item, "Backdrop") ,
                       'poster'       : downloadUtils.getArtwork(item, "poster") , 
                       'tvshow.poster': downloadUtils.getArtwork(item, "tvshow.poster") ,
                       'banner'       : downloadUtils.getArtwork(item, "Banner") ,
                       'clearlogo'    : downloadUtils.getArtwork(item, "Logo") ,
                       'discart'      : downloadUtils.getArtwork(item, "Disc") ,
                       'clearart'     : downloadUtils.getArtwork(item, "Art") ,
                       'landscape'    : downloadUtils.getArtwork(item, "landscape") ,
                       'id'           : id ,
                       'year'         : item.get("ProductionYear"),
                       'watchedurl'   : 'http://' + server + '/mediabrowser/Users/'+ userid + '/PlayedItems/' + id,
                       'favoriteurl'  : 'http://' + server + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id,
                       'deleteurl'    : 'http://' + server + '/mediabrowser/Items/' + id,                   
                       'parenturl'    : url,
                       'totaltime'    : tempDuration,
                       'duration'     : tempDuration,
                       'itemtype'     : item_type}
                       
            if extraData['thumb'] == '':
                extraData['thumb'] = extraData['fanart_image']

            extraData['mode'] = _MODE_GETCONTENT
            if isFolder == True:
                u = 'http://' + server + '/mediabrowser/Users/'+ userid + '/items?ParentId=' +id +'&IsVirtualUnAired=false&IsMissing=false&Fields=' + detailsString + '&format=json&ImageTypeLimit=1'
                dirItems.append(self.addGUIItem(u, details, extraData))
            elif tempDuration != '0':
                u = server+',;'+id
                dirItems.append(self.addGUIItem(u, details, extraData, folder=False))
        return dirItems

    def processChannels(self, url, results, progress, pluginhandle):
        self.printDebug("== ENTER: processChannels ==")
        parsed = urlparse(url)
        parsedserver,parsedport=parsed.netloc.split(':')
        userid = downloadUtils.getUserId()
        xbmcplugin.setContent(pluginhandle, 'movies')
        detailsString = "Path,Genres,Studios,CumulativeRunTimeTicks"
        if(__settings__.getSetting('includeStreamInfo') == "true"):
            detailsString += ",MediaStreams"
        if(__settings__.getSetting('includePeople') == "true"):
            detailsString += ",People"
        if(__settings__.getSetting('includeOverview') == "true"):
            detailsString += ",Overview"            
        server = self.getServerFromURL(url)
        dirItems = []
        result = results.get("Items")
        if(result == None):
            result = []

        item_count = len(result)
        current_item = 1;
            
        for item in result:
            id=str(item.get("Id")).encode('utf-8')
            type=item.get("Type").encode('utf-8')
            
            if(progress != None):
                percentDone = (float(current_item) / float(item_count)) * 100
                progress.update(int(percentDone), __language__(30126) + str(current_item))
                current_item = current_item + 1
            
            if(item.get("Name") != None):
                tempTitle = item.get("Name")
                tempTitle=tempTitle.encode('utf-8')
            else:
                tempTitle = "Missing Title"
                
            if type=="ChannelFolderItem":
                isFolder = True
            else:
                isFolder = False
            item_type = str(type).encode('utf-8')
            
            if(item.get("ChannelId") != None):
               channelId = str(item.get("ChannelId")).encode('utf-8')
            
            channelName = ''   
            if(item.get("ChannelName") != None):
               channelName = item.get("ChannelName").encode('utf-8')   
               
            if(item.get("PremiereDate") != None):
                premieredatelist = (item.get("PremiereDate")).split("T")
                premieredate = premieredatelist[0]
            else:
                premieredate = ""
            
            mediaStreams=API().getMediaStreams(item, True)
                    
            people = API().getPeople(item)

            # Process Studios
            studio = API().getStudio(item)
            
            # Process Genres
            genre = ""
            genres = item.get("Genres")
            if(genres != None and genres != []):
                for genre_string in genres:
                    if genre == "": #Just take the first genre
                        genre = genre_string
                    elif genre_string != None:
                        genre = genre + " / " + genre_string
                    
            # Process UserData
            userData = item.get("UserData")
            PlaybackPositionTicks = '100'
            overlay = "0"
            favorite = "False"
            seekTime = 0
            if(userData != None):
                if userData.get("Played") != True:
                    overlay = "7"
                    watched = "true"
                else:
                    overlay = "6"
                    watched = "false"
                if userData.get("IsFavorite") == True:
                    overlay = "5"
                    favorite = "True"
                else:
                    favorite = "False"
                if userData.get("PlaybackPositionTicks") != None:
                    PlaybackPositionTicks = str(userData.get("PlaybackPositionTicks"))
                    reasonableTicks = int(userData.get("PlaybackPositionTicks")) / 1000
                    seekTime = reasonableTicks / 10000
            
            playCount = 0
            if(userData != None and userData.get("Played") == True):
                playCount = 1
            # Populate the details list
            details={'title'        : tempTitle,
                     'channelname'  : channelName,
                     'plot'         : item.get("Overview"),
                     'Overlay'      : overlay,
                     'playcount'    : str(playCount)}
            
            db.set("viewType", "")
            if item.get("Type") == "ChannelVideoItem":
                xbmcplugin.setContent(pluginhandle, 'movies')
                db.set("viewType", "_CHANNELS")
            elif item.get("Type") == "ChannelAudioItem":
                xbmcplugin.setContent(pluginhandle, 'songs')
                db.set("viewType", "_MUSICTRACKS")
                     
            try:
                tempDuration = str(int(item.get("RunTimeTicks", "0"))/(10000000*60))
                RunTimeTicks = str(item.get("RunTimeTicks", "0"))
            except TypeError:
                try:
                    tempDuration = str(int(item.get("CumulativeRunTimeTicks"))/(10000000*60))
                    RunTimeTicks = str(item.get("CumulativeRunTimeTicks"))
                except TypeError:
                    tempDuration = "0"
                    RunTimeTicks = "0"

            # Populate the extraData list
            extraData={'thumb'        : downloadUtils.getArtwork(item, "Primary")  ,
                       'fanart_image' : downloadUtils.getArtwork(item, "Backdrop") ,
                       'poster'       : downloadUtils.getArtwork(item, "poster") , 
                       'tvshow.poster': downloadUtils.getArtwork(item, "tvshow.poster") ,
                       'banner'       : downloadUtils.getArtwork(item, "Banner") ,
                       'clearlogo'    : downloadUtils.getArtwork(item, "Logo") ,
                       'discart'      : downloadUtils.getArtwork(item, "Disc") ,
                       'clearart'     : downloadUtils.getArtwork(item, "Art") ,
                       'landscape'    : downloadUtils.getArtwork(item, "Thumb") ,
                       'id'           : id ,
                       'rating'       : item.get("CommunityRating"),
                       'year'         : item.get("ProductionYear"),
                       'premieredate' : premieredate,
                       'studio'       : studio,
                       'genre'        : genre,
                       'playcount'    : str(playCount),
                       'director'     : people.get('Director'),
                       'writer'       : people.get('Writer'),
                       'channels'     : mediaStreams.get('channels'),
                       'videocodec'   : mediaStreams.get('videocodec'),
                       'aspectratio'  : mediaStreams.get('aspectratio'),
                       'audiocodec'   : mediaStreams.get('audiocodec'),
                       'height'       : mediaStreams.get('height'),
                       'width'        : mediaStreams.get('width'),
                       'cast'         : people.get('Cast'),
                       'favorite'     : favorite,   
                       'watchedurl'   : 'http://' + server + '/mediabrowser/Users/'+ userid + '/PlayedItems/' + id,
                       'favoriteurl'  : 'http://' + server + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id,
                       'deleteurl'    : 'http://' + server + '/mediabrowser/Items/' + id,                   
                       'parenturl'    : url,
                       'totaltime'    : tempDuration,
                       'duration'     : tempDuration,
                       'itemtype'     : item_type}
                       
            if extraData['thumb'] == '':
                extraData['thumb'] = extraData['fanart_image']

            extraData['mode'] = _MODE_GETCONTENT
            if type=="Channel":
                u = 'http://' + server + '/mediabrowser/Channels/'+ id + '/Items?userid=' +userid + '&format=json'
                dirItems.append(self.addGUIItem(u, details, extraData))
            
            elif isFolder == True:
                u = 'http://' + server + '/mediabrowser/Channels/'+ channelId + '/Items?userid=' +userid + '&folderid=' + id + '&format=json'
                dirItems.append(self.addGUIItem(u, details, extraData))
            else: 
                u = server+',;'+id
                dirItems.append(self.addGUIItem(u, details, extraData, folder=False))
        return dirItems

    def processPlaylists(self, url, results, progress, pluginhandle):
        self.printDebug("== ENTER: processPlaylists ==")
        parsed = urlparse(url)
        parsedserver,parsedport=parsed.netloc.split(':')
        userid = downloadUtils.getUserId()
        xbmcplugin.setContent(pluginhandle, 'movies')
        detailsString = ""          
        server = self.getServerFromURL(url)
        dirItems = []
        result = results.get("Items")
        if(result == None):
            result = []

        item_count = len(result)
        current_item = 1;
        xbmcplugin.setContent(pluginhandle, 'movies')
        db.set("viewType", "_MOVIES")            

        for item in result:
            id=str(item.get("Id")).encode('utf-8')
            type=item.get("Type").encode('utf-8')
            
            if(progress != None):
                percentDone = (float(current_item) / float(item_count)) * 100
                progress.update(int(percentDone), __language__(30126) + str(current_item))
                current_item = current_item + 1
            
            if(item.get("Name") != None):
                tempTitle = item.get("Name")
                tempTitle=tempTitle.encode('utf-8')
            else:
                tempTitle = "Missing Title"
                
            
            isFolder = False
            item_type = str(type).encode('utf-8')
            
          
            # Populate the details list
            details={'title'        : tempTitle}
                    
            try:
                tempDuration = str(int(item.get("RunTimeTicks", "0"))/(10000000*60))
                RunTimeTicks = str(item.get("RunTimeTicks", "0"))
            except TypeError:
                try:
                    tempDuration = str(int(item.get("CumulativeRunTimeTicks"))/(10000000*60))
                    RunTimeTicks = str(item.get("CumulativeRunTimeTicks"))
                except TypeError:
                    tempDuration = "0"
                    RunTimeTicks = "0"

            # Populate the extraData list
            extraData={'thumb'        : downloadUtils.getArtwork(item, "Primary")  ,
                       'fanart_image' : downloadUtils.getArtwork(item, "Backdrop") ,
                       'poster'       : downloadUtils.getArtwork(item, "poster") , 
                       'tvshow.poster': downloadUtils.getArtwork(item, "tvshow.poster") ,
                       'banner'       : downloadUtils.getArtwork(item, "Banner") ,
                       'clearlogo'    : downloadUtils.getArtwork(item, "Logo") ,
                       'discart'      : downloadUtils.getArtwork(item, "Disc") ,
                       'clearart'     : downloadUtils.getArtwork(item, "Art") ,
                       'landscape'    : downloadUtils.getArtwork(item, "Thumb") ,
                       'id'           : id ,
                       'year'         : item.get("ProductionYear"),
                       'watchedurl'   : 'http://' + server + '/mediabrowser/Users/'+ userid + '/PlayedItems/' + id,
                       'favoriteurl'  : 'http://' + server + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id,
                       'deleteurl'    : 'http://' + server + '/mediabrowser/Items/' + id,                   
                       'parenturl'    : url,
                       'totaltime'    : tempDuration,
                       'duration'     : tempDuration,
                       'itemtype'     : item_type}
                       
            if extraData['thumb'] == '':
                extraData['thumb'] = extraData['fanart_image']

            extraData['mode'] = _MODE_GETCONTENT
          
            u = server+',;'+id+',;'+'PLAYLIST'
            dirItems.append(self.addGUIItem(u, details, extraData, folder=False))
        return dirItems

    def processGenres(self, url, results, progress, content, pluginhandle):
        self.printDebug("== ENTER: processGenres ==")
        parsed = urlparse(url)
        parsedserver,parsedport=parsed.netloc.split(':')
        userid = downloadUtils.getUserId()
        xbmcplugin.setContent(pluginhandle, 'movies')
        detailsString = "Path,Genres,Studios,CumulativeRunTimeTicks"
        if(__settings__.getSetting('includeStreamInfo') == "true"):
            detailsString += ",MediaStreams"
        if(__settings__.getSetting('includePeople') == "true"):
            detailsString += ",People"
        if(__settings__.getSetting('includeOverview') == "true"):
            detailsString += ",Overview"            
        server = self.getServerFromURL(url)
        dirItems = []
        result = results.get("Items")
        if(result == None):
            result = []

        item_count = len(result)
        current_item = 1;
        db.set("viewType", "_MOVIES")            
        
        for item in result:
            id=str(item.get("Id")).encode('utf-8')
            type=item.get("Type").encode('utf-8')
            item_type = str(type).encode('utf-8')
            if(progress != None):
                percentDone = (float(current_item) / float(item_count)) * 100
                progress.update(int(percentDone), __language__(30126) + str(current_item))
                current_item = current_item + 1
            
            if(item.get("Name") != None):
                tempTitle = item.get("Name")
                tempTitle=tempTitle.encode('utf-8')
            else:
                tempTitle = "Missing Title"
                
           
            isFolder = True
          
            # Populate the details list
            details={'title'        : tempTitle}
                      
            try:
                tempDuration = str(int(item.get("RunTimeTicks", "0"))/(10000000*60))
                RunTimeTicks = str(item.get("RunTimeTicks", "0"))
            except TypeError:
                try:
                    tempDuration = str(int(item.get("CumulativeRunTimeTicks"))/(10000000*60))
                    RunTimeTicks = str(item.get("CumulativeRunTimeTicks"))
                except TypeError:
                    tempDuration = "0"
                    RunTimeTicks = "0"

            # Populate the extraData list
            extraData={'thumb'        : downloadUtils.getArtwork(item, "Primary") ,
                       'fanart_image' : downloadUtils.getArtwork(item, "Backdrop") ,
                       'poster'       : downloadUtils.getArtwork(item, "poster") , 
                       'tvshow.poster': downloadUtils.getArtwork(item, "tvshow.poster") ,
                       'banner'       : downloadUtils.getArtwork(item, "Banner") ,
                       'clearlogo'    : downloadUtils.getArtwork(item, "Logo") ,
                       'discart'      : downloadUtils.getArtwork(item, "Disc") ,
                       'clearart'     : downloadUtils.getArtwork(item, "Art") ,
                       'landscape'    : downloadUtils.getArtwork(item, "Thumb") ,
                       'id'           : id ,
                       'year'         : item.get("ProductionYear"),
                       'watchedurl'   : 'http://' + server + '/mediabrowser/Users/'+ userid + '/PlayedItems/' + id,
                       'favoriteurl'  : 'http://' + server + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id,
                       'deleteurl'    : 'http://' + server + '/mediabrowser/Items/' + id,                   
                       'parenturl'    : url,
                       'totaltime'    : tempDuration,
                       'duration'     : tempDuration,
                       'itemtype'     : item_type}
                       
            if extraData['thumb'] == '':
                extraData['thumb'] = extraData['fanart_image']

            extraData['mode'] = _MODE_GETCONTENT
                                     
            u = 'http://' + server + '/mediabrowser/Users/' + userid + '/Items?&SortBy=SortName&Fields=' + detailsString + '&Recursive=true&SortOrder=Ascending&IncludeItemTypes=' + content + '&Genres=' + item.get("Name") + '&format=json&ImageTypeLimit=1'
            dirItems.append(self.addGUIItem(u, details, extraData))
          
        return dirItems

    def processArtists(self, url, results, progress, pluginhandle):
        self.printDebug("== ENTER: processArtists ==")
        parsed = urlparse(url)
        parsedserver,parsedport=parsed.netloc.split(':')
        userid = downloadUtils.getUserId()
        xbmcplugin.setContent(pluginhandle, 'movies')
        detailsString = "Path,Genres,Studios,CumulativeRunTimeTicks"
        if(__settings__.getSetting('includeStreamInfo') == "true"):
            detailsString += ",MediaStreams"
        if(__settings__.getSetting('includePeople') == "true"):
            detailsString += ",People"
        if(__settings__.getSetting('includeOverview') == "true"):
            detailsString += ",Overview"            
        server = self.getServerFromURL(url)
        dirItems = []
        result = results.get("Items")
        if(result == None):
            result = []

        item_count = len(result)
        current_item = 1;
        db.set("viewType", "_MUSICARTISTS")            
        for item in result:
            id=str(item.get("Id")).encode('utf-8')
            type=item.get("Type").encode('utf-8')
            item_type = str(type).encode('utf-8')
            if(progress != None):
                percentDone = (float(current_item) / float(item_count)) * 100
                progress.update(int(percentDone), __language__(30126) + str(current_item))
                current_item = current_item + 1
            
            if(item.get("Name") != None):
                tempTitle = item.get("Name")
                tempTitle=tempTitle.encode('utf-8')
            else:
                tempTitle = "Missing Title"
                
           
            isFolder = True
       
          
            # Populate the details list
            details={'title'        : tempTitle}
            
            try:
                tempDuration = str(int(item.get("RunTimeTicks", "0"))/(10000000*60))
                RunTimeTicks = str(item.get("RunTimeTicks", "0"))
            except TypeError:
                try:
                    tempDuration = str(int(item.get("CumulativeRunTimeTicks"))/(10000000*60))
                    RunTimeTicks = str(item.get("CumulativeRunTimeTicks"))
                except TypeError:
                    tempDuration = "0"
                    RunTimeTicks = "0"

            # Populate the extraData list
            extraData={'thumb'        : downloadUtils.getArtwork(item, "Primary") ,
                       'fanart_image' : downloadUtils.getArtwork(item, "Backdrop") ,
                       'poster'       : downloadUtils.getArtwork(item, "poster") , 
                       'tvshow.poster': downloadUtils.getArtwork(item, "tvshow.poster") ,
                       'banner'       : downloadUtils.getArtwork(item, "Banner") ,
                       'clearlogo'    : downloadUtils.getArtwork(item, "Logo") ,
                       'discart'      : downloadUtils.getArtwork(item, "Disc") ,
                       'clearart'     : downloadUtils.getArtwork(item, "Art") ,
                       'landscape'    : downloadUtils.getArtwork(item, "Thumb") ,
                       'id'           : id ,
                       'year'         : item.get("ProductionYear"),
                       'watchedurl'   : 'http://' + server + '/mediabrowser/Users/'+ userid + '/PlayedItems/' + id,
                       'favoriteurl'  : 'http://' + server + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id,
                       'deleteurl'    : 'http://' + server + '/mediabrowser/Items/' + id,                   
                       'parenturl'    : url,
                       'totaltime'    : tempDuration,
                       'duration'     : tempDuration,
                       'itemtype'     : item_type}
                       
            if extraData['thumb'] == '':
                extraData['thumb'] = extraData['fanart_image']

            extraData['mode'] = _MODE_GETCONTENT
            
            # Somehow need to handle foreign characters .. 
            title = item.get("Name").replace(" ", "+")
                                
            u = 'http://' + server + '/mediabrowser/Users/' + userid + '/Items?SortBy=SortName&Fields=AudioInfo&Recursive=true&SortOrder=Ascending&IncludeItemTypes=MusicAlbum&Artists=' + title + '&format=json&ImageTypeLimit=1'
            dirItems.append(self.addGUIItem(u, details, extraData))
          
        return dirItems

    def processStudios(self, url, results, progress, content, pluginhandle):
        self.printDebug("== ENTER: processStudios ==")
        parsed = urlparse(url)
        parsedserver,parsedport=parsed.netloc.split(':')
        userid = downloadUtils.getUserId()
        xbmcplugin.setContent(pluginhandle, 'movies')
        detailsString = "Path,Genres,Studios,CumulativeRunTimeTicks"
        if(__settings__.getSetting('includeStreamInfo') == "true"):
            detailsString += ",MediaStreams"
        if(__settings__.getSetting('includePeople') == "true"):
            detailsString += ",People"
        if(__settings__.getSetting('includeOverview') == "true"):
            detailsString += ",Overview"            
        server = self.getServerFromURL(url)
        dirItems = []
        result = results.get("Items")
        if(result == None):
            result = []

        item_count = len(result)
        current_item = 1;
        db.set("viewType", "_MOVIES")            
        for item in result:
            id=str(item.get("Id")).encode('utf-8')
            type=item.get("Type").encode('utf-8')
            item_type = str(type).encode('utf-8')
            if(progress != None):
                percentDone = (float(current_item) / float(item_count)) * 100
                progress.update(int(percentDone), __language__(30126) + str(current_item))
                current_item = current_item + 1
            
            if(item.get("Name") != None):
                tempTitle = item.get("Name")
                tempTitle=tempTitle.encode('utf-8')
            else:
                tempTitle = "Missing Title"
                
           
            isFolder = True
          
            # Populate the details list
            details={'title'        : tempTitle}
            

                     
            try:
                tempDuration = str(int(item.get("RunTimeTicks", "0"))/(10000000*60))
                RunTimeTicks = str(item.get("RunTimeTicks", "0"))
            except TypeError:
                try:
                    tempDuration = str(int(item.get("CumulativeRunTimeTicks"))/(10000000*60))
                    RunTimeTicks = str(item.get("CumulativeRunTimeTicks"))
                except TypeError:
                    tempDuration = "0"
                    RunTimeTicks = "0"

            # Populate the extraData list
            extraData={'thumb'        : downloadUtils.getArtwork(item, "Primary") ,
                       'fanart_image' : downloadUtils.getArtwork(item, "Backdrop") ,
                       'poster'       : downloadUtils.getArtwork(item, "poster") , 
                       'tvshow.poster': downloadUtils.getArtwork(item, "tvshow.poster") ,
                       'banner'       : downloadUtils.getArtwork(item, "Banner") ,
                       'clearlogo'    : downloadUtils.getArtwork(item, "Logo") ,
                       'discart'      : downloadUtils.getArtwork(item, "Disc") ,
                       'clearart'     : downloadUtils.getArtwork(item, "Art") ,
                       'landscape'    : downloadUtils.getArtwork(item, "Thumb") ,
                       'id'           : id ,
                       'year'         : item.get("ProductionYear"),
                       'watchedurl'   : 'http://' + server + '/mediabrowser/Users/'+ userid + '/PlayedItems/' + id,
                       'favoriteurl'  : 'http://' + server + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id,
                       'deleteurl'    : 'http://' + server + '/mediabrowser/Items/' + id,                   
                       'parenturl'    : url,
                       'totaltime'    : tempDuration,
                       'duration'     : tempDuration,
                       'itemtype'     : item_type}
                       
            if extraData['thumb'] == '':
                extraData['thumb'] = extraData['fanart_image']

            extraData['mode'] = _MODE_GETCONTENT
            xbmc.log("XBMB3C - process studios nocode: " + tempTitle)
            tempTitle = tempTitle.replace(' ', '+')
            xbmc.log("XBMB3C - process studios nocode spaces replaced: " + tempTitle)
            tempTitle2 = unicode(tempTitle,'utf-8')          
            u = 'http://' + server + '/mediabrowser/Users/' + userid + '/Items?&SortBy=SortName&Fields=' + detailsString + '&Recursive=true&SortOrder=Ascending&IncludeItemTypes=' + content + '&Studios=' + tempTitle2.encode('ascii','ignore') + '&format=json&ImageTypeLimit=1'
            xbmc.log("XBMB3C - process studios: " + u)
            dirItems.append(self.addGUIItem(u, details, extraData))
          
        return dirItems

    def processPeople(self, url, results, progress, content, pluginhandle):
        self.printDebug("== ENTER: processPeople ==")
        parsed = urlparse(url)
        parsedserver,parsedport=parsed.netloc.split(':')
        userid = downloadUtils.getUserId()
        xbmcplugin.setContent(pluginhandle, 'movies')
        detailsString = "Path,Genres,Studios,CumulativeRunTimeTicks"
        if(__settings__.getSetting('includeStreamInfo') == "true"):
            detailsString += ",MediaStreams"
        if(__settings__.getSetting('includePeople') == "true"):
            detailsString += ",People"
        if(__settings__.getSetting('includeOverview') == "true"):
            detailsString += ",Overview"            
        server = self.getServerFromURL(url)
        dirItems = []
        result = results.get("Items")
        if(result == None):
            result = []

        item_count = len(result)
        current_item = 1;
        db.set("viewType", "_MOVIES")
        for item in result:
            id=str(item.get("Id")).encode('utf-8')
            type=item.get("Type").encode('utf-8')
            item_type = str(type).encode('utf-8')
            if(progress != None):
                percentDone = (float(current_item) / float(item_count)) * 100
                progress.update(int(percentDone), __language__(30126) + str(current_item))
                current_item = current_item + 1
            
            if(item.get("Name") != None):
                tempTitle = item.get("Name")
                tempTitle=tempTitle.encode('utf-8')
            else:
                tempTitle = "Missing Title"
                
           
            isFolder = True
       
          
            # Populate the details list
            details={'title'        : tempTitle}
                     
            try:
                tempDuration = str(int(item.get("RunTimeTicks", "0"))/(10000000*60))
                RunTimeTicks = str(item.get("RunTimeTicks", "0"))
            except TypeError:
                try:
                    tempDuration = str(int(item.get("CumulativeRunTimeTicks"))/(10000000*60))
                    RunTimeTicks = str(item.get("CumulativeRunTimeTicks"))
                except TypeError:
                    tempDuration = "0"
                    RunTimeTicks = "0"

            # Populate the extraData list
            extraData={'thumb'        : downloadUtils.getArtwork(item, "Primary") ,
                       'fanart_image' : downloadUtils.getArtwork(item, "Backdrop") ,
                       'poster'       : downloadUtils.getArtwork(item, "poster") , 
                       'tvshow.poster': downloadUtils.getArtwork(item, "tvshow.poster") ,
                       'banner'       : downloadUtils.getArtwork(item, "Banner") ,
                       'clearlogo'    : downloadUtils.getArtwork(item, "Logo") ,
                       'discart'      : downloadUtils.getArtwork(item, "Disc") ,
                       'clearart'     : downloadUtils.getArtwork(item, "Art") ,
                       'landscape'    : downloadUtils.getArtwork(item, "landscape") ,
                       'id'           : id ,
                       'year'         : item.get("ProductionYear"),
                       'watchedurl'   : 'http://' + server + '/mediabrowser/Users/'+ userid + '/PlayedItems/' + id,
                       'favoriteurl'  : 'http://' + server + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id,
                       'deleteurl'    : 'http://' + server + '/mediabrowser/Items/' + id,                   
                       'parenturl'    : url,
                       'totaltime'    : tempDuration,
                       'duration'     : tempDuration,
                       'itemtype'     : item_type}
                       
            if extraData['thumb'] == '':
                extraData['thumb'] = extraData['fanart_image']

            extraData['mode'] = _MODE_GETCONTENT
            xbmc.log("XBMB3C - process people nocode: " + tempTitle)
            tempTitle = tempTitle.replace(' ', '+')
            xbmc.log("XBMB3C - process people nocode spaces replaced: " + tempTitle)
            tempTitle2 = unicode(tempTitle,'utf-8')          
            u = 'http://' + server + '/mediabrowser/Users/' + userid + '/Items?&SortBy=SortName&Fields=' + detailsString + '&Recursive=true&SortOrder=Ascending&IncludeItemTypes=' + content + '&Person=' + tempTitle2.encode('ascii','ignore') + '&format=json&ImageTypeLimit=1'
            xbmc.log("XBMB3C - process people: " + u)
            dirItems.append(self.addGUIItem(u, details, extraData))
          
        return dirItems

    def addGUIItem(self, url, details, extraData, folder=True ):

        url = url.encode('utf-8')
    
        self.printDebug("Adding GuiItem for [%s]" % details.get('title','Unknown'), level=2)
        self.printDebug("Passed details: " + str(details), level=2)
        self.printDebug("Passed extraData: " + str(extraData), level=2)
        #self.printDebug("urladdgui:" + str(url))
        if details.get('title','') == '':
            return
    
        if extraData.get('mode',None) is None:
            mode="&mode=0"
        else:
            mode="&mode=%s" % extraData['mode']
        
        # play or show info
        selectAction = __settings__.getSetting('selectAction')
    
        #Create the URL to pass to the item
        if 'mediabrowser/Videos' in url:
            if(selectAction == "1"):
                u = sys.argv[0] + "?id=" + extraData.get('id') + "&mode=" + str(_MODE_ITEM_DETAILS)
            else:
                u = sys.argv[0] + "?url=" + url + '&mode=' + str(_MODE_BASICPLAY)
        elif 'mediabrowser/Search' in url:
            u = sys.argv[0]+"?url=" + url + '&mode=' + str(_MODE_SEARCH)
        #EXPERIMENTAL
        elif 'FastMovies' in url:
            u = sys.argv[0]+"?url=" + url + '&mode=' + str(_MODE_GETCONTENT)        
        #/EXPERIMENTAL
        elif 'SETVIEWS' in url:
            u = sys.argv[0]+"?url=" + url + '&mode=' + str(_MODE_SETVIEWS)     
        elif url.startswith('http') or url.startswith('file'):
            u = sys.argv[0]+"?url="+urllib.quote(url)+mode
        elif 'PLAYLIST' in url:
            u = sys.argv[0]+"?url=" + url + '&mode=' + str(_MODE_PLAYLISTPLAY)
        else:
            if(selectAction == "1"):
                u = sys.argv[0] + "?id=" + extraData.get('id') + "&mode=" + str(_MODE_ITEM_DETAILS)
            else:
                u = sys.argv[0]+"?url=" + url + '&mode=' + str(_MODE_BASICPLAY)
    
        #Create the ListItem that will be displayed
        thumbPath=str(extraData.get('thumb',''))
        
        addCounts = __settings__.getSetting('addCounts') == 'true'
        
        WINDOW = xbmcgui.Window( 10000 )
        if WINDOW.getProperty("addshowname") == "true":
            if extraData.get('locationtype')== "Virtual":
                listItemName = extraData.get('premieredate').decode("utf-8") + u" - " + details.get('SeriesName','').decode("utf-8") + u" - " + u"S" + details.get('season').decode("utf-8") + u"E" + details.get('title','Unknown').decode("utf-8")
                if(addCounts and extraData.get("RecursiveItemCount") != None and extraData.get("UnplayedItemCount") != None):
                    listItemName = listItemName + " (" + str(extraData.get("RecursiveItemCount") - extraData.get("UnplayedItemCount")) + "/" + str(extraData.get("RecursiveItemCount")) + ")"
                list = xbmcgui.ListItem(listItemName, iconImage=thumbPath, thumbnailImage=thumbPath)
            else:
                if details.get('season') == None:
                    season = '0'
                else:
                    season = details.get('season')
                listItemName = details.get('SeriesName','').decode("utf-8") + u" - " + u"S" + season + u"E" + details.get('title','Unknown').decode("utf-8")
                if(addCounts and extraData.get("RecursiveItemCount") != None and extraData.get("UnplayedItemCount") != None):
                    listItemName = listItemName + " (" + str(extraData.get("RecursiveItemCount") - extraData.get("UnplayedItemCount")) + "/" + str(extraData.get("RecursiveItemCount")) + ")"
                list = xbmcgui.ListItem(listItemName, iconImage=thumbPath, thumbnailImage=thumbPath)
        else:
            listItemName = details.get('title','Unknown')
            if(addCounts and extraData.get("RecursiveItemCount") != None and extraData.get("UnplayedItemCount") != None):
                listItemName = listItemName + " (" + str(extraData.get("RecursiveItemCount") - extraData.get("UnplayedItemCount")) + "/" + str(extraData.get("RecursiveItemCount")) + ")"
            list = xbmcgui.ListItem(listItemName, iconImage=thumbPath, thumbnailImage=thumbPath)
        self.printDebug("Setting thumbnail as " + thumbPath, level=2)
        
        # calculate percentage
        percentage = 0
        if (extraData.get('resumetime') != None and float(extraData.get('resumetime')) > 0):
            duration = float(extraData.get('duration'))
            if(duration > 0):
                resume = float(extraData.get('resumetime')) #/ 60.0
                percentage = int((resume / duration) * 100.0)
                list.setProperty("complete_percentage", str(percentage))          
        # add resume percentage text to titles
        addResumePercent = __settings__.getSetting('addResumePercent') == 'true'
        if (addResumePercent and details.get('title') != None and percentage != 0):
            details['title'] = details.get('title') + " (" + str(percentage) + "%)"
        
        #Set the properties of the item, such as summary, name, season, etc
        #list.setInfo( type=extraData.get('type','Video'), infoLabels=details )
        
        #For all end items    
        if ( not folder):
            #list.setProperty('IsPlayable', 'true')
            if extraData.get('type','video').lower() == "video":
                list.setProperty('TotalTime', str(extraData.get('duration')))
                list.setProperty('ResumeTime', str(extraData.get('resumetime')))
        
        artTypes=['poster', 'tvshow.poster', 'fanart_image', 'clearlogo', 'discart', 'banner', 'clearart', 'landscape', 'small_poster', 'tiny_poster', 'medium_poster','small_fanartimage', 'medium_fanartimage', 'medium_landscape', 'fanart_noindicators']
        
        for artType in artTypes:
            imagePath=str(extraData.get(artType,''))
            list=self.setArt(list,artType, imagePath)
            self.printDebug( "Setting " + artType + " as " + imagePath, level=2)
        
        menuItems = self.addContextMenu(details, extraData, folder)
        if(len(menuItems) > 0):
            list.addContextMenuItems( menuItems, True )
    
        # new way
        videoInfoLabels = {}
        
        if(extraData.get('type') == None or extraData.get('type') == "Video"):
            videoInfoLabels.update(details)
        else:
            list.setInfo( type = extraData.get('type','Video'), infoLabels = details )
        
        videoInfoLabels["duration"] = extraData.get("duration")
        videoInfoLabels["playcount"] = extraData.get("playcount")
        if (extraData.get('favorite') == 'True'):
            videoInfoLabels["top250"] = "1"    
            
        videoInfoLabels["mpaa"] = extraData.get('mpaa')
        videoInfoLabels["rating"] = extraData.get('rating')
        videoInfoLabels["director"] = extraData.get('director')
        videoInfoLabels["writer"] = extraData.get('writer')
        videoInfoLabels["year"] = extraData.get('year')
        videoInfoLabels["studio"] = extraData.get('studio')
        videoInfoLabels["genre"] = extraData.get('genre')
        if extraData.get('premieredate') != None:
            videoInfoLabels["premiered"] = extraData.get('premieredate').decode("utf-8")
        
        videoInfoLabels["episode"] = details.get('episode')
        videoInfoLabels["season"] = details.get('season') 
        
        list.setInfo('video', videoInfoLabels)
        
        list.addStreamInfo('video', {'duration': extraData.get('duration'), 'aspect': extraData.get('aspectratio'),'codec': extraData.get('videocodec'), 'width' : extraData.get('width'), 'height' : extraData.get('height')})
        list.addStreamInfo('audio', {'codec': extraData.get('audiocodec'),'channels': extraData.get('channels')})
        
        if extraData.get('criticrating') != None:
            list.setProperty('CriticRating', str(extraData.get('criticrating')))
        if extraData.get('itemtype') != None:
            list.setProperty('ItemType', extraData.get('itemtype'))
        if extraData.get('totaltime') != None:
            list.setProperty('TotalTime', extraData.get('totaltime'))
        if extraData.get('TotalSeasons')!=None:
            list.setProperty('TotalSeasons',extraData.get('TotalSeasons'))
        if extraData.get('TotalEpisodes')!=None:  
            list.setProperty('TotalEpisodes',extraData.get('TotalEpisodes'))
        if extraData.get('WatchedEpisodes')!=None:
            list.setProperty('WatchedEpisodes',extraData.get('WatchedEpisodes'))
        if extraData.get('UnWatchedEpisodes')!=None:
            list.setProperty('UnWatchedEpisodes',extraData.get('UnWatchedEpisodes'))
        if extraData.get('NumEpisodes')!=None:
            list.setProperty('NumEpisodes',extraData.get('NumEpisodes'))
        
        
        pluginCastLink = "plugin://plugin.video.xbmb3c?mode=" + str(_MODE_CAST_LIST) + "&id=" + str(extraData.get('id'))
        list.setProperty('CastPluginLink', pluginCastLink)
        list.setProperty('ItemGUID', extraData.get('guiid'))
        list.setProperty('id', extraData.get('id'))
        list.setProperty('Video3DFormat', details.get('Video3DFormat'))
            
        return [u, list, folder]

    def addContextMenu(self, details, userData, folder, id=''):
        self.printDebug("Building Context Menus", level=2)
        commands = []
        if id == '':
            id = userData.get('id')
            title=details.get('title')
            playcount=userData.get("playcount")
            favorite=userData.get('favorite')
        else:
            title=db.get(id + '.Name')       
            playcount=userData.get('PlayCount')
            favorite=userData.get('Favorite')

        WINDOW = xbmcgui.Window( 10000 )        
        userid = WINDOW.getProperty("userid")
        mb3Host = db.get("mb3Host")
        mb3Port = db.get("mb3Port")
        
        if id != None:
            watchedurl = 'http://' + mb3Host + ':' + mb3Port + '/mediabrowser/Users/' + userid + '/PlayedItems/' + id
            favoriteurl = 'http://' + mb3Host + ':' + mb3Port + '/mediabrowser/Users/'+ userid + '/FavoriteItems/' + id
            deleteurl = 'http://' + mb3Host + ':' + mb3Port + '/mediabrowser/Items/' + id
            scriptToRun = PLUGINPATH + "/default.py"
            
            pluginCastLink = "XBMC.Container.Update(plugin://plugin.video.xbmb3c?mode=" + str(_MODE_CAST_LIST) + "&id=" + str(id) + ")"
            commands.append(( __language__(30100), pluginCastLink))
            
            if playcount == "0":
                argsToPass = 'markWatched,' + watchedurl
                commands.append(( __language__(30093), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")"))
            else:
                argsToPass = 'markUnwatched,' + watchedurl
                commands.append(( __language__(30094), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")"))
            if favorite != 'True':
                argsToPass = 'markFavorite,' + favoriteurl
                commands.append(( __language__(30095), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")"))
            else:
                argsToPass = 'unmarkFavorite,' + favoriteurl
                commands.append(( __language__(30096), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")"))
                
            argsToPass = 'genrefilter'
            commands.append(( __language__(30040), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")"))
            
            if not folder:
                argsToPass = 'playall,' + id
                commands.append(( __language__(30041), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")"))  
                
            argsToPass = 'refresh'
            commands.append(( __language__(30042), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")"))
            
            argsToPass = 'delete,' + deleteurl
            commands.append(( __language__(30043), "XBMC.RunScript(" + scriptToRun + ", " + argsToPass + ")"))
            
            if details.get('channelname') == 'Trailers':
                commands.append(( __language__(30046),"XBMC.RunPlugin(%s)" % CP_ADD_URL % title))
                
        return(commands)

    def setArt (self, list, name, path): #Duplicate from main
        if name=='thumb' or name=='fanart_image' or name=='small_poster' or name=='tiny_poster'  or name == "medium_landscape" or name=='medium_poster' or name=='small_fanartimage' or name=='medium_fanartimage' or name=='fanart_noindicators':
            list.setProperty(name, path)
        else:#elif xbmcVersionNum >= 13:
            list.setArt({name:path})
        return list

    def getServerFromURL(self, url):  #Duplicate from main
        '''
        Simply split the URL up and get the server portion, sans port
        @ input: url, woth or without protocol
        @ return: the URL server
        '''
        if url[0:4] == "http":
            return url.split('/')[2]
        else:
            return url.split('/')[0]
            
    def setWindowHeading(self, url, pluginhandle) :
        WINDOW = xbmcgui.Window( 10000 )
        WINDOW.setProperty("addshowname", "false")
        WINDOW.setProperty("currenturl", url)
        WINDOW.setProperty("currentpluginhandle", str(pluginhandle))
        if 'ParentId' in url:
            dirUrl = url.replace('items?ParentId=','Items/')
            splitUrl = dirUrl.split('&')
            dirUrl = splitUrl[0] + '?format=json'
            jsonData = downloadUtils.downloadUrl(dirUrl)
            result = json.loads(jsonData)
            for name in result:
                title = name
            WINDOW.setProperty("heading", title)
        elif 'IncludeItemTypes=Episode' in url:
            WINDOW.setProperty("addshowname", "true")        