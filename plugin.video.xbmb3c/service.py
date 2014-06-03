import xbmc
import xbmcgui
import xbmcaddon
import urllib
import httplib
import os
import time
import requests

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

__cwd__ = xbmcaddon.Addon(id='plugin.video.xbmb3c').getAddonInfo('path')
__addon__       = xbmcaddon.Addon(id='plugin.video.xbmb3c')
__language__     = __addon__.getLocalizedString
BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) )
sys.path.append(BASE_RESOURCE_PATH)
base_window = xbmcgui.Window( 10000 )

from InfoUpdater import InfoUpdaterThread
from NextUpItems import NextUpUpdaterThread
from RandomItems import RandomInfoUpdaterThread
from BackgroundLoader import BackgroundRotationThread
from ThemeMusic import ThemeMusicThread
from RecentItems import RecentInfoUpdaterThread
from InProgressItems import InProgressUpdaterThread
from WebSocketClient import WebSocketThread
from ClientInformation import ClientInformation
from MenuLoad import LoadMenuOptionsThread
from ImageProxy import MyHandler
from ImageProxy import ThreadingHTTPServer

_MODE_BASICPLAY=12

def getAuthHeader():
    addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
    deviceName = addonSettings.getSetting('deviceName')
    deviceName = deviceName.replace("\"", "_") # might need to url encode this as it is getting added to the header and is user entered data
    clientInfo = ClientInformation()
    txt_mac = clientInfo.getMachineId()
    version = clientInfo.getVersion()  
    userid = xbmcgui.Window( 10000 ).getProperty("userid")
    authString = "MediaBrowser UserId=\"" + userid + "\",Client=\"XBMC\",Device=\"" + deviceName + "\",DeviceId=\"" + txt_mac + "\",Version=\"" + version + "\""
    headers = {'Accept-encoding': 'gzip', 'Authorization' : authString}
    xbmc.log("XBMB3C Authentication Header : " + str(headers))
    return headers 


# start some worker threads

newInProgressThread = None
if __addon__.getSetting('useInProgressUpdater') == "true":
    newInProgressThread = InProgressUpdaterThread()
    newInProgressThread.start()
else:
    xbmc.log("XBMB3C Service InProgressUpdater Disabled")
  
newRecentInfoThread = None
if __addon__.getSetting('useRecentInfoUpdater') == "true":
    newRecentInfoThread = RecentInfoUpdaterThread()
    newRecentInfoThread.start()
else:
    xbmc.log("XBMB3C Service RecentInfoUpdater Disabled")    

newRandomInfoThread = None    
if __addon__.getSetting('useRandomInfo') == "true":
    newRandomInfoThread = RandomInfoUpdaterThread()
    newRandomInfoThread.start()
else:
    xbmc.log("XBMB3C Service RandomInfo Disabled")        

newNextUpThread = None
if __addon__.getSetting('useNextUp') == "true":
    newNextUpThread = NextUpUpdaterThread()
    newNextUpThread.start()
else:
    xbmc.log("XBMB3C Service NextUp Disabled")     

newWebSocketThread = None
if __addon__.getSetting('useWebSocketRemote') == "true":
    newWebSocketThread = WebSocketThread()
    newWebSocketThread.start()
else:
    xbmc.log("XBMB3C Service WebSocketRemote Disabled")

newMenuThread = None
if __addon__.getSetting('useMenuLoader') == "true":
    newMenuThread = LoadMenuOptionsThread()
    newMenuThread.start()
else:
    xbmc.log("XBMB3C Service MenuLoader Disabled")

backgroundUpdaterThread = None    
if __addon__.getSetting('useBackgroundLoader') == "true":
    backgroundUpdaterThread = BackgroundRotationThread()
    backgroundUpdaterThread.start()
else:
    xbmc.log("XBMB3C Service BackgroundLoader Disabled")
    
newThemeMusicThread = None    
if __addon__.getSetting('useThemeMusic') == "true":
    newThemeMusicThread = ThemeMusicThread()
    newThemeMusicThread.start()
else:
    xbmc.log("XBMB3C Service ThemeMusic Disabled")

newInfoThread = None    
if __addon__.getSetting('useInfoLoader') == "true":
    newInfoThread = InfoUpdaterThread()
    newInfoThread.start()
else:
    xbmc.log("XBMB3C Service InfoLoader Disabled")
    
###############################################
# start the image proxy server
###############################################

keepServing = True
def startImageProxyServer():

    xbmc.log("XBMB3 -> HTTP Image Proxy Server Starting")
    server = ThreadingHTTPServer(("",15001), MyHandler)
    
    while (keepServing):
        server.handle_request()
    
    xbmc.log("XBMB3 -> HTTP Image Proxy Server EXITING")
    
Thread(target=startImageProxyServer).start()

#################################################################################################

def deleteItem (url):
    return_value = xbmcgui.Dialog().yesno(__language__(30091),__language__(30092))
    if return_value:
        xbmc.log('Deleting via URL: ' + url)
        progress = xbmcgui.DialogProgress()
        progress.create(__language__(30052), __language__(30053))
        resp = requests.delete(url, data='', headers=getAuthHeader())
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
    xbmc.log('XBMB3C Service -> Marking watched via: ' + url)
    resp = requests.post(url, data='', headers=getAuthHeader())
    
def markUnWatched(url):
    xbmc.log('XBMB3C Service -> Marking watched via: ' + url)
    resp = requests.delete(url, data='', headers=getAuthHeader())    

def setPosition (url, method):
    xbmc.log('XBMB3C Service -> Setting position via: ' + url)
    if method == 'POST':
        resp = requests.post(url, data='', headers=getAuthHeader())
    elif method == 'DELETE':
        resp = requests.delete(url, data='', headers=getAuthHeader())
        
def hasData(data):
    if(data == None or len(data) == 0 or data == "None"):
        return False
    else:
        return True
        
def stopAll(played_information):

    if(len(played_information) == 0):
        return 
        
    addonSettings = xbmcaddon.Addon(id='plugin.video.xbmb3c')
    xbmc.log ("XBMB3C Service -> played_information : " + str(played_information))
    
    for item_url in played_information:
        data = played_information.get(item_url)
        if(data != None):
            xbmc.log ("XBMB3C Service -> item_url  : " + item_url)
            xbmc.log ("XBMB3C Service -> item_data : " + str(data))
            
            watchedurl = data.get("watchedurl")
            positionurl = data.get("positionurl")
            deleteurl = data.get("deleteurl")
            runtime = data.get("runtime")
            currentPossition = data.get("currentPossition")
            item_id = data.get("item_id")
            
            if(currentPossition != None and hasData(runtime) and hasData(positionurl) and hasData(watchedurl)):
                runtimeTicks = int(runtime)
                xbmc.log ("XBMB3C Service -> runtimeticks:" + str(runtimeTicks))
                percentComplete = (currentPossition * 10000000) / runtimeTicks
                markPlayedAt = float(addonSettings.getSetting("markPlayedAt")) / 100    

                xbmc.log ("XBMB3C Service -> Percent Complete:" + str(percentComplete) + " Mark Played At:" + str(markPlayedAt))
                if (percentComplete > markPlayedAt):
                
                    gotDeleted = 0
                    if(deleteurl != None and deleteurl != ""):
                        xbmc.log ("XBMB3C Service -> Offering Delete:" + str(deleteurl))
                        gotDeleted = deleteItem(deleteurl)
                        
                    if(gotDeleted == 0):
                        setPosition(positionurl + '/Progress?PositionTicks=0', 'POST')
                        if(newWebSocketThread != None):
                            newWebSocketThread.playbackStopped(item_id, str(0))
                        markWatched(watchedurl)
                else:
                    markUnWatched(watchedurl)
                    if(newWebSocketThread != None):
                        newWebSocketThread.playbackStopped(item_id, str(int(currentPossition * 10000000)))
                    setPosition(positionurl + '?PositionTicks=' + str(int(currentPossition * 10000000)), 'DELETE')
                    
    if(newNextUpThread != None):
        newNextUpThread.updateNextUp()
        
    if(backgroundUpdaterThread != None):
        backgroundUpdaterThread.updateActionUrls()
        
    played_information.clear()

class Service( xbmc.Player ):

    played_information = {}
    
    def __init__( self, *args ):
        xbmc.log("XBMB3C Service -> starting monitor service")
        self.played_information = {}
        pass

    def onPlayBackStarted( self ):
        # Will be called when xbmc starts playing a file
        
        stopAll(self.played_information)
        
        currentFile = xbmc.Player().getPlayingFile()
        
        WINDOW = xbmcgui.Window( 10000 )
        watchedurl = WINDOW.getProperty("watchedurl")
        deleteurl = WINDOW.getProperty("deleteurl")
        positionurl = WINDOW.getProperty("positionurl")
        runtime = WINDOW.getProperty("runtimeticks")
        item_id = WINDOW.getProperty("item_id")
        
        if(newWebSocketThread != None):
            newWebSocketThread.playbackStarted(item_id)
        
        if (watchedurl != "" and positionurl != ""):
        
            data = {}
            data["watchedurl"] = watchedurl
            data["deleteurl"] = deleteurl
            data["positionurl"] = positionurl
            data["runtime"] = runtime
            data["item_id"] = item_id
            self.played_information[currentFile] = data
            
            xbmc.log("XBMB3C Service -> ADDING_FILE : " + currentFile)
            xbmc.log("XBMB3C Service -> ADDING_FILE : " + str(self.played_information))

            # reset in progress possition
            setPosition(positionurl + '/Progress?PositionTicks=0', 'POST')

    def onPlayBackEnded( self ):
        # Will be called when xbmc stops playing a file
        xbmc.log("XBMB3C Service -> onPlayBackEnded")
        stopAll(self.played_information)

    def onPlayBackStopped( self ):
        # Will be called when user stops xbmc playing a file
        xbmc.log("XBMB3C Service -> onPlayBackStopped")
        stopAll(self.played_information)

monitor = Service()
lastProgressUpdate = datetime.today()
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
                    if(newWebSocketThread != None):
                        newWebSocketThread.sendProgressUpdate(item_id, str(int(playTime * 10000000)))
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
    xbmc.log("XBMB3C Service -> Tried to stop image proxy server but it was already stopped")

xbmc.log("XBMB3C Service -> Service shutting down")

