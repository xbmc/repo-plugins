import sys
import os
import urllib
import urllib2
import cookielib
import time
import blowfish
import hashlib 
import base64
import re
import json
from xml.dom import minidom
from subprocess import Popen, PIPE, STDOUT

import xbmcplugin, xbmcgui
import xbmcaddon

import pprint

def loadPage(url):
    print url
    headers = {
      'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.0; en-GB; rv:1.8.1.12) Gecko/20100101 Firefox/11.0',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'Accept-Encoding': 'gzip, deflate',
      'Accept-Language': 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3',
      'Cache-Control': 'max-age=0',
      'Connection': 'keep-alive'
    }
 
    request = urllib2.Request(url, None, headers)
    response = urllib2.urlopen(request)
    cj.save(COOKIEFILE,True)
    return response.read()

def createRnd():
    return int(time.time()*1000)

def getSessionIdFromCookieJar(cookieJar):
    for cookie in cookieJar:
        if cookie.name == "JSESSIONID":
            return cookie.value
    return None

def readTag(tag,dom):
    try:
      dom = dom.getElementsByTagName(tag)[0].firstChild;
      return unicode(dom.data);
    except:
      return "";

def decryptXML(data,secVersion, sec):
    key = getDecryptXMLKey(secVersion,sec)
    data = data.replace("\n","")
    data_decrypted = ""
    if key is not None:
        try:
            cipher = blowfish.Blowfish (key)
            cipher.initCBC()
            data = base64.decodestring(data)
            data_decrypted = cipher.decryptCBC(data)
            data_decrypted = data_decrypted[8:]
            data_decrypted = data_decrypted.replace("\x01","")
            data_decrypted = data_decrypted.replace("\x02","")
            data_decrypted = data_decrypted.replace("\x03","")
            data_decrypted = data_decrypted.replace("\x04","")
            data_decrypted = data_decrypted.replace("\x05","")
            data_decrypted = data_decrypted.replace("\x06","")
            data_decrypted = data_decrypted.replace("\x07","")
            data_decrypted = data_decrypted.replace("\x08","")
        except:
            print "decrypting failed"
    return data_decrypted

def getDecryptXMLKey(secVersion,sec):
    keys = ('SceljyienIp2','iquafZadvaf9','EvadvouxUth5','HuWutTotaf1')
    for key in keys:
        if secVersion.lower() == hashlib.md5(sec+"/"+key).hexdigest():
            return key
    return None

def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

def addDirectoryItem(name, parameters={}, pic="", isfolder=True, contextCommands = None):
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    if contextCommands is not None:
        li.addContextMenuItems( contextCommands, True ) 
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=isfolder)

def mainPage():
    url = defaultChannel % (getSessionIdFromCookieJar(cj),createRnd())
    addDirectoryItem(addon.getLocalizedString(30004), {"action" : "searchVideo", "link": url})
    
    url = defaultChannel % (getSessionIdFromCookieJar(cj),createRnd())
    addDirectoryItem(addon.getLocalizedString(30005), {"action" : "showChannel", "link": url})
    
    url = listChannels % (getSessionIdFromCookieJar(cj),"mood",createRnd())
    addDirectoryItem(addon.getLocalizedString(30006), {"action" : "showChannels", "link": url})
    url = listChannels % (getSessionIdFromCookieJar(cj),"genre",createRnd())
    addDirectoryItem(addon.getLocalizedString(30007), {"action" : "showChannels", "link": url})
    url = listChannels % (getSessionIdFromCookieJar(cj),"special",createRnd())
    addDirectoryItem(addon.getLocalizedString(30008), {"action" : "showChannels", "link": url})
    
    xbmcplugin.endOfDirectory(thisPlugin)

def showChannel(url):
    xmlPage = loadPage(url)
    xmlDom = minidom.parseString(xmlPage);
    
    videoList = []
    
    #Get Videos
    for videoDom in xmlDom.getElementsByTagName("video"):
        videoInfo = getVideoInfo(videoDom)
        videoList.append(videoInfo)
    
    playMore = "false"
    if xmlDom.getElementsByTagName("channel")[0].getAttribute("more") == "true":
        playMore = "true"
    
    addDirectoryItem(addon.getLocalizedString(30000), {"action" : "streamVideos", "link": json.dumps(videoList), "playMore":playMore}, "", False)

    #Add links
    for videoInfo in videoList:
        title = videoInfo['title']
        parameters =  {"action" : "playVideo", "link": videoInfo['url'], "title":videoInfo['title'], "image":videoInfo['image']}
        image = videoInfo['image']
        commands = []
        commands.append(( addon.getLocalizedString(30002), "XBMC.Container.Update(%s?action=%s&link=%s)" % ( sys.argv[0],  "moreLikeThis", videoInfo['id'] )))
        commands.append(( addon.getLocalizedString(30003),"XBMC.Container.Update(%s?action=%s&link=%s)" % ( sys.argv[0],  "downloadVideo", videoInfo['id'] )))
        addDirectoryItem(title, parameters, image, False, commands)
    
    #Add more Link
    if playMore == "true":
        channelUrl = more % (getSessionIdFromCookieJar(cj),createRnd())
        addDirectoryItem(addon.getLocalizedString(30001), {"action" : "showChannel", "link": channelUrl})
    
    xbmcplugin.endOfDirectory(thisPlugin)

def getVideoInfo(videoDom):
    id = videoDom.getAttribute("id")
    artist = readTag("artist",videoDom)
    title = readTag("title",videoDom)
    image = readTag("image",videoDom)
    
    
    streamInfo = None
    streamInfoHQ = None
    
    #StreamToken
    streamTokenDom = videoDom.getElementsByTagName("streamToken")[0]
    streamToken = streamTokenDom.firstChild.data
    streamTokenSecVersion = streamTokenDom.getAttribute("secVersion")
    streamTokenSec = streamTokenDom.getAttribute("sec")
    
    x = 0
    while x < len(videoDom.getElementsByTagName("url")):
        #Url
        streamUrlDom = videoDom.getElementsByTagName("url")[x]
        streamUrl = streamUrlDom.firstChild.data
        streamUrlSecVersion = streamUrlDom.getAttribute("secVersion")
        streamUrlSec = streamUrlDom.getAttribute("sec")
        
        print streamUrlDom.getAttribute("qualityName")
        
        if streamUrlDom.getAttribute("qualityName") == "highHQ":
            streamInfoHQ = (streamUrl,streamUrlSecVersion,streamUrlSec)
        
        if streamUrlDom.getAttribute("qualityName") == "lowLQ" and addon.getSetting('select_quality') == "niedrig":
            streamInfo = (streamUrl,streamUrlSecVersion,streamUrlSec)
            
        if streamUrlDom.getAttribute("qualityName") == "HD720p" and addon.getSetting('select_quality') == "beste":
            streamInfo = (streamUrl,streamUrlSecVersion,streamUrlSec)
        
        x = x+1
    
    if streamInfo is None:
        streamInfo = streamInfoHQ
    
    streamUrlDec = decryptXML(streamInfo[0],streamInfo[1],streamInfo[2])
    streamTokenDec = decryptXML(streamToken,streamTokenSecVersion,streamTokenSec)

    streamUrlDec = streamUrlDec.replace("http://video.tape.tv","mp4:tapetv")
    streamUrlDec = streamUrlDec.replace("http://video2.tape.tv","mp4:tapetv")
    
    videoTitle = unicode(artist + " - " + title).encode('utf-8')
    videoUrl = "rtmpe://cp68509.edgefcs.net/ondemand?auth=%s&aifp=v001" % (streamTokenDec)
    videoUrl = videoUrl + " playpath=%s" % (streamUrlDec)
    
    return { "title":videoTitle, "url":videoUrl, "image":image, "id":id }
    
def showChannels(url):
    xmlPage = loadPage(url)
    xmlDom = minidom.parseString(xmlPage);
    
    print getSessionIdFromCookieJar(cj)
    
    for channelDom in xmlDom.getElementsByTagName("channel"):
        id = channelDom.getAttribute("id")
        displayName = readTag("displayName",channelDom)
        image = readTag("url",channelDom.getElementsByTagName("image")[0])
        url = getChannel % (getSessionIdFromCookieJar(cj),id,createRnd())
        addDirectoryItem(displayName, {"action" : "showChannel", "link": url},image)
    xbmcplugin.endOfDirectory(thisPlugin)

def playVideo(videoUrl, videoTitle ="", videoImage=""):
    videoUrl = videoUrl.replace("+"," ")
    videoTitle = videoTitle.replace("+"," ")
    item = xbmcgui.ListItem(videoTitle,iconImage="DefaultFolder.png", thumbnailImage=videoImage)
    player.play(videoUrl, item)   
    while player.is_active:
        player.sleep(100)

def searchVideo():
    keyboard = xbmc.Keyboard("")
    keyboard.doModal();
    searchString = keyboard.getText()
    searchString = searchString.decode('UTF-8')
    searchString = searchString.replace( u'\xf6',"%F6")
    searchString = searchString.replace( u'\xe4',"%E4")
    searchString = searchString.replace( u'\xfc',"%FC")
    searchString = searchString.replace( u'\xdf',"%DF")
    searchUrl = search % (getSessionIdFromCookieJar(cj),searchString,createRnd())
    
    xmlPage = loadPage(searchUrl)
    xmlDom = minidom.parseString(xmlPage);
    
    for videoDom in xmlDom.getElementsByTagName("video"):
        #Info
        id = videoDom.getAttribute("id")
        artist = readTag("artist",videoDom)
        title = readTag("title",videoDom)
        image = readTag("image",videoDom)
        videoTitle = unicode(artist + " - " + title).encode('utf-8')
        commands = []
        commands.append(( addon.getLocalizedString(30002), "XBMC.Container.Update(%s?action=%s&link=%s)" % ( sys.argv[0],  "moreLikeThis", id )))
        commands.append(( addon.getLocalizedString(30003),"XBMC.Container.Update(%s?action=%s&link=%s)" % ( sys.argv[0],  "downloadVideo", id )))
        addDirectoryItem(videoTitle, {"action" : "loadVideo", "link": id, "title":videoTitle}, image, False, commands)
    xbmcplugin.endOfDirectory(thisPlugin)

def loadVideo(id):
    videoInfo = loadVideoInfo(id)
    playVideo(videoInfo['url'],videoInfo['title'],videoInfo['image'])
    
def loadVideoInfo(id):
    url = searchPLay % (getSessionIdFromCookieJar(cj),id,createRnd())
    
    xmlPage = loadPage(url)
    xmlDom = minidom.parseString(xmlPage);
    
    videoDom = xmlDom.getElementsByTagName("video")[0]
    videoInfo = getVideoInfo(videoDom)
    
    return videoInfo

def streamVideos(link,playMore):
    link = link.replace("+"," ")
    
    videoList = json.loads(link)
    
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO);
    playlist.clear();
    
    #Link parsen
    for videoInfo in videoList:        
        playListInfo.append(videoInfo)
        
        listItem = xbmcgui.ListItem(videoInfo['title'],iconImage="DefaultFolder.png", thumbnailImage=videoInfo['image']);
        playlist.add(url=videoInfo['url'], listitem=listItem)  
    
    player.play(playlist, xbmcgui.ListItem("playlist"))
    player.setPlaylist(playlist)
    
    if playMore == "true":
        player.setPlayMore(True)
        
    player.setPlayMoreLike(True)
    
    
    channelTime = 0
    while player.is_active:
        player.sleep(100)
        channelTime = channelTime+1
        player.setVideoTime(player.getVideoTime()+1)
        if not channelTime%100:
            playListPosition = playlist.getposition()
            videoId = playListInfo[playListPosition]['id']
            sendHearbeat(videoId, player.getVideoTime(), channelTime, playListPosition)

def sendHearbeat(videoId, videoTime, channelTime, videoCount):
    url = heartbeat % (getSessionIdFromCookieJar(cj),videoId,(videoTime/10),(channelTime/10),(channelTime/10),videoCount,videoCount,createRnd())
    loadPage(url)

def loadMoreVideos(playlist, moreLike = False):
    if moreLike:
        playListPosition = playlist.getposition()
        videoId = playListInfo[playListPosition]['id']
        url = moreLikeThis % (getSessionIdFromCookieJar(cj),videoId,createRnd())
    else:
        url = moreLink % (getSessionIdFromCookieJar(cj),createRnd())
    
    xmlPage = loadPage(url)
    xmlDom = minidom.parseString(xmlPage);
    
    videoList = []
    
    for videoDom in xmlDom.getElementsByTagName("video"):
        videoInfo = getVideoInfo(videoDom)
        videoList.append(videoInfo)
    
    for videoInfo in videoList:
        playListInfo.append(videoInfo)

        listItem = xbmcgui.ListItem(videoInfo['title'],iconImage="DefaultFolder.png", thumbnailImage=videoInfo['image']);
        playlist.add(url=videoInfo['url'], listitem=listItem) 

def showMoreLikeThis(id):
    url = moreLikeThis % (getSessionIdFromCookieJar(cj),id,createRnd())
    showChannel(url)

def downloadVideo(id):
    #THX to: http://code.google.com/p/nibor-xbmc-repo/source/browse/trunk/plugin.video.4od/default.py
    videoInfo = loadVideoInfo(id)
    filenamePos = videoInfo['url'].rfind("/")+1
    defFilename = videoInfo['url'][filenamePos:]
    
    url = []
    playpathPos = videoInfo['url'].find(" playpath=")
    url.append(videoInfo['url'][:playpathPos])
    url.append(videoInfo['url'][playpathPos+len(" playpath="):])
    
    # Download
    # Ensure rtmpdump has been located
    rtmpdump_path = addon.getSetting('rtmpdump_path')
    if ( rtmpdump_path is '' ):
        d = xbmcgui.Dialog()
        d.ok('Download Error','You have not located your rtmpdump executable.\n Please update the addon settings and try again.','','')
        addon.openSettings(sys.argv[ 0 ])
        return
                        
    # Ensure default download folder is defined
    downloadFolder = addon.getSetting('download_folder')
    if downloadFolder is '':
        d = xbmcgui.Dialog()
        d.ok('Download Error','You have not set the default download folder.\n Please update the addon settings and try again.','','')
        addon.openSettings(sys.argv[ 0 ])
        return
                        
    filename = defFilename
                                                                
    savePath = os.path.join( "T:"+os.sep, downloadFolder, filename )
    cmdline = CreateRTMPDUMPCmd( rtmpdump_path, url, savePath ) 
    xbmc.executebuiltin('XBMC.Notification(tape.tv,Starte Download: %s)' % filename)
    p = Popen( cmdline, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT )
    x = p.stdout.read()
                        
    xbmc.executebuiltin("XBMC.Notification(Download Finished!,"+filename+",2000)")
    return

def CreateRTMPDUMPCmd( rtmpdump_path, url, savePath ):
        args = [
                                rtmpdump_path,
                                "-r", '"%s"' % url[0],
                                "-y", '"%s"' % url[1],
                                "-o", '"%s"' % savePath,
                                "--verbose"
                                ]
        cmdline = ' '.join(args)
                
        return cmdline

class MyPlayer(xbmc.Player) :
    def __init__ (self):
        self.is_active = True
        self.playMore = False
        self.playMoreLike = False
        self.playList = None
        self.videoTime = 0
        xbmc.Player.__init__(self)
    
    def setPlayMore(self,playMore):
        self.playMore = playMore
    
    def setPlayMoreLike(self,playMoreLike):
        self.playMoreLike = playMoreLike
        
    def setPlaylist(self,playList):
        self.playList = playList

    def setVideoTime(self,videoTime):
        self.videoTime = videoTime

    def getVideoTime(self):
        return self.videoTime

    def onPlayBackEnded(self):
        self.is_active = False
        
    def onPlayBackStopped(self):
        self.is_active = False
        
    def onPlayBackStarted(self):
        self.videoTime = 0
        if self.playMore:
            if self.playList.__len__()-self.playList.getposition()<=4:
                loadMoreVideos(self.playList)
        elif self.playMoreLike:
            loadMoreVideos(self.playList,True)
    
    def sleep(self, s):
        xbmc.sleep(s) 

player=MyPlayer()
  
playListInfo = []
  
pluginName="plugin.video.tapetv"

#Settings laden
addon = xbmcaddon.Addon(pluginName)
action = addon.getSetting( 'select_action' )

#Cookie
scriptDataPath = "special://profile/addon_data/"+pluginName
scriptDataPath = xbmc.translatePath(scriptDataPath)
COOKIEFILE = os.path.join(scriptDataPath,'cookies.lwp')
if not os.path.exists(scriptDataPath):
    os.makedirs(scriptDataPath)

cj = cookielib.LWPCookieJar()

if os.path.isfile(COOKIEFILE):
    cj.load(COOKIEFILE,True)

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)  

thisPlugin = int(sys.argv[1])

baseUrl = "http://www.tape.tv/"

#Geoip erkennen
req = urllib2.Request(baseUrl)
response = urllib2.urlopen(req)
cj.save(COOKIEFILE,True)
if baseUrl != response.geturl():
    baseUrl = response.geturl()
    baseUrl = "http://www.tape.tv/telly/geoip"
    telly = "geoip"
    page = loadPage(baseUrl)
else:
    telly = "tapetv"
    page = response.read()
    
pageDomain = re.compile("&amp;domain=(.*?)&amp;").search(page).group(1)

defaultChannel = "http://"+pageDomain+"/tapeMVC/tape/channel/defaultChannel;jsessionid=%s?telly="+telly+"&rnd=%s"

listChannels = "http://"+pageDomain+"/tapeMVC/tape/channel/listChannels;jsessionid=%s?telly="+telly+"&type=%s&rnd=%s"
getChannel = "http://"+pageDomain+"/tapeMVC/tape/channel/getChannel;jsessionid=%s?telly="+telly+"&channelId=%s&rnd=%s"

more = "http://"+pageDomain+"/tapeMVC/tape/channel/more;jsessionid=%s?telly="+telly+"&rnd=%s"
moreLink = "http://"+pageDomain+"/tapeMVC/tape/channel/more;jsessionid=%s?telly="+telly+"&rnd=%s"
moreLikeThis = "http://"+pageDomain+"/tapeMVC/tape/channel/moreLikeThis;jsessionid=%s?telly="+telly+"&videoId=%s&rnd=%s"

search = "http://"+pageDomain+"/tapeMVC/tape/search/search;jsessionid=%s?telly="+telly+"&artistOrTitle=%s&origin=search&rnd=%s"
searchPLay = "http://"+pageDomain+"/tapeMVC/tape/search/play;jsessionid=%s?telly="+telly+"&videoId=%s&origin=search&rnd=%s"

heartbeat = "http://"+pageDomain+"/tapeMVC/tape/notify/heartBeat;jsessionid=%s?telly="+telly+"&videoId=%s&videoTime=%s&channelTime=%s&globalTime=%s&channelCounter=%s&globalCounter=%s&rnd=%s"

if not sys.argv[2]:
    mainPage()
else:
    params = get_params()
    if params['action'] == "showChannel":
        showChannel(urllib.unquote(params['link']))
    elif params['action'] == "showChannels":
        showChannels(urllib.unquote(params['link']))
    elif params['action'] == "playVideo":
        playVideo(urllib.unquote(params['link']),urllib.unquote(params['title']),urllib.unquote(params['image']))
    elif params['action'] == "searchVideo":
        searchVideo()
    elif params['action'] == "streamVideos":
        streamVideos(urllib.unquote(params['link']),params['playMore'])
    elif params['action'] == "loadVideo":
        loadVideo(urllib.unquote(params['link']))
    elif params['action'] == "moreLikeThis":
        showMoreLikeThis(urllib.unquote(params['link']))
    elif params['action'] == "downloadVideo":
        downloadVideo(urllib.unquote(params['link']))
    else:
        mainPage()
