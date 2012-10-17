import urllib,urllib2,re,string
import xbmc,xbmcplugin,xbmcgui,xbmcaddon,CommonFunctions
import os
import simplejson as json
import unicodedata
import time
from xml.dom.minidom import parse
from time import strftime,sleep
from datetime import date

common = CommonFunctions

__settings__ = xbmcaddon.Addon(id='plugin.video.sagetv')
__language__ = __settings__.getLocalizedString
__cwd__      = __settings__.getAddonInfo('path')
sage_mac = __settings__.getSetting("sage_mac")

# SageTV recording Directories for path replacement
sage_rec = __settings__.getSetting("sage_rec")
sage_unc = __settings__.getSetting("sage_unc")
sage_rec2 = __settings__.getSetting("sage_rec2")
sage_unc2 = __settings__.getSetting("sage_unc2")
sage_rec3 = __settings__.getSetting("sage_rec3")
sage_unc3 = __settings__.getSetting("sage_unc3")
sage_rec4 = __settings__.getSetting("sage_rec4")
sage_unc4 = __settings__.getSetting("sage_unc4")
sage_rec5 = __settings__.getSetting("sage_rec5")
sage_unc5 = __settings__.getSetting("sage_unc5")

sagemappings = [ (sage_rec, sage_unc) ]

if ( sage_unc2 != '' and sage_unc2 != None ):
    sagemappings.append( (sage_rec2, sage_unc2) )
if ( sage_unc3 != '' and sage_unc3 != None ):
    sagemappings.append( (sage_rec3, sage_unc3) )
if ( sage_unc4 != '' and sage_unc4 != None ):
    sagemappings.append( (sage_rec4, sage_unc4) )
if ( sage_unc5 != '' and sage_unc5 != None ):
    sagemappings.append( (sage_rec5, sage_unc5) )

# Map file recording path to the first matching UNC path
def filemap(filepath):
    for (rec, unc) in sagemappings:
        if ( filepath.find(rec) != -1 ):
            return filepath.replace(rec, unc)

    return filepath

# SageTV URL based on user settings
strUrl = 'http://' + __settings__.getSetting("sage_user") + ':' + __settings__.getSetting("sage_pass") + '@' + __settings__.getSetting("sage_ip") + ':' + __settings__.getSetting("sage_port")
IMAGE_POSTER = xbmc.translatePath(os.path.join(__cwd__,'resources','media','poster.jpg'))
IMAGE_THUMB = xbmc.translatePath(os.path.join(__cwd__,'resources','media','thumb.jpg'))
DEFAULT_CHARSET = 'utf-8'
MIN_VERSION_SAGEX_REQUIRED = "7.1.9.12"

# 500-THUMBNAIL 501/502/505/506/507/508-LIST 503-MINFO2 504-MINFO 515-MINFO3
confluence_views = [500,501,502,503,504,508]


def TOPLEVELCATEGORIES():

    url = strUrl + '/sagex/api?command=GetInstalledPlugins&encoder=json'
    plugins = executeSagexAPIJSONCall(url, "Result")

    if(plugins == None or len(plugins) == 0):
        print "SageTV not detected, or required plugins not installed"
        xbmcgui.Dialog().ok(__language__(21000),__language__(21001),__language__(21002),__language__(21003))
        return
        
    print "Successfully able to connect to the SageTV server @ " + __settings__.getSetting("sage_ip") + ':' + __settings__.getSetting("sage_port")
    sagexVersion = ""
    for plugin in plugins:
        if(plugin.get("PluginIdentifier") == "sagex-api-services"):
            sagexVersion = plugin.get("PluginVersion")
 
    print "TOPLEVELCATEGORIES STARTED; sagex-api-services version=" + sagexVersion
    if(sagexVersion == ""):
        xbmcgui.Dialog().ok(__language__(21004),__language__(21005) + " " + MIN_VERSION_SAGEX_REQUIRED, __language__(21006),__language__(21007))
        return        
    if(comparePluginVersions(sagexVersion, MIN_VERSION_SAGEX_REQUIRED) < 0):
        xbmcgui.Dialog().ok(__language__(21004),__language__(21005) + " " + MIN_VERSION_SAGEX_REQUIRED, __language__(21008) + " " + sagexVersion,__language__(21009) + " " + MIN_VERSION_SAGEX_REQUIRED)
        return

    addTopLevelDir('1. Watch Recordings', strUrl + '/sagex/api?c=xbmc:GetTVMediaFilesGroupedByTitle&size=500&encoder=json',1,IMAGE_POSTER,'Browse previously recorded and currently recording shows')
    addTopLevelDir('2. View Upcoming Recordings', strUrl + '/sagex/api?command=GetScheduledRecordings&encoder=json',2,IMAGE_POSTER,'View and manage your upcoming recording schedule')
    addTopLevelDir('3. Browse Channel Listings', strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByBoolMethod(GetAllChannels(), "IsChannelViewable", true)&size=1000&encoder=json',3,IMAGE_POSTER,'Browse channels and manage recordings')
    addTopLevelDir('4. Search for Recordings', strUrl + '/',4,IMAGE_POSTER,'Search for Recordings')
    addTopLevelDir('5. Search for Airings', strUrl + '/',5,IMAGE_POSTER,'Search for Upcoming Airings')

    xbmc.executebuiltin("Container.SetViewMode(535)")
    
def VIEWLISTOFRECORDEDSHOWS(url,name):
    #Get the list of Recorded shows
    now = time.time()
    strNowObject = date.fromtimestamp(now)
    now = "%02d.%02d.%s" % (strNowObject.day+1, strNowObject.month, strNowObject.year)
    addDir('[All Shows]',strUrl + '/sagex/api?c=xbmc:GetMediaFilesForShowWithSubsetOfProperties&1=&size=500&encoder=json',11,IMAGE_POSTER,IMAGE_THUMB,'',now,'')
    titleObjects = executeSagexAPIJSONCall(url, "Result")
    titles = titleObjects.keys()
    for title in titles:
        mfsForTitle = titleObjects.get(title)
        for mfSubset in mfsForTitle:
            strTitle = mfSubset.get("ShowTitle")
            strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
            strMediaFileID = mfSubset.get("MediaFileID")
            strExternalID = mfSubset.get("ShowExternalID")
            startTime = float(mfSubset.get("AiringStartTime") // 1000)
            strAiringdateObject = date.fromtimestamp(startTime)
            strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
            break
        urlToShowEpisodes = strUrl + '/sagex/api?c=xbmc:GetMediaFilesForShowWithSubsetOfProperties&1=' + urllib2.quote(strTitle.encode("utf8")) + '&size=500&encoder=json'
        #urlToShowEpisodes = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByMethod(GetMediaFiles("T"),"GetMediaTitle","' + urllib2.quote(strTitle.encode("utf8")) + '",true)&size=500&encoder=json'
        #urlToShowEpisodes = strUrl + '/sage/Search?searchType=TVFiles&SearchString=' + urllib2.quote(strTitle.encode("utf8")) + '&DVD=on&sort2=airdate_asc&partials=both&TimeRange=0&pagelen=100&sort1=title_asc&filename=&Video=on&search_fields=title&xml=yes'
        print "ADDING strTitle=" + strTitle + "; urlToShowEpisodes=" + urlToShowEpisodes
        imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileID
        fanartUrl = strUrl + "/sagex/media/background/" + strMediaFileID
        #print "ADDING imageUrl=" + imageUrl
        addDir(strTitle, urlToShowEpisodes,11,imageUrl,'',strExternalID,strAiringdate,fanartUrl)

def VIEWLISTOFEPISODESFORSHOW(url,name):
    mfs = executeSagexAPIJSONCall(url, "Result")
    print "# of EPISODES for " + name + "=" + str(len(mfs))
    if(mfs == None or len(mfs) == 0):
        print "NO EPISODES FOUND FOR SHOW=" + name
        xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True)
        return

    for mfSubset in mfs:
        strTitle = mfSubset.get("ShowTitle")
        strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
        strMediaFileID = mfSubset.get("MediaFileID")

        strEpisode = mfSubset.get("EpisodeTitle")
        strDescription = mfSubset.get("EpisodeDescription")
        strGenre = mfSubset.get("ShowGenre")
        strAiringID = mfSubset.get("AiringID")
        seasonNum = int(mfSubset.get("SeasonNumber"))
        episodeNum = int(mfSubset.get("EpisodeNumber"))
        studio = mfSubset.get("AiringChannelName")
        isFavorite = mfSubset.get("IsFavorite")
        watchedDuration = mfSubset.get("WatchedDuration", 0) // 1000
        fileDuration = mfSubset.get("FileDuration", 0) // 1000
        isWatched = mfSubset.get("IsWatched")
        isArchived = mfSubset.get("IsLibraryFile")
        
        startTime = float(mfSubset.get("AiringStartTime") // 1000)
        strAiringdateObject = date.fromtimestamp(startTime)
        airTime = strftime('%H:%M', time.localtime(startTime))
        strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
        strOriginalAirdate = strAiringdate
        if(mfSubset.get("OriginalAiringDate") > 0):
            startTime = float(mfSubset.get("OriginalAiringDate") // 1000)
            strOriginalAirdateObject = date.fromtimestamp(startTime)
            strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

        # if there is no episode name use the description in the title
        if(strGenre.find("Movie")<0 and strGenre.find("Movies")<0 and strGenre.find("Film")<0 and strGenre.find("Shopping")<0 and strGenre.find("Consumer")<0):
            strDisplayText = strEpisode
            if(strEpisode == ""):
                if(strDescription != ""):
                    strDisplayText = strDescription
                else:
                    if(strGenre.find("News")>=0):
                        strDisplayText = studio + " News - " + strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime
                        strDescription = strGenre
                    elif(strGenre.find("Sports")>=0):
                        strDisplayText = strTitle + " - " + strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime
                        strDescription = strGenre
            if(name == "[All Shows]"):
                strDisplayText = strTitle + " - " + strDisplayText
        else:
            strDisplayText = strTitle

        segs = mfSubset.get("SegmentFiles")
        if(len(segs) == 1):
            strMappedFilepath = filemap(mfSubset.get("SegmentFiles")[0])
        else:
            #If a recording has multiple segments, stack them to group the segments together such that during playback it's transparent to the user
            strMappedFilepath = "stack://"
            for seg in segs:
                strMappedFilepath = strMappedFilepath + filemap(seg) + " , "
            #Once the stack:// is generated, remove the extraneous " , " at the end of it
            strMappedFilepath = strMappedFilepath[0:len(strMappedFilepath)-3]
            #strMappedFilepath = strUrl + '/sagex/api?c=xbmc:GetPlaylistOfSegmentsForMediafile&1=%s&2=%s&3=%s&raw_content_type=audio/mpegurl&encoder=raw' % (strMediaFileID, urllib2.quote(sage_rec.encode("utf8")), urllib2.quote(sage_unc.encode("utf8")))
        
        print "************SEGS=" + str(segs)
        print "************strMappedFilepath=" + str(strMappedFilepath)
        imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileID
        fanartUrl = strUrl + "/sagex/media/background/" + strMediaFileID
        addMediafileLink(strDisplayText,strMappedFilepath,strDescription,imageUrl,strGenre,strOriginalAirdate,strAiringdate,strTitle,strMediaFileID,strAiringID,seasonNum,episodeNum,studio,isFavorite,isWatched,watchedDuration,fileDuration,fanartUrl,isArchived)

    xbmc.executebuiltin("Container.SetViewMode(504)")

def VIEWUPCOMINGRECORDINGS(url,name):
    #req = urllib.urlopen(url)
    airings = executeSagexAPIJSONCall(url, "Result")
    for airing in airings:
        show = airing.get("Show")
        strTitle = airing.get("AiringTitle")
        strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
        strEpisode = show.get("ShowEpisode")
        if(strEpisode == None):
            strEpisode = ""        
        strDescription = show.get("ShowDescription")
        if(strDescription == None):
            strDescription = ""        
        strGenre = show.get("ShowCategoriesString")
        strAiringID = str(airing.get("AiringID"))
        seasonNum = int(show.get("ShowSeasonNumber"))
        episodeNum = int(show.get("ShowEpisodeNumber"))
        studio = airing.get("AiringChannelName")
        isFavorite = airing.get("IsFavorite")
        
        startTime = float(airing.get("AiringStartTime") // 1000)
        strAiringdateObject = date.fromtimestamp(startTime)
        airTime = strftime('%H:%M', time.localtime(startTime))
        strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
        strOriginalAirdate = strAiringdate
        if(airing.get("OriginalAiringDate")):
            startTime = float(airing.get("OriginalAiringDate") // 1000)
            strOriginalAirdateObject = date.fromtimestamp(startTime)
            strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

        # if there is no episode name use the description in the title
        
        strDisplayText = strTitle
        if(strGenre.find("Movie")<0 and strGenre.find("Movies")<0 and strGenre.find("Film")<0 and strGenre.find("Shopping")<0 and strGenre.find("Consumer")<0):
            if(strEpisode == ""):
                if(strDescription != ""):
                    strDisplayText = strTitle + ' - ' + strDescription
                else:
                    if(strGenre.find("News")>=0):
                        strDisplayText = studio + " News - " + strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime
                        strDescription = strGenre
                    elif(strGenre.find("Sports")>=0):
                        strDisplayText = strTitle + " - " + strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime
                        strDescription = strGenre
            else:
                strDisplayText = strTitle + ' - ' + strEpisode
        strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
        addAiringLink(strDisplayText,'',strDescription,IMAGE_THUMB,strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum,studio,isFavorite, airing.get("AiringStartTime"), airing.get("AiringEndTime"))

    xbmc.executebuiltin("Container.SetViewMode(504)")

def VIEWCHANNELLISTING(url,name):
    channels = executeSagexAPIJSONCall(url, "Result")
    for channel in channels:
        channelNumber = channel.get("ChannelNumber")
        channelName = channel.get("ChannelName")
        channelDescription = channel.get("ChannelDescription")
        channelNetwork = channel.get("ChannelNetwork")
        channelStationID = channel.get("StationID")
        now = time.time()
        startRange = str(long(now * 1000))
        rangeSizeDays = 7
        rangeSizeSeconds = rangeSizeDays * 24 * 60 * 60
        endRange = str(long((now + rangeSizeSeconds) * 1000))

        urlToAiringsOnChannel = strUrl + '/sagex/api?command=EvaluateExpression&1=GetAiringsOnChannelAtTime(GetChannelForStationID("' + str(channelStationID) + '"),"' + startRange + '","' + endRange + '",false)&encoder=json'
        logoUrl = strUrl + "/sagex/media/logo/" + str(channelStationID)
        strDisplayText = channelNumber + "-" + channelName
        addChannelDir(strDisplayText, urlToAiringsOnChannel,31,logoUrl,channelDescription)

    xbmc.executebuiltin("Container.SetViewMode(535)")

def VIEWAIRINGSONCHANNEL(url,name):
    airings = executeSagexAPIJSONCall(url, "Result")
    for airing in airings:
        show = airing.get("Show")
        strTitle = airing.get("AiringTitle")
        strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
        strEpisode = show.get("ShowEpisode")
        if(strEpisode == None):
            strEpisode = ""        
        strDescription = show.get("ShowDescription")
        if(strDescription == None):
            strDescription = ""        
        strGenre = show.get("ShowCategoriesString")
        strAiringID = str(airing.get("AiringID"))
        seasonNum = int(show.get("ShowSeasonNumber"))
        episodeNum = int(show.get("ShowEpisodeNumber"))
        studio = airing.get("AiringChannelName")        
        isFavorite = airing.get("IsFavorite")
        
        startTime = float(airing.get("AiringStartTime") // 1000)
        strAiringdateObject = date.fromtimestamp(startTime)
        airTime = strftime('%H:%M', time.localtime(startTime))
        strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
        strOriginalAirdate = strAiringdate
        if(airing.get("OriginalAiringDate")):
            startTime = float(airing.get("OriginalAiringDate") // 1000)
            strOriginalAirdateObject = date.fromtimestamp(startTime)
            strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

        # if there is no episode name use the description in the title
        strDisplayText = strTitle
        if(strGenre.find("Movie")<0 and strGenre.find("Movies")<0 and strGenre.find("Film")<0 and strGenre.find("Shopping")<0 and strGenre.find("Consumer")<0):
            if(strEpisode == ""):
                if(strDescription != ""):
                    strDisplayText = strTitle + ' - ' + strDescription
                else:
                    if(strGenre.find("News")>=0):
                        strDisplayText = studio + " News - " + strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime
                        strDescription = strGenre
                    elif(strGenre.find("Sports")>=0):
                        strDisplayText = strTitle + " - " + strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime
                        strDescription = strGenre
            else:
                strDisplayText = strTitle + ' - ' + strEpisode
        strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
        addAiringLink(strDisplayText,'',strDescription,IMAGE_THUMB,strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum,studio,isFavorite, airing.get("AiringStartTime"), airing.get("AiringEndTime"))

    xbmc.executebuiltin("Container.SetViewMode(504)")

def SEARCHFORRECORDINGS(url,name):
    titleToSearchFor = common.getUserInput(__language__(21010),"")
    if(titleToSearchFor == "" or titleToSearchFor == None):
        return
    url = strUrl + '/sagex/api?c=xbmc:SearchForMediaFiles&1=%s&size=100&encoder=json' % urllib2.quote(titleToSearchFor.encode("utf8"))
    #url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByMethod(GetMediaFiles("T"), "GetMediaTitle", "' + urllib2.quote(titleToSearchFor.encode("utf8")) + '", true)&size=100&encoder=json'
    mfs = executeSagexAPIJSONCall(url, "Result")
    print "# of EPISODES for " + titleToSearchFor + "=" + str(len(mfs))
    if(mfs == None or len(mfs) == 0):
        print "NO EPISODES FOUND FOR SEARCH=" + titleToSearchFor
        xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True)
        return

    for mfSubset in mfs:
        strTitle = mfSubset.get("ShowTitle")
        print "showtitle=" + str(strTitle)
        strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
        strMediaFileID = mfSubset.get("MediaFileID")

        strEpisode = mfSubset.get("EpisodeTitle")
        strDescription = mfSubset.get("EpisodeDescription")
        strGenre = mfSubset.get("ShowGenre")
        strAiringID = mfSubset.get("AiringID")
        seasonNum = int(mfSubset.get("SeasonNumber"))
        episodeNum = int(mfSubset.get("EpisodeNumber"))
        studio = mfSubset.get("AiringChannelName")
        isFavorite = mfSubset.get("IsFavorite")
        watchedDuration = mfSubset.get("WatchedDuration", 0) // 1000
        fileDuration = mfSubset.get("FileDuration", 0) // 1000
        isWatched = mfSubset.get("IsWatched")
        isArchived = mfSubset.get("IsLibraryFile")
        
        startTime = float(mfSubset.get("AiringStartTime") // 1000)
        strAiringdateObject = date.fromtimestamp(startTime)
        airTime = strftime('%H:%M', time.localtime(startTime))
        strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
        strOriginalAirdate = strAiringdate
        if(mfSubset.get("OriginalAiringDate") > 0):
            startTime = float(mfSubset.get("OriginalAiringDate") // 1000)
            strOriginalAirdateObject = date.fromtimestamp(startTime)
            strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

        # if there is no episode name use the description in the title
        strDisplayText = strTitle
        if(strGenre.find("Movie")<0 and strGenre.find("Movies")<0 and strGenre.find("Film")<0 and strGenre.find("Shopping")<0 and strGenre.find("Consumer")<0):
            if(strEpisode != "" and strDescription != ""):
                strDisplayText = strTitle + ' - ' + strDescription
            elif(strEpisode != ""):
                strDisplayText = strTitle + ' - ' + strEpisode
            else:
                if(strGenre.find("News")>=0):
                    strDisplayText = studio + " News - " + strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime
                    strDescription = strGenre
                elif(strGenre.find("Sports")>=0):
                    strDisplayText = strTitle + " - " + strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime
                    strDescription = strGenre
                

        segs = mfSubset.get("SegmentFiles")
        if(len(segs) == 1):
            strMappedFilepath = filemap(mfSubset.get("SegmentFiles")[0])
        else:
            #If a recording has multiple segments, stack them to group the segments together such that during playback it's transparent to the user
            strMappedFilepath = "stack://"
            for seg in segs:
                strMappedFilepath = strMappedFilepath + filemap(seg) + " , "
            #Once the stack:// is generated, remove the extraneous " , " at the end of it
            strMappedFilepath = strMappedFilepath[0:len(strMappedFilepath)-3]
            #strMappedFilepath = strUrl + '/sagex/api?c=xbmc:GetPlaylistOfSegmentsForMediafile&1=%s&2=%s&3=%s&raw_content_type=audio/mpegurl&encoder=raw' % (strMediaFileID, urllib2.quote(sage_rec.encode("utf8")), urllib2.quote(sage_unc.encode("utf8")))
        
        print "************SEGS=" + str(segs)
        print "************strMappedFilepath=" + str(strMappedFilepath)
        imageUrl = strUrl + "/sagex/media/poster/" + strMediaFileID
        fanartUrl = strUrl + "/sagex/media/background/" + strMediaFileID
        addMediafileLink(strDisplayText,strMappedFilepath,strDescription,imageUrl,strGenre,strOriginalAirdate,strAiringdate,strTitle,strMediaFileID,strAiringID,seasonNum,episodeNum,studio,isFavorite,isWatched,watchedDuration,fileDuration,fanartUrl,isArchived)

    xbmc.executebuiltin("Container.SetViewMode(504)")

def SEARCHFORAIRINGS(url,name):
    titleToSearchFor = common.getUserInput(__language__(21010),"")
    if(titleToSearchFor == "" or titleToSearchFor == None):
        return
    now = time.time()
    startRange = str(long(now * 1000))
    #url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByRange(SearchByTitle("%s","T"),"GetAiringStartTime","%s",java_lang_Long_MAX_VALUE,true)&encoder=json' % (urllib2.quote(titleToSearchFor.encode("utf8")), startRange)
    #url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByRange(SearchByTitle("%s","T"),"GetAiringStartTime",java_lang_Long_parseLong("%d"),java_lang_Long_MAX_VALUE,true)&encoder=json' % (urllib2.quote(titleToSearchFor.encode("utf8")), int(time.time()) * 1000)
    url = strUrl + '/sagex/api?command=EvaluateExpression&1=FilterByRange(SearchSelectedFields("%s",false,true,true,false,false,false,false,false,false,false,"T"),"GetAiringStartTime",java_lang_Long_parseLong("%d"),java_lang_Long_MAX_VALUE,true)&size=100&encoder=json' % (urllib2.quote(titleToSearchFor.encode("utf8")), int(time.time()) * 1000)
    airings = executeSagexAPIJSONCall(url, "Result")
    for airing in airings:
        show = airing.get("Show")
        strTitle = airing.get("AiringTitle")
        strTitle = unicodedata.normalize('NFKD', strTitle).encode('ascii','ignore')
        strEpisode = show.get("ShowEpisode")
        if(strEpisode == None):
            strEpisode = ""        
        strDescription = show.get("ShowDescription")
        if(strDescription == None):
            strDescription = ""        
        strGenre = show.get("ShowCategoriesString")
        strAiringID = str(airing.get("AiringID"))
        seasonNum = int(show.get("ShowSeasonNumber"))
        episodeNum = int(show.get("ShowEpisodeNumber"))
        studio = airing.get("AiringChannelName")        
        isFavorite = airing.get("IsFavorite")
        
        startTime = float(airing.get("AiringStartTime") // 1000)
        strAiringdateObject = date.fromtimestamp(startTime)
        airTime = strftime('%H:%M', time.localtime(startTime))
        strAiringdate = "%02d.%02d.%s" % (strAiringdateObject.day, strAiringdateObject.month, strAiringdateObject.year)
        strOriginalAirdate = strAiringdate
        if(airing.get("OriginalAiringDate")):
            startTime = float(airing.get("OriginalAiringDate") // 1000)
            strOriginalAirdateObject = date.fromtimestamp(startTime)
            strOriginalAirdate = "%02d.%02d.%s" % (strOriginalAirdateObject.day, strOriginalAirdateObject.month, strOriginalAirdateObject.year)

        # if there is no episode name use the description in the title
        strDisplayText = strTitle
        if(strGenre.find("Movie")<0 and strGenre.find("Movies")<0 and strGenre.find("Film")<0 and strGenre.find("Shopping")<0 and strGenre.find("Consumer")<0):
            if(strEpisode == ""):
                if(strDescription != ""):
                    strDisplayText = strTitle + ' - ' + strDescription
                else:
                    strDisplayText = studio + " News - " + strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime
                    strDescription = strGenre
            else:
                strDisplayText = strTitle + ' - ' + strEpisode
        strDisplayText = strftime('%a %b %d', time.localtime(startTime)) + " @ " + airTime + ": " + strDisplayText
        addAiringLink(strDisplayText,'',strDescription,IMAGE_THUMB,strGenre,strOriginalAirdate,strAiringdate,strTitle,strAiringID,seasonNum,episodeNum,studio,isFavorite, airing.get("AiringStartTime"), airing.get("AiringEndTime"))

    xbmc.executebuiltin("Container.SetViewMode(504)")

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

def addMediafileLink(name,url,plot,iconimage,genre,originalairingdate,airingdate,showtitle,mediafileid,airingid,seasonnum,episodenum,studio,isfavorite,iswatched,resumetime,totaltime,fanartimage,isArchived):
        ok=True
        liz=xbmcgui.ListItem(name)
        scriptToRun = "special://home/addons/plugin.video.sagetv/contextmenuactions.py"
        actionDelete = "delete|" + strUrl + '/sagex/api?command=DeleteFile&1=mediafile:' + mediafileid
        actionDeleteSetWatched = "deletesetwatched|" + strUrl + '/sagex/api?command=SetWatched&1=mediafile:' + mediafileid + "|" + strUrl + '/sagex/api?command=DeleteFile&1=mediafile:' + mediafileid
        actionDeleteClearWatched = "deleteclearwatched|" + strUrl + '/sagex/api?command=ClearWatched&1=mediafile:' + mediafileid + "|" + strUrl + '/sagex/api?command=DeleteFile&1=mediafile:' + mediafileid
        actionDeleteDontLike = "deletedontlike|" + strUrl + '/sagex/api?command=SetDontLike&1=mediafile:' + mediafileid + "|" + strUrl + '/sagex/api?command=DeleteFile&1=mediafile:' + mediafileid
        actionDeleteWrongRecording = "deletewrongrecording|" + strUrl + '/sagex/api?command=DeleteFileWithoutPrejudice&1=mediafile:' + mediafileid
        actionSetWatched = "setwatched|" + strUrl + '/sagex/api?command=SetWatched&1=mediafile:' + mediafileid
        actionClearWatched = "clearwatched|" + strUrl + '/sagex/api?command=ClearWatched&1=mediafile:' + mediafileid
        actionSetArchived = "setarchived|" + strUrl + '/sagex/api?command=MoveFileToLibrary&1=mediafile:' + mediafileid
        actionClearArchived = "cleararchived|" + strUrl + '/sagex/api?command=MoveTVFileOutOfLibrary&1=mediafile:' + mediafileid
        actionCancelRecording = "cancelrecording|" + strUrl + '/sagex/api?command=CancelRecord&1=mediafile:' + mediafileid
        actionRemoveFavorite = "removefavorite|" + strUrl + '/sagex/api?command=EvaluateExpression&1=RemoveFavorite(GetFavoriteForAiring(GetAiringForID(' + airingid + ')))'
        actionWatchStream = "watchstream|" + strUrl + "|" + mediafileid
        
        bisAiringRecording = isAiringRecording(airingid)

        contextMenuItems = []

        if(bisAiringRecording):
            contextMenuItems.append((__language__(21017), 'XBMC.RunScript(' + scriptToRun + ', ' + actionCancelRecording + ')'))
            if(isfavorite):
                contextMenuItems.append((__language__(21018), 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')'))
        else:
            if(isfavorite):
                contextMenuItems.append((__language__(21018), 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')'))

        if(iswatched):
            contextMenuItems.append((__language__(21023), 'XBMC.RunScript(' + scriptToRun + ', ' + actionClearWatched + ')'))
            liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Genre": genre, "date": airingdate, "premiered": originalairingdate, "aired": originalairingdate, "TVShowTitle": showtitle, "season": seasonnum, "episode": episodenum, "studio": studio, "overlay": 7, "playcount": 1 } )
        else:
            contextMenuItems.append((__language__(21022), 'XBMC.RunScript(' + scriptToRun + ', ' + actionSetWatched + ')'))
            if(resumetime != 0 and totaltime != 0):
                liz.setProperty("resumetime",str(resumetime))
                liz.setProperty("totaltime",str(totaltime))
            liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Genre": genre, "date": airingdate, "premiered": originalairingdate, "aired": originalairingdate, "TVShowTitle": showtitle, "season": seasonnum, "episode": episodenum, "studio": studio, "overlay": 6, "playcount": 0 } )

        if(isArchived):
            contextMenuItems.append((__language__(21025), 'XBMC.RunScript(' + scriptToRun + ', ' + actionClearArchived + ')'))
        else:
            contextMenuItems.append((__language__(21024), 'XBMC.RunScript(' + scriptToRun + ', ' + actionSetArchived + ')'))

        contextMenuItems.append((__language__(21016), 'XBMC.RunScript(' + scriptToRun + ', ' + actionDelete + ')'))
        contextMenuItems.append((__language__(21026), 'XBMC.RunScript(' + scriptToRun + ', ' + actionDeleteSetWatched + ')'))
        contextMenuItems.append((__language__(21027), 'XBMC.RunScript(' + scriptToRun + ', ' + actionDeleteClearWatched + ')'))
        contextMenuItems.append((__language__(21028), 'XBMC.RunScript(' + scriptToRun + ', ' + actionDeleteDontLike + ')'))
        contextMenuItems.append((__language__(21029), 'XBMC.RunScript(' + scriptToRun + ', ' + actionDeleteWrongRecording + ')'))
        contextMenuItems.append((__language__(21037), 'XBMC.RunScript(' + scriptToRun + ', ' + actionWatchStream + ')'))
        liz.addContextMenuItems(contextMenuItems, True)
        
        liz.setIconImage(iconimage)
        liz.setThumbnailImage(iconimage)
        liz.setProperty("fanart_image",fanartimage)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
        return ok

def addAiringLink(name,url,plot,iconimage,genre,originalairingdate,airingdate,showtitle,airingid,seasonnum,episodenum,studio,isfavorite,starttime,endtime):
    ok=True
    liz=xbmcgui.ListItem(name)
    scriptToRun = "special://home/addons/plugin.video.sagetv/contextmenuactions.py"
    actionCancelRecording = "cancelrecording|" + strUrl + '/sagex/api?command=CancelRecord&1=airing:' + airingid
    actionAddFavorite = "addfavorite|" + strUrl + '/sagex/api?command=AddFavorite&1=%s&2=true&3=true&4=&5=&6=&7=&8=&9=&10=&11=&12=&13=&14=' % showtitle
    actionRemoveFavorite = "removefavorite|" + strUrl + '/sagex/api?command=EvaluateExpression&1=RemoveFavorite(GetFavoriteForAiring(GetAiringForID(' + airingid + ')))'
    actionRecord = "record|" + strUrl + '/sagex/api?command=Record&1=airing:' + airingid
    actionWatchNow = "watchnow|" + strUrl + "|" + airingid
    
    bisAiringScheduledToRecord = isAiringScheduledToRecord(airingid)
    
    contextMenuItems = []
    
    if(bisAiringScheduledToRecord):
        contextMenuItems.append((__language__(21017), 'XBMC.RunScript(' + scriptToRun + ', ' + actionCancelRecording + ')'))
        if(isfavorite):
            contextMenuItems.append((__language__(21018), 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')'))
        else:
            contextMenuItems.append((__language__(21030), 'XBMC.RunScript(' + scriptToRun + ', ' + actionAddFavorite + ')'))
    else:
        if(isfavorite):
            contextMenuItems.append((__language__(21019), 'XBMC.RunScript(' + scriptToRun + ', ' + actionRecord + ')'))
            contextMenuItems.append((__language__(21018), 'XBMC.RunScript(' + scriptToRun + ', ' + actionRemoveFavorite + ')'))
        else:
            #Check if an airing is airing live right now; if it is, provide the ability to watch it live
            bisAiringLiveNow = isAiringLiveNow(starttime, endtime)
            print "bisAiringLiveNow=" + str(bisAiringLiveNow)
            if(bisAiringLiveNow):
                contextMenuItems.append((__language__(21020), 'XBMC.RunScript(' + scriptToRun + ', ' + actionWatchNow + ')'))
                
            contextMenuItems.append((__language__(21019), 'XBMC.RunScript(' + scriptToRun + ', ' + actionRecord + ')'))
            contextMenuItems.append((__language__(21030), 'XBMC.RunScript(' + scriptToRun + ', ' + actionAddFavorite + ')'))

    liz.addContextMenuItems(contextMenuItems, True)
    
    liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Genre": genre, "date": airingdate, "premiered": originalairingdate, "aired": originalairingdate, "TVShowTitle": showtitle, "season": seasonnum, "episode": episodenum, "studio": studio } )
    liz.setIconImage(iconimage)
    liz.setThumbnailImage(iconimage)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
    return ok

# Checks if an airing is currently recording
def isAiringScheduledToRecord(airingid):
    sageApiUrl = strUrl + '/sagex/api?command=EvaluateExpression&1=java_util_HashSet_contains(new_java_util_HashSet(java_util_Arrays_asList(GetScheduledRecordings())),GetAiringForID(' + airingid + '))&encoder=json'
    return executeSagexAPIJSONCall(sageApiUrl, "Result")
        
def isAiringRecording(airingid):
    sageApiUrl = strUrl + '/sagex/api?command=IsFileCurrentlyRecording&1=airing:' + airingid + '&encoder=json'
    return executeSagexAPIJSONCall(sageApiUrl, "Result")
        
def getShowSeriesDescription(showexternalid):
    sageApiUrl = strUrl + '/sagex/api?command=EvaluateExpression&1=GetSeriesDescription(GetShowSeriesInfo(GetShowForExternalID("' + showexternalid + '")))&encoder=json'
    return executeSagexAPIJSONCall(sageApiUrl, "Result")
        
def isAiringLiveNow(starttime, endtime):
    now = int(time.time()) * 1000
    if(now >= starttime and now < endtime):
        return True
    return False

def executeSagexAPIJSONCall(url, resultToGet):
    print "*** sagex request URL:" + url
    url_error = False
    input = ""
    try:
        input = urllib.urlopen(url)
        
    except IOError, i:
        print "ERROR in executeSagexAPIJSONCall: Unable to connect to SageTV server"
        xbmc.executebuiltin('WakeOnLan(%s)'% sage_mac)
        xbmc.sleep(15000)
        url_error = True
        
    if url_error:
      input = urllib.urlopen(url)
      
    fileData = input.read()
    resp = unicodeToStr(json.JSONDecoder().decode(fileData))

    objKeys = resp.keys()
    numKeys = len(objKeys)
    if(numKeys == 1):
        return resp.get(resultToGet)    

    else:
        return None

def addTopLevelDir(name,url,mode,iconimage,dirdescription):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name)

    liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": dirdescription } )
    liz.setIconImage(iconimage)
    liz.setThumbnailImage(iconimage)
    #liz.setIconImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
    #liz.setThumbnailImage(xbmc.translatePath(os.path.join(__cwd__,'resources','media',iconimage)))
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok

def addDir(name,url,mode,iconimage,thumbimage,showexternalid,airingdate,fanartimage):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name)
    strSeriesDescription = ""
    strSeriesDescription = getShowSeriesDescription(showexternalid)

    liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": strSeriesDescription, "date": airingdate } )
    liz.setIconImage(iconimage)
    if(thumbimage != ""):
        liz.setThumbnailImage(thumbimage)
    else:
        liz.setThumbnailImage(iconimage)
    liz.setProperty("fanart_image",fanartimage)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok

def addChannelDir(name,url,mode,iconimage,channeldescription):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
    ok=True
    liz=xbmcgui.ListItem(name)

    liz.setInfo(type="video", infoLabels={ "Title": name, "Plot": channeldescription } )
    liz.setIconImage(iconimage)
    liz.setThumbnailImage(iconimage)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok


def unicodeToStr(obj):
    t = obj
    if(t is unicode):
        return obj.encode(DEFAULT_CHARSET)
    elif(t is list):
        for i in range(0, len(obj)):
            obj[i] = unicodeToStr(obj[i])
        return obj
    elif(t is dict):
        for k in obj.keys():
            v = obj[k]
            del obj[k]
            obj[k.encode(DEFAULT_CHARSET)] = unicodeToStr(v)
        return obj
    else:
        return obj # leave numbers and booleans alone

def comparePluginVersions(s1, s2):

    # See if they are equal.
    if s1 == s2:
        return 0

    # Make sure they are the same length.
    str1 = normalizePluginString(s1, len(string.split(s2, '.')))
    str2 = normalizePluginString(s2, len(string.split(s1, '.')))

    # Split into parts separated by '.'
    p1 = string.split(str1, '.')
    p2 = string.split(str2, '.')

    for i in range(len(p1)):
        int1 = int(p1[i])
        int2 = int(p2[i])
        if int1 < int2:
            return -1
        elif int2 < int1:
            return 1

    return 0
        
def normalizePluginString(s, l):
    while len(string.split(s, '.')) < l:
        s += ".0"
    return s

params=get_params()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

if mode==None or url==None or len(url)<1:
        print ""
        TOPLEVELCATEGORIES()
       
elif mode==1:
    print ""+url
    VIEWLISTOFRECORDEDSHOWS(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
        
elif mode==11:
    print ""+url
    VIEWLISTOFEPISODESFORSHOW(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
        
elif mode==2:
    print ""+url
    VIEWUPCOMINGRECORDINGS(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

elif mode==3:
    print ""+url
    VIEWCHANNELLISTING(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)

elif mode==31:
    print ""+url
    VIEWAIRINGSONCHANNEL(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

elif mode==4:
    print ""+url
    SEARCHFORRECORDINGS(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

elif mode==5:
    print ""+url
    SEARCHFORAIRINGS(url,name)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_EPISODE)

xbmcplugin.setContent(int(sys.argv[1]),'episodes')
xbmcplugin.endOfDirectory(int(sys.argv[1]))
