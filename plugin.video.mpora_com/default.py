#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import re
import sys
import xbmcplugin
import xbmcgui
import xbmcaddon
import base64
import socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.mpora_com')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
viewMode = str(settings.getSetting("viewMode"))
maxVideoQuality = settings.getSetting("maxVideoQuality")
qual = ["720p", "540p"]
maxVideoQuality = qual[int(maxVideoQuality)]


def index():
    addDir(translation(30002), "http://mpora.com/videos", 'sortDirection', "")
    addDir(translation(30003), "http://mpora.com/snowboarding/videos", 'sortDirection', "")
    addDir(translation(30004), "http://mpora.com/surfing/videos", 'sortDirection', "")
    addDir(translation(30005), "http://mpora.com/skateboarding/videos", 'sortDirection', "")
    addDir(translation(30006), "http://mpora.com/bmx/videos", 'sortDirection', "")
    addDir(translation(30007), "http://mpora.com/bmxracing/videos", 'sortDirection', "")
    addDir(translation(30008), "http://mpora.com/mountainbiking/videos", 'sortDirection', "")
    addDir(translation(30009), "http://mpora.com/motocross/videos", 'sortDirection', "")
    addDir(translation(30010), "http://mpora.com/skiing/videos", 'sortDirection', "")
    addDir(translation(30011), "http://mpora.com/wakeboarding/videos", 'sortDirection', "")
    addDir(translation(30012), "http://mpora.com/windsurfing/videos", 'sortDirection', "")
    addDir(translation(30013), "http://mpora.com/kitesurfing/videos", 'sortDirection', "")
    addDir(translation(30014), "http://mpora.com/road-cycling/videos", 'sortDirection', "")
    addDir(translation(30015), "http://mpora.com/outdoor/videos", 'sortDirection', "")
    addDir(translation(30020), "", 'search', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def sortDirection(url):
    urlRecent = url+"/recent"
    urlBrands = url+"/brands"
    urlHD = url+"/hd"
    addDir(translation(30017), urlRecent, 'listVideos', "")
    addDir(translation(30016), url, 'listVideos', "")
    addDir(translation(30019), urlHD, 'listVideos', "")
    addDir(translation(30018), urlBrands, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listVideos(url):
    content = getUrl(url)
    spl = content.split('<a class="video-thumbnail')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<h6>(.+?)</h6>', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = "http://mpora.com"+match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace("_200x112_", "_640x360_").replace("_tn_", "_")
        addLink(title, url, 'playVideo', thumb)
    matchPage = re.compile('<a class="next_page" rel="next" href="(.+?)">', re.DOTALL).findall(content)
    if matchPage:
        urlNext = "http://mpora.com"+matchPage[0]
        addDir(translation(30001), urlNext, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def search():
    keyboard = xbmc.Keyboard('', translation(30020))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        listVideos('http://mpora.com/search?q='+search_string+'&submit=search')


def playVideo(url):
    content = getUrl(url)
    matchSD = re.compile('"sd":{"sources":\\[{"type":"video/mp4","src":"(.+?)"}', re.DOTALL).findall(content)
    matchHD = re.compile('"hd":{"sources":\\[{"type":"video/mp4","src":"(.+?)"}', re.DOTALL).findall(content)
    finalUrl = ""
    if matchSD:
        finalUrl = matchSD[0]
        if maxVideoQuality == "720p" and len(matchHD) > 0:
            finalUrl = matchHD[0]
    if finalUrl:
        listitem = xbmcgui.ListItem(path=finalUrl)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')
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


def addLink(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
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
mode = params.get('mode')
url = params.get('url')
if isinstance(url, type(str())):
    url = urllib.unquote_plus(url)

if mode == 'listVideos':
    listVideos(url)
elif mode == 'sortDirection':
    sortDirection(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'playAll':
    playAll(url)
elif mode == 'search':
    search()
else:
    index()
