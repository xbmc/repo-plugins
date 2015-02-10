#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import xbmcaddon
import xbmcplugin
import xbmcgui
import sys
import re

addon = xbmcaddon.Addon()
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
xbox = xbmc.getCondVisibility("System.Platform.xbox")
translation = addon.getLocalizedString
forceView = addon.getSetting("forceView") == "true"
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
viewID = str(addon.getSetting("viewID"))
urlMain = "http://www.vitaminl.tv"


def index():
    addDir(translation(30001), urlMain, "listVideos", icon)
    addDir(translation(30002), urlMain+"/hot", "listVideos", icon)
    addDir(translation(30003), urlMain+"/rising", "listVideos", icon)
    addDir(translation(30004), urlMain+"/top", "listVideos", icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    content = getUrl(url)
    spl = content.split('<div class="videoListItem">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('data-youtubeid="(.+?)"', re.DOTALL).findall(entry)
        id = match[0]
        match = re.compile('<div class="duration">(.+?)</div>', re.DOTALL).findall(entry)
        duration = match[0].strip()
        splDuration = duration.split(":")
        duration = str(int(splDuration[0])*60+int(splDuration[1]))
        match = re.compile('<span class="views">(.+?)</span> <span class="comments">(.+?)</span>', re.DOTALL).findall(entry)
        views = match[0][0]
        comments = match[0][1]
        thumb = "http://img.youtube.com/vi/"+id+"/0.jpg"
        match = re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        addLink(title, id, "playVideo", thumb, duration, views+" views - "+comments+" comments")
    match = re.compile('<a class="buttons nextListPage" href="(.+?)">', re.DOTALL).findall(content)
    if match:
        addDir(translation(30005), urlMain+match[0], "listVideos", '')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView:
        xbmc.executebuiltin('Container.SetViewMode('+viewID+')')


def playVideo(id):
    if xbox:
        url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
    else:
        url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')
    response = urllib2.urlopen(req)
    content = response.read()
    response.close()
    return content


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


def addLink(name, url, mode, iconimage, duration, desc):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    if duration:
        liz.addStreamInfo('video', {'duration': int(duration)})
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


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
else:
    index()
