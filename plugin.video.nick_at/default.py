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
import xbmcaddon

#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
addonID = 'plugin.video.nick_at'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
jrOnly = addon.getSetting("jrOnly") == "true"
forceViewMode = addon.getSetting("forceView") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
viewMode = str(addon.getSetting("viewID"))
translation = addon.getLocalizedString
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
iconJr = xbmc.translatePath('special://home/addons/'+addonID+'/iconJr.png')
iconNight = xbmc.translatePath('special://home/addons/'+addonID+'/iconnight.png')
urlMain = "http://www.nickelodeon.at"
urlMainJR = "http://www.nickelodeon.at/sender/nickjr"
urlMainnight ="http://www.nicknight.at"
opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')]

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


def nickMain():
    addDir(translation(30003), urlMain+"/videos", 'listVideos', icon)
    addDir(translation(30004), urlMain+"/videos", 'listShows', icon)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def nickJrMain():
    addDir(translation(30003), urlMainJR, 'listShowsJRnew', iconJr)
    addDir(translation(30004), urlMainJR, 'listShowsJR', iconJr)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def nightMain():
    addDir(translation(30004), urlMainnight, 'listShowsNight', iconNight)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

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
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listShows(url):
    content = opener.open(url).read()
    match = re.compile('<li class=\'item\'><a href="(.+?)".*?alt="(.+?)" src="(.+?)"', re.DOTALL).findall(content)
    for url, title, thumb in match:
        if url.startswith("/shows/"):
            title = title[:title.rfind(" - ")]
            title = cleanTitle(title)
            addDir(title, urlMain+url, 'listVideos', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listShowsJR(url):
    debug ("listShowsJR :" +url)
    content = opener.open(url).read()
    content = content[content.find("<h2 class='headline-section'>Nick Jr. Shows</h2>"):]
    content = content[:content.find("<div class='row apps no-scroll'>")]    
    spl = content.split("<div class='list-simple--teaser-container small'>")
    for i in range(1, len(spl), 1):
        entry = spl[i]
        debug("------------")
        debug(entry)
        match = re.compile("title=[\"'](.+?)['\"]", re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile("data-src='(.+?)'", re.DOTALL).findall(entry)
        thumb = match[0]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = "http://www.nickelodeon.at"+match[0]
        debug("listShowsJR Showurl: "+ url)
        addDir(title, url, 'listVideosJR', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listShowsJRnew(url):
    debug ("listShowsJR :" +url)
    content = opener.open(url).read()
    content = content[content.find("<h1 class='row-title channels'>Neu bei Nick Jr.</h1>"):]
    content = content[:content.find("<h2 class='headline-section'>Nick Jr. Shows</h2>")]
    spl = content.split("<div class='list-simple--teaser-container'>")
    for i in range(1, len(spl), 1):
        entry = spl[i]
        debug("------------")
        debug(entry)
        match = re.compile("title=[\"'](.+?)['\"]", re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile("data-src='(.+?)'", re.DOTALL).findall(entry)
        thumb = match[0]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = "http://www.nickelodeon.at"+match[0]
        debug("listShowsJR Showurl: "+ url)
        addDir(title, url, 'listVideosJR', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
        
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
        addDir(title, url, 'listVideosnight', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideosJR(url):
    debug("listVideosJR URL: "+ url)
    content = opener.open(url).read()
    content = content[content.find("<ol class='playlist'>"):]
    content = content[:content.find("</ol>")]
    spl = content.split("<li class='fullepisode playlist-item'")
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile("title=[\"'](.+?)['\"]", re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile("src=[\"'](.+?)[\"']", re.DOTALL).findall(entry)
        thumb = match[0]
        match = re.compile("href=[\"'](.+?)[\"']", re.DOTALL).findall(entry)
        url = match[0]
        addLink(title, url, 'playVideo', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

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
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    xbmc.log("NICK : "+ url) 
    content = opener.open(url).read()
    match = re.compile("mrss[:= ]+?[\"']([^\"']+?)[\"']", re.DOTALL).findall(content)                        
    url=match[0]  
    debug("--------- :"+url)    
    content = opener.open(url).read()
    match = re.compile("<media:content.+?url='(.+?)'", re.DOTALL).findall(content)
    content = opener.open(match[0]).read()
    match = re.compile('type="video/mp4" bitrate="(.+?)">.+?<src>(.+?)</src>', re.DOTALL).findall(content)
    bitrate = 0
    for br, urlTemp in match:
        if int(br) > bitrate:
            bitrate = int(br)
            finalUrl = urlTemp
    listitem = xbmcgui.ListItem(path=finalUrl+" swfVfy=1 swfUrl=http://player.mtvnn.com/assets/footer/mediaplayer/g2player_2.2.4.swf")
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


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
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

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listVideosJR':
    listVideosJR(url)
elif mode == 'listShowsJRnew':
    listShowsJRnew(url)    
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
else:
    index()
