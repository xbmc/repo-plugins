#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import os
import xbmcplugin
import xbmcaddon
import xbmcgui

#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
addonID = 'plugin.video.giga_de'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addonDir = xbmc.translatePath(addon.getAddonInfo('path'))
icon = os.path.join(addonDir, 'icon.png')
settings = xbmcaddon.Addon(id=addonID)
translation = settings.getLocalizedString
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
forceViewMode = settings.getSetting("forceView") == "true"
viewMode = str(settings.getSetting("viewID"))
Quality = settings.getSetting("maxVideoQuality")


def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    

def index():
    addDir(translation(30001), "http://www.giga.de/tv/alle-videos/", 'listVideos', icon)
    addDir(translation(30105), "http://www.giga.de/android/videos-podcasts/", 'listVideos', icon)
    addDir(translation(30106), "http://www.giga.de/windows/videos/", 'listVideos', icon)
    content = getUrl("http://www.giga.de/games/videos/")
    content = content[content.find('<section class="channels">'):]
    content = content[:content.find('</section>')]
    spl = content.split('<li>')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace("-150x95.jpg",".jpg")
        match = re.compile('<h3>(.+?)</h3>', re.DOTALL).findall(entry)
        title = match[0]
        addDir(title, url, 'listVideos', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    debug("listVideos URL:"+ url)
    mainUrl = url
    content = getUrl(url)
    spl = content.split('<hgroup>')
    for i in range(2, len(spl), 1):
        entry = spl[i]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        titleTemp = entry[entry.find("<a"):]
        match = re.compile('>(.+?)</a>', re.DOTALL).findall(titleTemp)
        title = match[0]
        title = cleanTitle(title)
        thumb = ""
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        if match:
            thumb = match[0].replace("-300x190.jpg",".jpg")
        addLink(title, url, 'playVideos', thumb)
    if "/page/" in mainUrl:
        match = re.compile('/page/(.+?)/', re.DOTALL).findall(mainUrl)
        nr = str(int(match[0])+1)
        newUrl = mainUrl[:-2]+nr+"/"
    else:
        nr = "2"
        newUrl = mainUrl+"page/2/"
    if 'class="next"' in content:
        addDir(translation(30002)+" ("+nr+")", newUrl, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideos(url):
    debug ("PLAYVIDEOS: "+ url)
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    inhalt = getUrl(url)    
    kurz_inhalt = inhalt[inhalt.find('<div class="current">')+1:]
    kurz_inhalt = kurz_inhalt[:kurz_inhalt.find('<div class="playlist" data-role="playlist">')]
    debug("kurz_inhalt : "+kurz_inhalt)
    match = re.compile('<iframe src="([^"]+)".+</div>', re.DOTALL).findall(kurz_inhalt)
    url=match[0]
    debug("URL2 :"+url)
    content = getUrl(url)
    match1 = re.compile('file: "([^"]+)", label: "([^"]+)"', re.DOTALL).findall(content)    
    debug ("Quality:"+ Quality)
    if Quality=="Select":         
          q=[]
          for url,qual in match1:
            q.append(qual)
            dialog = xbmcgui.Dialog()
          nr=dialog.select("Bitrate", q)                
          entry=match1[nr][0]
    else:
        if  Quality=="Max":
          entry=match1[0][0] 
        else:
          entry=match1[-1][0]
    debug("Entry"+ entry)    
    listitem = xbmcgui.ListItem(path=entry)    
    xbmcplugin.setResolvedUrl(pluginhandle,True, listitem)  
    

def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def getYoutubeUrl(id):
    if xbox:
        url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
    else:
        url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
    return url


def cleanTitle(title):
    return title.replace("<b>", "").replace("</b>", "").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#038;", "&").replace("&#039;", "\\").replace("&#8211;", "-").replace("&#8220;", "-").replace("&#8221;", "-").replace("&#8217;", "'").replace("&quot;", "\"").strip()


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:24.0) Gecko/20100101 Firefox/24.0')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart and iconimage!=icon:
        liz.setProperty("fanart_image", iconimage)
    liz.addContextMenuItems([(translation(30003), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if useThumbAsFanart and iconimage!=icon:
        liz.setProperty("fanart_image", iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok



params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))

if mode == 'listVideosTop':
    listVideosTop(url)
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideos':
    playVideos(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == "queueVideo":
    queueVideo(url, name)
else:
    index()
