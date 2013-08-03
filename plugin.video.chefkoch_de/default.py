#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import xbmcplugin
import xbmcgui
import xbmcaddon

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.chefkoch_de')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
viewMode = str(settings.getSetting("viewMode"))
baseUrl = "http://www.chefkoch.de"


def index():
    addDir(translation(30002), baseUrl+"/magazin/6,143,0/Chefkoch/", 'listVideos', "")
    addDir(translation(30003), baseUrl+"/magazin/6,148,0/Chefkoch/", 'listVideos', "")
    addDir(translation(30004), baseUrl+"/magazin/6,149,0/Chefkoch/", 'listVideos', "")
    addDir(translation(30005), baseUrl+"/magazin/6,150,0/Chefkoch/", 'listVideos', "")
    addDir(translation(30006), baseUrl+"/magazin/6,144,0/Chefkoch/", 'listVideos', "")
    addDir(translation(30007), baseUrl+"/magazin/6,151,0/Chefkoch/", 'listVideos', "")
    addDir(translation(30008), baseUrl+"/magazin/6,152,0/Chefkoch/", 'listVideos', "")
    addDir(translation(30009), baseUrl+"/magazin/6,153,0/Chefkoch/", 'listVideos', "")
    addDir(translation(30011), baseUrl+"/magazin/6,147,0/Chefkoch/", 'listVideos', "")
    addDir(translation(30010), baseUrl+"/magazin/6,146,0/Chefkoch/", 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    content = getUrl(url)
    if ",0/" in url:
        splStart = 1
    else:
        splStart = 2
    spl = content.split('	<a href="http://www.chefkoch.de/magazin/rt/')
    for i in range(splStart, len(spl), 1):
        entry = spl[i]
        match = re.compile('<a href="(.+?)" name="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
        url = match[0][0]
        title = match[0][2]
        title = cleanTitle(title)
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]
        match = re.compile('<strong>ca. (.+?) Min.</strong>', re.DOTALL).findall(entry)
        length = ""
        if match:
            length = match[0]
        addLink(title, url, 'playVideo', thumb, length)
    matchPage = re.compile('<span class="magazin-pagination-next">.+?<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(content)
    if matchPage:
        for url, title in matchPage:
            if title.find("chste") >= 0:
                urlNext = baseUrl+url
                addDir(translation(30001), urlNext, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    content = getUrl(url)
    match = re.compile("file  : '(.+?)'", re.DOTALL).findall(content)
    url = match[0]
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, duration):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Duration": duration})
    liz.setProperty('IsPlayable', 'true')
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

if mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
