#!/usr/bin/python
# -*- coding: utf-8 -*-
import socket
import urllib
import urllib2
import xbmcplugin
import xbmcaddon
import xbmcgui
import time
import sys
import os
import re

#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
addonID = 'plugin.video.tvtoday_de'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
opener = urllib2.build_opener()
baseUrl = "http://www.tvtoday.de"
userAgent = "Mozilla/5.0 (Windows NT 5.1; rv:24.0) Gecko/20100101 Firefox/24.0"
opener.addheaders = [('User-Agent', userAgent)]
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
forceViewMode = addon.getSetting("forceView") == "true"
viewMode = str(addon.getSetting("viewID"))
addonDir = xbmc.translatePath(addon.getAddonInfo('path'))
addonUserDataFolder = xbmc.translatePath(addon.getAddonInfo('profile'))
cacheFile = os.path.join(addonUserDataFolder, 'cache')
icon = os.path.join(addonDir, 'icon.png')

if not os.path.isdir(addonUserDataFolder):
    os.mkdir(addonUserDataFolder)


def index():
    addDir("Gesamt", "", 'listVideosAll', icon)
    addDir("Serien", "carousel_SE", 'listVideos', icon)
    addDir("Reportagen", "carousel_RE", 'listVideos', icon)
    addDir("Spielfilme", "carousel_SP", 'listVideos', icon)
    addDir("Unterhaltung", "carousel_U", 'listVideos', icon)
    addDir("Kinder", "carousel_KIN", 'listVideos', icon)
    addDir("Sport", "carousel_SPO", 'listVideos', icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideosAll():
    content = getUrl(baseUrl+"/mediathek")
    content = content[content.find('<div id="topTeaser"')+1:]
    spl = content.split('<div class="carousel-feature">')
    entries = []
    for i in range(1, len(spl), 1):
        entry = spl[i]
        if "rtl2-programm" not in entry and "rtl-programm" not in entry and "vox-programm" not in entry and "super-programm" not in entry:
            match1 = re.compile('class="heading">(.+?)<', re.DOTALL).findall(entry)
            match2 = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            if match1:
                title = cleanTitle(match1[0])
            elif match2:
                title = cleanTitle(match2[0])
            title = title.replace("<wbr/>","").replace("<br />"," -")
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url = match[0]
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0]
            thumb = thumb[:thumb.find(',')]+".jpg"
            addLink(title, url, 'playVideo', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listVideos(type):
    content = getUrl(baseUrl+"/mediathek")
    content = content[content.find('id="'+type+'"'):]
    content = content[:content.find('</ul>')]
    spl = content.split('<div class="el">')
    entries = []
    for i in range(1, len(spl), 1):
        entry = spl[i]
        if "sat1-programm" not in entry:
            match = re.compile('<strong>([^<]*)</strong>.+?<span>(.+?)</span>', re.DOTALL).findall(entry)
            title = cleanTitle(match[0][0].strip())+" - "+cleanTitle(match[0][1].strip())
            title = title.replace("<wbr/>","").replace("<br />"," -")
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url = match[0]
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0]
            thumb = thumb[:thumb.find(',')]+".jpg"
            addLink(title, url, 'playVideo', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(urlMain):
    content = opener.open(urlMain).read()
    match1 = re.compile("openwin\\('(.+?)'", re.DOTALL).findall(content)
#                      <a href="http://mediathek.daserste.de/Die-Kanzlei/Folge-13-%C3%9Cble-Tricks/Das-Erste/Video?documentId=32425652&bcastId=30292384" class="mediathek-open col-hover-thek" id="mediathek-8160108" data-info="Die Kanzlei-ARD-8160108">
    match2 = re.compile('a href=\"([^"]+)" class="mediathek-open col-hover-thek"', re.DOTALL).findall(content)
    if match1:
        url = match1[0]
    elif match2:
        url = match2[0]
    finalUrl = ""
    if url.startswith("http://www.zdf.de/ZDFmediathek/"):
        match = re.compile("/beitrag/video/(.+?)/", re.DOTALL).findall(url)
        if match:
            finalUrl = getPluginUrl("plugin.video.zdf_de_lite")+"/?mode=playVideo&url="+urllib.quote_plus(match[0])
    elif url.startswith("http://www.arte.tv"):
        match = re.compile("http://www.arte.tv/guide/de/([^/]+?)/", re.DOTALL).findall(url)
        id=match[0]
        try:            
            xbmcaddon.Addon('plugin.video.arte_tv')
            finalUrl = getPluginUrl("plugin.video.arte_tv")+"/?mode=play-video&id="+id
        except:
          try:
               xbmcaddon.Addon('plugin.video.arteplussept')
               finalUrl = getPluginUrl("plugin.video.arteplussept")+"/play/"+urllib.quote_plus(id)               
          except:
                xbmc.log("Kein Arte Plugin vorhanden")
        #http://www.arte.tv/guide/de/064098-001/arte-junior-das-magazin

        print "##X## "+ id                
    elif url.startswith("http://mediathek.daserste.de/"):
        m = re.compile('documentId=([0-9]+)', re.DOTALL).findall(content)        
        url = m[0]        
        finalUrl = getPluginUrl("plugin.video.ardmediathek_de")+"/?mode=playVideo&url="+urllib.quote_plus(url)
    elif url.startswith("http://www.ardmediathek.de/"):
        url = url[url.find("documentId=")+11:]
        if "&" in url:
            url = url[:url.find("&")]
        finalUrl = getPluginUrl("plugin.video.ardmediathek_de")+"/?mode=playVideo&url="+urllib.quote_plus(url)
    elif url.startswith("http://rtl-now.rtl.de/") or url.startswith("http://rtl2now.rtl2.de/") or url.startswith("http://www.voxnow.de/") or url.startswith("http://www.rtlnitronow.de/") or url.startswith("http://www.superrtlnow.de/"):
        finalUrl = getPluginUrl("plugin.video.rtl_now")+"/?mode=playVideo&url="+urllib.quote_plus(url)
    if finalUrl:
        listitem = xbmcgui.ListItem(path=finalUrl)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def getUrl(url):
    if os.path.exists(cacheFile) and (time.time()-os.path.getmtime(cacheFile) < 60*10):
        fh = open(cacheFile, 'r')
        content = fh.read()
        fh.close()
    else:
        content = opener.open(url).read()
        fh = open(cacheFile, 'w')
        fh.write(content)
        fh.close()
    return content


def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')


def cleanTitle(title):
    title = title.replace("u0026", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.replace("\\'", "'").strip()
    return title


def getPluginUrl(pluginID):
    plugin = xbmcaddon.Addon(id=pluginID)
    if xbmc.getCondVisibility("System.Platform.xbox"):
        return "plugin://video/"+plugin.getAddonInfo('name')
    else:
        return "plugin://"+plugin.getAddonInfo('id')


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, desc="", duration="", date=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Aired": date, "Duration": duration, "Episode": 1})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart and iconimage!=icon:
        liz.setProperty("fanart_image", iconimage)
    entries = []
    entries.append((translation(30001), 'RunPlugin('+getPluginUrl(addonID)+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',))
    liz.addContextMenuItems(entries)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, args="", type=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&thumb="+urllib.quote_plus(iconimage)+"&args="+urllib.quote_plus(args)+"&type="+urllib.quote_plus(type)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultTVShows.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if useThumbAsFanart and not iconimage.split(os.sep)[-1].startswith("icon"):
        liz.setProperty("fanart_image", iconimage)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
thumb = urllib.unquote_plus(params.get('thumb', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listVideosAll':
    listVideosAll()
elif mode == 'playVideo':
    playVideo(url)
elif mode == "queueVideo":
    queueVideo(url, name)
else:
    index()
