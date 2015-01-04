import xbmc
import xbmcgui
import xbmcaddon
import urllib
import httplib
import os
import time
import socket
import inspect
import sys
import threading
import json
from datetime import datetime
import xml.etree.ElementTree as xml

import mimetypes
from threading import Thread
from urlparse import parse_qs
from urllib import urlretrieve

from random import randint
import random
import urllib2

__settings__ = xbmcaddon.Addon(id='plugin.video.xbmb3c')
__cwd__ = xbmcaddon.Addon(id='plugin.video.xbmb3c').getAddonInfo('path')
__addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
__language__     = __addon__.getLocalizedString
BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
sys.path.append(BASE_RESOURCE_PATH)
base_window = xbmcgui.Window( 10000 )


from InfoUpdater import InfoUpdaterThread
from NextUpItems import NextUpUpdaterThread
from SuggestedItems import SuggestedUpdaterThread
from RandomItems import RandomInfoUpdaterThread
from ArtworkLoader import ArtworkRotationThread
from ThemeMedia import ThemeMediaThread
from RecentItems import RecentInfoUpdaterThread
from InProgressItems import InProgressUpdaterThread
from WebSocketClient import WebSocketThread
from ClientInformation import ClientInformation
from MenuLoad import LoadMenuOptionsThread
from ImageProxy import MyHandler
from ImageProxy import ThreadingHTTPServer
from PlaylistItems import PlaylistItemUpdaterThread
from DownloadUtils import DownloadUtils
from BackgroundData import BackgroundDataUpdaterThread
from Utils import PlayUtils
from SkinHelperThread import SkinHelperThread


downloadUtils = DownloadUtils()

newInProgressThread = None
newRecentInfoThread = None
newRandomInfoThread = None
newNextUpThread = None
newSuggestedThread = None
newWebSocketThread = None
newMenuThread = None
artworkRotationThread = None
newThemeMediaThread = None
newInfoThread = None
newPlaylistsThread = None
newBackgroundDataThread = None
logLevel = 0
try:
    logLevel = int(__settings__.getSetting('logLevel'))   
except:
    pass

def printDebug( msg, level = 1):
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


###########################################################################  
##Start of Service
###########################################################################
    
def ServiceEntryPoint():
    # auth the service
    try:
        downloadUtils.authenticate()
    except Exception, e:
        pass
    
    # start some worker threads
    skinHelperThread = SkinHelperThread()
    skinHelperThread.start()
    printDebug("[MB3 SkinHelper] Started... fetching background images now")

    
    if __addon__.getSetting('useInProgressUpdater') == "true":
        newInProgressThread = InProgressUpdaterThread()
        newInProgressThread.start()
    else:
        printDebug("XBMB3C Service InProgressUpdater Disabled")
      
    
    if __addon__.getSetting('useRecentInfoUpdater') == "true":
        newRecentInfoThread = RecentInfoUpdaterThread()
        newRecentInfoThread.start()
    else:
        printDebug("XBMB3C Service RecentInfoUpdater Disabled")    
    
      
    if __addon__.getSetting('useRandomInfo') == "true":
        newRandomInfoThread = RandomInfoUpdaterThread()
        newRandomInfoThread.start()
    else:
        printDebug("XBMB3C Service RandomInfo Disabled")        
    
    
    if __addon__.getSetting('useNextUp') == "true":
        newNextUpThread = NextUpUpdaterThread()
        newNextUpThread.start()
    else:
        printDebug("XBMB3C Service NextUp Disabled")    
        
    if __addon__.getSetting('useSuggested') == "true":
        newSuggestedThread = SuggestedUpdaterThread()
        newSuggestedThread.start()
    else:
        printDebug("XBMB3C Service Suggested Disabled")   
    
    if __addon__.getSetting('useWebSocketRemote') == "true":
        newWebSocketThread = WebSocketThread()
        newWebSocketThread.start()
    else:
        printDebug("XBMB3C Service WebSocketRemote Disabled")
    
    if __addon__.getSetting('useMenuLoader') == "true":
        newMenuThread = LoadMenuOptionsThread()
        newMenuThread.start()
    else:
        printDebug("XBMB3C Service MenuLoader Disabled")
    
    if __addon__.getSetting('useBackgroundLoader') == "true":
        artworkRotationThread = ArtworkRotationThread()
        artworkRotationThread.start()
    else:
        printDebug("XBMB3C Service BackgroundLoader Disabled")
           
    if __addon__.getSetting('useThemeMovies') == "true" or __addon__.getSetting('useThemeMusic') == "true":
        newThemeMediaThread = ThemeMediaThread()
        newThemeMediaThread.start()
    else:
        printDebug("XBMB3C Service ThemeMedia Disabled")
    
    if __addon__.getSetting('useInfoLoader') == "true":
        newInfoThread = InfoUpdaterThread()
        newInfoThread.start()
    else:
        printDebug("XBMB3C Service InfoLoader Disabled")
        
    if __addon__.getSetting('usePlaylistsUpdater') == "true":
        newPlaylistsThread = PlaylistItemUpdaterThread()
        newPlaylistsThread.start()
    else:
        printDebug("XBMB3C Service PlaylistsUpdater Disabled")
        
    if __addon__.getSetting('useBackgroundData') == "true":
        newBackgroundDataThread = BackgroundDataUpdaterThread()
        newBackgroundDataThread.start()
    else:
        printDebug("XBMB3C BackgroundDataUpdater Disabled")

    
    ###############################################
    # start the image proxy server
    ###############################################
    
    keepServing = True
    def startImageProxyServer():
    
        printDebug("XBMB3 -> HTTP Image Proxy Server Starting")
        server = ThreadingHTTPServer(("",15001), MyHandler)
        
        while (keepServing):
            server.handle_request()
        
        printDebug("XBMB3 -> HTTP Image Proxy Server EXITING")
        
    Thread(target=startImageProxyServer).start()
    
    monitor = Service()
    lastProgressUpdate = datetime.today()
    
    addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
    if socket.gethostname() != None and socket.gethostname() != '' and addonSettings.getSetting("deviceName") == 'XBMB3C':
        addonSettings.setSetting("deviceName", socket.gethostname())
    
    while not xbmc.abortRequested:
        if xbmc.Player().isPlaying():
            try:
                playTime = xbmc.Player().getTime()
                currentFile = xbmc.Player().getPlayingFile()
                
                if(monitor.played_information.get(currentFile) != None):
                    monitor.played_information[currentFile]["currentPossition"] = playTime
                
                # send update
                td = datetime.today() - lastProgressUpdate
                secDiff = td.seconds
                if(secDiff > 10):
                    if(monitor.played_information.get(currentFile) != None and monitor.played_information.get(currentFile).get("item_id") != None):
                        item_id =  monitor.played_information.get(currentFile).get("item_id")
                        #if(newWebSocketThread != None):
                            #newWebSocketThread.sendProgressUpdate(item_id, str(int(playTime * 10000000)))
                        reportPlayback(str(int(playTime * 10000000)))
                    lastProgressUpdate = datetime.today()
                
            except Exception, e:
                xbmc.log("XBMB3C Service -> Exception in Playback Monitor : " + str(e))
                pass
    
        xbmc.sleep(1000)
        xbmcgui.Window(10000).setProperty("XBMB3C_Service_Timestamp", str(int(time.time())))
        
    # stop the WebSocket client
    if(newWebSocketThread != None):
        newWebSocketThread.stopClient()
    
    # stop the image proxy
    keepServing = False
    try:
        requesthandle = urllib.urlopen("http://localhost:15001/?id=dummy&type=Primary", proxies={})
    except:
        printDebug("XBMB3C Service -> Tried to stop image proxy server but it was already stopped")
    
    printDebug("XBMB3C Service -> Service shutting down") 

def deleteItem (url):
    return_value = xbmcgui.Dialog().yesno(__language__(30091),__language__(30092))
    if return_value:
        printDebug('Deleting via URL: ' + url)
        progress = xbmcgui.DialogProgress()
        progress.create(__language__(30052), __language__(30053))
        downloadUtils.downloadUrl(url, type="DELETE")
        deleteSleep=0
        while deleteSleep<10:
            xbmc.sleep(1000)
            deleteSleep=deleteSleep+1
            progress.update(deleteSleep*10,__language__(30053))
        progress.close()
        xbmc.executebuiltin("Container.Refresh")
        return 1
    else:
        return 0
        
def markWatched(url):
    printDebug('XBMB3C Service -> Marking watched via: ' + url)
    downloadUtils.downloadUrl(url, type="DELETE")
    downloadUtils.downloadUrl(url, postBody="", type="POST")
       
def markUnWatched(url):
    printDebug('XBMB3C Service -> Marking watched via: ' + url)
    downloadUtils.downloadUrl(url, type="DELETE")

def stopTranscoding(url):
    printDebug('XBMB3C Service -> Stopping transcoding: ' + url)
    downloadUtils.downloadUrl(url, type="DELETE")

        
def hasData(data):
    if(data == None or len(data) == 0 or data == "None"):
        return False
    else:
        return True
        
def stopAll(played_information):

    if(len(played_information) == 0):
        return 
        
    addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
    printDebug("XBMB3C Service -> played_information : " + str(played_information))
    
    for item_url in played_information:
        data = played_information.get(item_url)
        if(data != None):
            printDebug("XBMB3C Service -> item_url  : " + item_url)
            printDebug("XBMB3C Service -> item_data : " + str(data))
            
            watchedurl = data.get("watchedurl")
            positionurl = data.get("positionurl")
            deleteurl = data.get("deleteurl")
            runtime = data.get("runtime")
            currentPossition = data.get("currentPossition")
            item_id = data.get("item_id")
            currentFile = data.get("currentfile")
          
            if(currentPossition != None and hasData(runtime) and hasData(positionurl) and hasData(watchedurl)):
                runtimeTicks = int(runtime)
                printDebug("XBMB3C Service -> runtimeticks:" + str(runtimeTicks))
                percentComplete = (currentPossition * 10000000) / runtimeTicks
                markPlayedAt = float(addonSettings.getSetting("markPlayedAt")) / 100    

                printDebug("XBMB3C Service -> Percent Complete:" + str(percentComplete) + " Mark Played At:" + str(markPlayedAt))
                stopPlayback(currentFile,str(int(currentPossition * 10000000)))
                if (percentComplete > markPlayedAt):
                    gotDeleted = 0
                    if(deleteurl != None and deleteurl != ""):
                        printDebug("XBMB3C Service -> Offering Delete:" + str(deleteurl))
                        gotDeleted = deleteItem(deleteurl)

    if(newNextUpThread != None):
        newNextUpThread.updateNextUp()
        
    if(artworkRotationThread != None):
        artworkRotationThread.updateActionUrls()
        
    played_information.clear()

    # stop transcoding - todo check we are actually transcoding?
    clientInfo = ClientInformation()
    txt_mac = clientInfo.getMachineId()
    url = ("http://%s:%s/mediabrowser/Videos/ActiveEncodings" % (addonSettings.getSetting('ipaddress'), addonSettings.getSetting('port')))  
    url = url + '?DeviceId=' + txt_mac
    stopTranscoding(url)
    
def stopPlayback(currentFile,positionTicks):
    addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
    WINDOW = xbmcgui.Window( 10000 )
    item_id = WINDOW.getProperty(currentFile+"item_id")
    audioindex = WINDOW.getProperty(currentFile+"AudioStreamIndex")
    subtitleindex = WINDOW.getProperty(currentFile+"SubtitleStreamIndex")
    playMethod = WINDOW.getProperty(currentFile+"playmethod")
    
    url = ("http://%s:%s/mediabrowser/Sessions/Playing/Stopped" % (addonSettings.getSetting('ipaddress'), addonSettings.getSetting('port')))  
        
    url = url + "?itemId=" + item_id

    url = url + "&canSeek=true"
    url = url + "&PlayMethod=" + playMethod
    url = url + "&QueueableMediaTypes=Video"
    url = url + "&MediaSourceId=" + item_id
    url = url + "&PositionTicks=" + positionTicks   
    if(audioindex != None and audioindex!=""):
      url = url + "&AudioStreamIndex=" + audioindex
        
    if(subtitleindex != None and subtitleindex!=""):
      url = url + "&SubtitleStreamIndex=" + subtitleindex
        
    downloadUtils.downloadUrl(url, postBody="", type="POST")
    
def reportPlayback(positionTicks):
    addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
    try:
        currentFile = xbmc.Player().getPlayingFile()
        WINDOW = xbmcgui.Window( 10000 )
        item_id = WINDOW.getProperty(currentFile+"item_id")
        
        # only report playback if xbmb3c has initiated the playback (item_id has value)
        if item_id != "":
            audioindex = WINDOW.getProperty(currentFile+"AudioStreamIndex")
            subtitleindex = WINDOW.getProperty(currentFile+"SubtitleStreamIndex")
            playMethod = WINDOW.getProperty(currentFile+"playmethod")
            
            url = ("http://%s:%s/mediabrowser/Sessions/Playing/Progress" % (addonSettings.getSetting('ipaddress'), addonSettings.getSetting('port')))  
                
            url = url + "?itemId=" + item_id

            url = url + "&canSeek=true"
            url = url + "&PlayMethod=" + playMethod
            url = url + "&QueueableMediaTypes=Video"
            url = url + "&MediaSourceId=" + item_id
            url = url + "&PositionTicks=" + positionTicks   
            if(audioindex != None and audioindex!=""):
              url = url + "&AudioStreamIndex=" + audioindex
                
            if(subtitleindex != None and subtitleindex!=""):
              url = url + "&SubtitleStreamIndex=" + subtitleindex
                
            downloadUtils.downloadUrl(url, postBody="", type="POST")
        
    except:
        pass
    
class Service( xbmc.Player ):

    played_information = {}
    
    def __init__( self, *args ):
        printDebug("XBMB3C Service -> starting monitor service")
        self.played_information = {}
        pass
    
    def onPlayBackStarted( self ):
        # Will be called when xbmc starts playing a file
        WINDOW = xbmcgui.Window( 10000 )
        stopAll(self.played_information)
        addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
        
        if xbmc.Player().isPlaying():
            currentFile = xbmc.Player().getPlayingFile()
            printDebug("XBMB3C Service -> onPlayBackStarted" + currentFile)
            
            watchedurl = WINDOW.getProperty(currentFile+"watchedurl")
            deleteurl = WINDOW.getProperty(currentFile+"deleteurl")
            positionurl = WINDOW.getProperty(currentFile+"positionurl")
            runtime = WINDOW.getProperty(currentFile+"runtimeticks")
            item_id = WINDOW.getProperty(currentFile+"item_id")
            audioindex = WINDOW.getProperty(currentFile+"AudioStreamIndex")
            subtitleindex = WINDOW.getProperty(currentFile+"SubtitleStreamIndex")
            playMethod = WINDOW.getProperty(currentFile+"playmethod")
            
            if(item_id == None or len(item_id) == 0):
                return
        
            url = ("http://%s:%s/mediabrowser/Sessions/Playing" % (addonSettings.getSetting('ipaddress'), addonSettings.getSetting('port')))  
            
            url = url + "?itemId=" + item_id

            url = url + "&canSeek=true"
            url = url + "&PlayMethod=" + playMethod
            url = url + "&QueueableMediaTypes=Video"
            url = url + "&MediaSourceId=" + item_id
            
            if(audioindex != None and audioindex!=""):
              url = url + "&AudioStreamIndex=" + audioindex
            
            if(subtitleindex != None and subtitleindex!=""):
              url = url + "&SubtitleStreamIndex=" + subtitleindex
            
            downloadUtils.downloadUrl(url, postBody="", type="POST")
            # if(newWebSocketThread != None):
              #   newWebSocketThread.playbackStarted(item_id)
            
            if (watchedurl != "" and positionurl != ""):
            
                data = {}
                data["watchedurl"] = watchedurl
                data["deleteurl"] = deleteurl
                data["positionurl"] = positionurl
                data["runtime"] = runtime
                data["item_id"] = item_id
                data['currentfile'] = currentFile
                self.played_information[currentFile] = data
                
                printDebug("XBMB3C Service -> ADDING_FILE : " + currentFile)
                printDebug("XBMB3C Service -> ADDING_FILE : " + str(self.played_information))

                # reset in progress possition
                #setPosition(positionurl + '/Progress?PositionTicks=0', 'POST')
                reportPlayback("0000000")

    def onPlayBackEnded( self ):
        # Will be called when xbmc stops playing a file
        printDebug("XBMB3C Service -> onPlayBackEnded")
        stopAll(self.played_information)

    def onPlayBackStopped( self ):
        # Will be called when user stops xbmc playing a file
        printDebug("XBMB3C Service -> onPlayBackStopped")
        stopAll(self.played_information)
