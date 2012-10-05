import urllib,urllib2,re
import xbmc,xbmcplugin,xbmcgui,xbmcaddon
from time import sleep
import simplejson as json

__settings__ = xbmcaddon.Addon(id='plugin.video.sagetv')
__language__ = __settings__.getLocalizedString
sage_mac = __settings__.getSetting("sage_mac")


DEFAULT_CHARSET = 'utf-8'

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
        
#Get the passed in argument from the addContextMenuItems() call in default.py
args = sys.argv[1].split("|")
if(args[0] in ["delete","cancelrecording","removefavorite","record"]):
    sageApiUrl = args[1]
    urllib.urlopen(sageApiUrl)
    if(args[0] == "delete"):
        xbmc.executebuiltin("Notification(" + __language__(21011) + "," + __language__(21012) + ")")
    elif(args[0] == "record"):
        xbmc.executebuiltin("Notification(" + __language__(21011) + "," + __language__(21013) + ")")
    xbmc.executebuiltin("Container.Refresh")
elif(args[0] == "watchnow"):
    xbmc.executebuiltin("Notification(" + __language__(21011) + "," + __language__(21014) + ")")
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
            xbmc.executebuiltin("Notification(" + __language__(21011) + "," + __language__(21021) + ")")
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
        xbmc.executebuiltin("Notification(" + __language__(21011) + "," + __language__(21015) + ")")
        print "NOTHING IS RECORDING"
        #return None
else:
	print "INVALID ARG PASSED IN TO CONTEXTMENUACTIONS.PY (sys.argv[1]=" + sys.argv[1]


