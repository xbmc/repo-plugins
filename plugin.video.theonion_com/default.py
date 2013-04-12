#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import re
import sys
import xbmcplugin
import xbmcaddon
import xbmcgui

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = 'plugin.video.theonion_com'
addon = xbmcaddon.Addon(id=addonID)
translation = addon.getLocalizedString
forceViewMode = addon.getSetting("forceViewMode") == "true"
viewMode = str(addon.getSetting("viewMode"))
base_url = "http://www.theonion.com"


def index():
    addDir(translation(30002), base_url+"/playlists/recent-news/", 'listVideos', "")
    content = getUrl(base_url+"/video/")
    content = content[content.find('<section class="show-list">'):]
    match = re.compile('<li class=".+?" class="show-title"><a href="(.+?)">(.+?)</a><span class="duration">(.+?)</span></li>', re.DOTALL).findall(content)
    for url, title, nr in match:
        addDir(title+" ("+nr.replace(" ep.", "")+")", base_url+url, "listVideos", "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    content = getUrl(url)
    mainUrl = url[:url.find("?")]
    spl = content.split('<article>')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
        url = base_url+match[0][0]
        title = match[0][1]
        title = cleanTitle(title)
        match = re.compile('<div class="desc" style="display: none;"><p>(.+?)</p></div>', re.DOTALL).findall(entry)
        desc = ""
        if match:
            desc = match[0]
            desc = cleanTitle(desc)
        match = re.compile('<span class="duration">(.+?)</span>', re.DOTALL).findall(entry)
        length = ""
        if match:
            length = match[0]
        match = re.compile('data-src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]
        addLink(title, url, 'playVideo', thumb, length, desc)
    match = re.compile('<li class="next"><a href="(.+?)">', re.DOTALL).findall(content)
    if match:
        urlNext = mainUrl+match[0]
        addDir(translation(30001), urlNext, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    content = getUrl(url)
    match = re.compile('<source src="(.+?)" type="(.+?)">', re.DOTALL).findall(content)
    finalUrl = ""
    for url, type in match:
        if type == "video/mp4":
            finalUrl = url
    listitem = xbmcgui.ListItem(path=finalUrl)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:19.0) Gecko/20100101 Firefox/19.0')
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


def addLink(name, url, mode, iconimage, duration, desc):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Duration": duration, "Plot": desc})
    liz.setProperty('IsPlayable', 'true')
    liz.addContextMenuItems([(translation(30006), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
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

if mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'queueVideo':
    queueVideo(url, name)
else:
    index()
