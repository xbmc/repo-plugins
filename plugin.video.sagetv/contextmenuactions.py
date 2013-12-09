import urllib,urllib2,re,string
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
import time
from time import sleep
if sys.version_info >=  (2, 7):
    import json as _json
else:
    import simplejson as _json 

__settings__ = xbmcaddon.Addon(id='plugin.video.sagetv')
__language__ = __settings__.getLocalizedString
sage_mac = __settings__.getSetting("sage_mac")


DEFAULT_CHARSET = 'utf-8'
MIN_VERSION_STREAMING_SERVICES_PLUGIN_REQUIRED = "1.3.7.59"


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
    resp = unicodeToStr(_json.JSONDecoder().decode(fileData))

    objKeys = resp.keys()
    numKeys = len(objKeys)
    if(numKeys == 1):
        return resp.get(resultToGet)    

    else:
        return None

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
            # If the user didn't specify a trailing \ or / in the recording path setting, add that as that's critical to mapping the path correctly
            if(rec.find("\\") != -1):
                if(rec.rfind("\\") != (len(rec)-1)):
                    rec = rec + "\\"
            elif(rec.find("/") != -1):
                if(rec.rfind("/") != (len(rec)-1)):
                    rec = rec + "/"
            return filepath.replace(rec, unc)

    return filepath
        
#Get the passed in argument from the addContextMenuItems() call in default.py
args = sys.argv[1].split("|")
if(args[0] in ["cancelrecording","addfavorite","removefavorite","record","setwatched","clearwatched","setarchived","cleararchived"]):
    sageApiUrl = args[1]
    urllib.urlopen(sageApiUrl)
    if(args[0] == "record"):
        xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30113) + ")")
    elif(args[0] == "addfavorite"):
        xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30131) + ")")
    elif(args[0] == "removefavorite"):
        xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30132) + ")")
    elif(args[0] == "setwatched"):
        xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30133) + ")")
    elif(args[0] == "clearwatched"):
        xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30134) + ")")
    elif(args[0] == "setarchived"):
        xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30135) + ")")
    elif(args[0] == "cleararchived"):
        xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30136) + ")")
    xbmc.executebuiltin("Container.Refresh")
elif(args[0][0:6] == "delete" and args[0] != "deleteall"):
    firstApiCall = args[1]
    #Check what kind of delete command was sent
    deleteCommand = args[0].replace("delete","")
    if(deleteCommand != "" and deleteCommand != "wrongrecording"):
        secondApiCall = args[2]
        urllib.urlopen(firstApiCall)
        urllib.urlopen(secondApiCall)
    else:
        urllib.urlopen(firstApiCall)

    if(args[0] == "delete"):
        xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30112) + ")")
    xbmc.executebuiltin("Container.Refresh")
elif(args[0] in ["setallwatched","clearallwatched","deleteall"]):
    strUrl = args[1]
    showName = args[2]
    urlToShowEpisodes = strUrl + '/sagex/api?c=xbmc:GetMediaFilesForShowWithSubsetOfProperties&1=' + urllib2.quote(showName) + '&size=500&encoder=json'
    mfs = executeSagexAPIJSONCall(urlToShowEpisodes, "Result")
    print "***Getting ready to execute action '" + args[0] + "'; # of EPISODES for " + showName + "=" + str(len(mfs))
    for mfSubset in mfs:
        strMediaFileID = mfSubset.get("MediaFileID")
        if(args[0] == "setallwatched"):
            sageApiUrl = strUrl + '/sagex/api?command=SetWatched&1=mediafile:' + strMediaFileID
        elif(args[0] == "clearallwatched"):
            sageApiUrl = strUrl + '/sagex/api?command=ClearWatched&1=mediafile:' + strMediaFileID
        elif(args[0] == "deleteall"):
            sageApiUrl = strUrl + '/sagex/api?command=DeleteFile&1=mediafile:' + strMediaFileID
            
        urllib.urlopen(sageApiUrl)

    xbmc.executebuiltin("Container.Refresh")
elif(args[0] == "watchstream"):
    strUrl = args[1]
    mediaFileID = args[2]
    #streamingUrl = strUrl + "/stream/HTTPLiveStreamingPlaylist?MediaFileId=" + mediaFileID
    qualitySettingArray = [150, 240, 440, 640, 840, 1240, 1840]
    qualitySettingIndex = int(__settings__.getSetting("streaming_quality"))
    qualitySetting = qualitySettingArray[qualitySettingIndex]
    streamingUrl = strUrl + "/stream/HTTPLiveStreamingPlaylist?MediaFileId=%s&ConversionId=%s&Quality=%s" % (mediaFileID, str(int(time.time())), qualitySetting)
    #First check that the media streaming services plugin is installed
    validStreamingServicesPluginVersionFound = True
    #url = strUrl + '/sagex/api?command=GetInstalledPlugins&encoder=json'
    url = strUrl + '/sagex/api?c=xbmc:GetPluginVersion&1=mediastreaming&encoder=json'
    streamingServicesPluginVersion = executeSagexAPIJSONCall(url, "Result")

    if(streamingServicesPluginVersion == None or len(streamingServicesPluginVersion) == 0):
        print "SageTV not detected, or required plugins not installed"
        xbmcgui.Dialog().ok(__language__(30100),__language__(30101),__language__(30102),__language__(30103))
        validStreamingServicesPluginVersionFound = False
        
    print "***SageTV mediastreaming plugin version installed=" + streamingServicesPluginVersion
    if(streamingServicesPluginVersion == ""):
        xbmcgui.Dialog().ok(__language__(30104),__language__(30138) + " " + MIN_VERSION_STREAMING_SERVICES_PLUGIN_REQUIRED, __language__(30139),__language__(30140))
        validStreamingServicesPluginVersionFound = False
    if(comparePluginVersions(streamingServicesPluginVersion, MIN_VERSION_STREAMING_SERVICES_PLUGIN_REQUIRED) < 0):
        xbmcgui.Dialog().ok(__language__(30104),__language__(30138) + " " + MIN_VERSION_STREAMING_SERVICES_PLUGIN_REQUIRED, __language__(30108) + " " + streamingServicesPluginVersion,__language__(30141) + " " + MIN_VERSION_STREAMING_SERVICES_PLUGIN_REQUIRED)
        validStreamingServicesPluginVersionFound = False

    if(validStreamingServicesPluginVersionFound):
        print "**Attempting to playback stream of recording; streaming URL=" + streamingUrl
        xbmc.executebuiltin('PlayMedia("%s")' % streamingUrl)
elif(args[0] == "watchnow"):
    xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30114) + ")")
    strUrl = args[1]
    airingID = args[2]    
    sageApiUrl = strUrl + '/sagex/api?command=Record&1=airing:' + airingID
    
    #temp code to try to get the current listiem playing
    #path = xbmc.getInfoLabel('ListItem.FileNameAndPath')
    #print "pathhhhhhhhh=" + str(path)

    isRecording = False
    minWait = 1
    maxWait = 8

    #Schedule the show to be recorded
    urllib.urlopen(sageApiUrl)

    #Wait until a mediafile is created (and if one isn't after a period of time, consider it a failure)
    sageApiUrl = strUrl + '/sagex/api?command=GetCurrentlyRecordingMediaFiles&1=&encoder=json'
    wait = minWait
    while not isRecording and wait <= maxWait:
        print "Checking if recording has started for airingid=" + airingID
        sleep(wait)
        wait *= 2
        mfs = executeSagexAPIJSONCall(sageApiUrl, "Result")
        for mf in mfs:
            airing = mf.get("Airing")
            recordingAiringID = str(airing.get("AiringID"))
            print "recordingAiringID=" + recordingAiringID
            if (recordingAiringID == airingID):
                isRecording = True
                print "Recording for airingid=%s has started" % airingID
                break

    #If a mediafile is found, play it
    if isRecording:
        sageApiUrl = strUrl + '/sagex/api?command=GetMediaFileForAiring&1=airing:%s&encoder=json' % airingID
        mf = executeSagexAPIJSONCall(sageApiUrl, "MediaFile")
        mediaFileID = str(mf.get("MediaFileID"))
        currentSize = 0
        tries = 0
        maxTries = 10
        minSizeNeededToStartPlaybackInBytes = 1000000
        sageApiUrl = strUrl + '/sagex/api?command=GetSize&1=mediafile:%s&encoder=json' % mediaFileID
        while(currentSize < minSizeNeededToStartPlaybackInBytes and tries <= maxTries):
            currentSize = executeSagexAPIJSONCall(sageApiUrl, "Result")
            print "Current playback size=" + str(currentSize)
            if(currentSize > minSizeNeededToStartPlaybackInBytes):
                break
            sleep(1)
            tries = tries+1
        if(currentSize < minSizeNeededToStartPlaybackInBytes):
            # if the mediafile is not growing fast enough and we passed the max tries, playback has failed
            xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30121) + ")")
        else:
            strFilepath = mf.get("SegmentFiles")[0]
            print "****GETTING READY TO PLAYBACK LIVE TV WITHIN THE SAGETV ADDON****"
            print "**File path from SageTV: " + strFilepath
            mappedFilepath = filemap(strFilepath)
            print "**Mapped path which will be passed in to XBMC's PlayMedia call: " + mappedFilepath
            print "**Attempting to playback live tv; mediafileid=%s with size=%s at strFilepath=%s" % (mediaFileID, str(currentSize), mappedFilepath)
            xbmc.sleep(5000)
            xbmc.executebuiltin('PlayMedia("%s")' % filemap(strFilepath))
    else:
        xbmc.executebuiltin("Notification(" + __language__(30111) + "," + __language__(30115) + ")")
        print "NOTHING IS RECORDING"
        #return None
else:
	print "INVALID ARG PASSED IN TO CONTEXTMENUACTIONS.PY (sys.argv[1]=" + sys.argv[1]


