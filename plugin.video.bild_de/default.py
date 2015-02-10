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
addon = xbmcaddon.Addon(id='plugin.video.bild_de')
forceViewMode = addon.getSetting("forceViewMode") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
viewMode = str(addon.getSetting("viewMode"))
translation = addon.getLocalizedString
urlMain = "http://www.bild.de"


def index():
    content = getUrl(urlMain+"/video/startseite/bildchannel-home/video-home-15713248.bild.html")
    content = content[content.find('<ol class="tabs">'):]
    content = content[:content.find('</ol>')]
    match = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(content)
    for url, title in match:
        spl = url.split("-")
        id = spl[len(spl)-1]
        id = id[:id.find(".")]
        url = urlMain+"/video/clip/tb-neueste-videos-30052724,zeigeTSLink=true,page=0,isVideoStartseite=true,view=ajax,contentContextId="+id+".bild.html"
        addDir(title, url, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    content = getUrl(url)
    spl = content.split('<div class="hentry')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<time datetime=".+?">(.+?)</time>', re.DOTALL).findall(entry)
        date = match[0]
        match = re.compile('<span class="kicker">(.+?)</span>', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        title = title.replace("„", "").replace("“", "")
        match = re.compile('href="/video/clip/(.+?)"', re.DOTALL).findall(entry)
        url = urlMain+"/video/clip/"+match[0]
        url = url.replace(".bild.html", ",view=xml.bild.xml")
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace("w=323", "w=800")
        addLink(title, url, 'playVideo', thumb)
    match = re.compile('class="next hide-text" data-ajax-href="(.+?)"', re.DOTALL).findall(content)
    if match:
        url = match[0]
        addDir(translation(30001), urlMain+url, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    content = getUrl(url)
    match = re.compile('<video src="(.+?)"', re.DOTALL).findall(content)
    listitem = xbmcgui.ListItem(path=match[0])
    return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


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


def addLink(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart:
        liz.setProperty("fanart_image", iconimage)
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
