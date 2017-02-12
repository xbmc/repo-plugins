#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import os
import random
import xbmcplugin
import xbmcgui
import xbmcaddon,json,requests,cookielib,xbmcvfs

#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
addonID = 'plugin.video.nick_de'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
jrOnly = addon.getSetting("jrOnly") == "true"

useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
viewMode = str(addon.getSetting("viewID"))
translation = addon.getLocalizedString
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
iconJr = xbmc.translatePath('special://home/addons/'+addonID+'/iconJr.png')
iconNight = xbmc.translatePath('special://home/addons/'+addonID+'/iconnight.png')
urlMain = "http://www.nick.de"
urlMainJR = "http://www.nickjr.de"
urlMainnight ="http://www.nicknight.de"



profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")

    
    
opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')]


profile    = xbmc.translatePath( addon.getAddonInfo('profile') ).decode("utf-8")
temp       = xbmc.translatePath( os.path.join( profile, 'temp', '') ).decode("utf-8")

if not xbmcvfs.exists(temp):       
       xbmcvfs.mkdirs(temp)

cookie= os.path.join(temp,"cookie.jar")
cj = cookielib.LWPCookieJar();


def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    
def index():
    if jrOnly:
        nickJrMain()
    else:
        addDir(translation(30001), "", 'nickMain', icon)
        addDir(translation(30002), "", 'nickJrMain', iconJr)
        addDir(translation(30007), "", 'nightMain', iconNight)
        xbmcplugin.endOfDirectory(pluginhandle)

  
def getUrl(url,data="x",header="",cookies=1):
   
        try:
            cj.load(cookie,ignore_discard=True, ignore_expires=True)        
        except:
            pass        
        debug("Get Url: " +url)
        for cook in cj:
            debug(" Cookie :"+ str(cook))
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))        
        userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0"
        if header=="":
          opener.addheaders = [('User-Agent', userAgent)]        
        else:
          opener.addheaders = header        
        try:
          if data!="x" :
             content=opener.open(url,data=data).read()
          else:
             content=opener.open(url).read()
        except urllib2.HTTPError as e:
             #debug( e.code   )
             cc=e.read()  
             debug("Error : " +cc)
       
        opener.close()
        cj.save(cookie,ignore_discard=True, ignore_expires=True)
        return content
        

def nickMain():
    addDir(translation(30003), urlMain+"/videos", 'listVideos', icon)
    addDir(translation(30004), urlMain+"/videos", 'listShows', icon)
    xbmcplugin.endOfDirectory(pluginhandle)
    

def nickJrMain():
    addDir(translation(30003), "http://www.nickjr.de/data/videosStreamPage.json?&urlKey=&apiKey=de_global_Nickjr_web&adfree=&excludeIds=", 'listVideosJR', iconJr,page=1)
    addDir(translation(30004), urlMainJR+"/data/nav.json?propKey=paw-patrol&urlKey=pups-and-the-big-freeze-pups-save-a-basketbal&apiKey=de_global_Nickjr_web", 'listShowsJR', iconJr)
    xbmcplugin.endOfDirectory(pluginhandle)
    

def nightMain():
    addDir(translation(30004), urlMainnight, 'listShowsNight', iconNight)
    xbmcplugin.endOfDirectory(pluginhandle)

def listVideos(url):
    debug("listVideos URL: "+ url)
    content = opener.open(url).read()
    spl = content.split("class='fullepisode playlist-item'")
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match1 = re.compile("class='title'>(.+?)<", re.DOTALL).findall(entry)
        match2 = re.compile("class='subtitle'>(.*?)<", re.DOTALL).findall(entry)
        title = match1[0]
        if match2 and match2[0]:
            title = title+" - "+match2[0]
        title = cleanTitle(title)
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace("140x105","640x")
        match = re.compile("href='(.+?)'", re.DOTALL).findall(entry)
        url = match[0]
        if not urlMain in url:
          url=urlMain+url
        addLink(title, url, 'playVideo', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    


def listShows(url):
    content = opener.open(url).read()
    match = re.compile('<li class=\'item\'><a href="(.+?)".*?alt="(.+?)" src="(.+?)"', re.DOTALL).findall(content)
    for url, title, thumb in match:
        if url.startswith("/shows/"):
            title = title[:title.rfind(" - ")]
            title = cleanTitle(title)
            addDir(title, urlMain+url, 'listVideos', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)



def listShowsJR(url):
    debug ("listShowsJR :" +url)
    content = getUrl(url)
    struktur = json.loads(content)
    debug("---------")
    debug(struktur)
    for serie in struktur["main"]["propertyCarousel"]["sprites"]:
      urln=serie["url"]
      title=serie["title"]
      addDir(title, urlMainJR+urln, 'listSeriesJr', "")
    xbmcplugin.endOfDirectory(pluginhandle)

def listSeriesJr(url):
   content = getUrl(url)
   elemente=content.split('<b class="tooltip-title">')
   for element in elemente:
     if not "games" in element:
        try:
          element='<b class="tooltip-title">'+element
          debug("------")
          debug(element)
          title = re.compile('<b class="tooltip-title">(.+?)</b>', re.DOTALL).findall(element)[0]
          desc=re.compile('<p class="tooltip-description">(.+?)</p>', re.DOTALL).findall(element)[0]
          urln=urlMainJR+re.compile('<a href="(.+?)"', re.DOTALL).findall(element)[0]
          img=re.compile('<source srcset="(.+?)"', re.DOTALL).findall(element)[0]
          if "tile-episode-flag" in element:
            adding=" (Episode)"
          else:
            adding=""
          addLink(title+adding, urln, 'playVideoJR', img)
        except:
          pass
   xbmcplugin.endOfDirectory(pluginhandle)

def listShowsNight(url):
    xbmc.log("NICK :listShowsNight "+ url) 
    content = opener.open(url).read()
    content = content[content.find("<ul class='carouFredSel'>"):]
    content = content[:content.find("</ul>")]
    match = re.compile('<li class=\'item\'><a href="([^"]+)" target=""><img alt="([^"]+)" src="([^"]+)" title="" /></a></li>', re.DOTALL).findall(content)
    for element in match:        
        title = element[1]
        thumb = element[2]
        url = urlMainnight+element[0]
        addDir(title, url, 'playVideoJR', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideosJR(url,page=1):
    urln=url+"&page="+str(page)
    debug("listVideosJR URL: "+ urln)
    content=getUrl(urln)
    struktur = json.loads(content)
    for element in  struktur["stream"]:
        for element2 in element["items"]:
          try:
             mediatype=element2["data"]["mediaType"]
             url3=urlMainJR+element2["data"]["url"]
             img=element2["data"]["images"]["thumbnail"]["r1-1"]
             title=element2["data"]["title"]
             addLink(title, url3, 'playVideoJR', img)
          except:
             pass 
    addDir("Next", url, 'listVideosJR', "",page=int(page)+1)
    xbmcplugin.endOfDirectory(pluginhandle)             
    
def playVideoJR(url):
    content = getUrl(url)
    id = re.compile('data-contenturi="(.+?)"', re.DOTALL).findall(content)[0]
    url2="http://media.mtvnservices.com/pmt/e1/access/index.html?uri="+id+"&configtype=edge"
    header=[]
    header.append (('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0'))    
    header.append (('Referer', url))    
    content = getUrl(url2,header=header)
    debug("++++++++++")
    debug(content)
    debug("++++++++++")
    struktur = json.loads(content)
    streamurl=struktur["feed"]["items"][0]["group"]["content"]   
    content = getUrl(streamurl)
    video = re.compile('<src>(.+?)</src>', re.DOTALL).findall(content)[-1]
    video=video.replace("rtmpe","rtmp")
    listitem = xbmcgui.ListItem(path=video+" swfVfy=1 swfUrl=http://media.mtvnservices.com/edge/polyfill/polyfill-1.4.14.swf")
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    debug(content)


def listVideosnight(url):
    xbmc.log("NICK :listVideosnight url "+ url)
    content = opener.open(url).read()        
    if "<ol class='playlist'>" in content:
        content = content[content.find("<ol class='playlist'>"):]
        content = content[:content.find("</ol>")]                         
    spl = content.split("playlist-item' data-item-id")     
    for i in range(1, len(spl), 1):
        entry = spl[i]
        xbmc.log("NICK :listVideosnight "+ entry)
        match = re.compile("<p class='subtitle'>([^<]+)", re.DOTALL).findall(entry)
        title = match[-1]
        title = cleanTitle(title)
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]
        match = re.compile("href='(.+?)'", re.DOTALL).findall(entry)
        url = match[0]
        addLink(title, url, 'playVideo', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    

def playVideo(url):
    xbmc.log("NICK : "+ url) 
    content = opener.open(url).read()
    # data-mrss="http://api.mtvnn.com/v2/mrss.xml?uri=mgid:sensei:video:mtvnn.com:local_playlist-42c03a89f16e99f0d018"
    match1 = re.compile('data-mrss="([^"]+)"', re.DOTALL).findall(content)
    #mrss     : 'http://api.mtvnn.com/v2/mrss?uri=mgid:sensei:video:mtvnn.com:local_playlist-a3dff586129cb4d17dc5',
    match2 = re.compile('mrss[\s]*: \'([^\']+)\'', re.DOTALL).findall(content)                        
    match3 = re.compile("mrss[\s]*:[^']*'([^']+?)'", re.DOTALL).findall(content)
    debug("------+++++-----")
    debug(content)
    #swf = re.compile('"(.+?.swf)[?|"]', re.DOTALL).findall(content)[0]
    swf = re.compile('"(/[^"]+?.swf)[\?"]', re.DOTALL).findall(content)[0]
    debug ("SWF :: "+swf)
    if not "http" in swf:
      swf="http://www.nicknight.de"+ swf
    if urlMain in url:
        content = opener.open(match1[0]).read()
    elif urlMainJR in url :
        content = opener.open(match2[0]).read()
    elif urlMainnight in url:
        content = opener.open(match3[0]).read()
    match = re.compile("<media:content.+?url='(.+?)'", re.DOTALL).findall(content)
    content = opener.open(match[0]).read()
    match = re.compile('type="video/mp4" bitrate="(.+?)">.+?<src>(.+?)</src>', re.DOTALL).findall(content)
    bitrate = 0
    for br, urlTemp in match:
        if int(br) > bitrate:
            bitrate = int(br)
            finalUrl = urlTemp
    listitem = xbmcgui.ListItem(path=finalUrl+" swfVfy=1 swfUrl="+swf)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name, thumb):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
    playlist.add(url, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö").replace("&#x27;", "'")
    title = title.strip()
    return title


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, desc="", duration=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration})
    liz.setProperty('IsPlayable', 'true')
    liz.addContextMenuItems([(translation(30006), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+str(name)+'&thumb='+urllib.quote_plus(iconimage)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage,page=1):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
thumb = urllib.unquote_plus(params.get('thumb', ''))
page = urllib.unquote_plus(params.get('page', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listVideosJR':
    listVideosJR(url,page)
elif mode == 'listVideosnight':
    listVideosnight(url)    
elif mode == 'listShowsNight':
    listShowsNight(url)      
elif mode == 'listShows':
    listShows(url)
elif mode == 'listShowsJR':
    listShowsJR(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'queueVideo':
    queueVideo(url, name, thumb)
elif mode == 'nickMain':
    nickMain()
elif mode == 'nickJrMain':
    nickJrMain()
elif mode == 'nightMain':
    nightMain()  
elif mode == 'playVideoJR':
    playVideoJR(url)
elif mode == 'listSeriesJr':
    listSeriesJr(url)    
else:
    index()