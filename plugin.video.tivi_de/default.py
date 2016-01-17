#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = 'plugin.video.tivi_de'
#addonID = addon.getAddonInfo('id')
forceViewMode = addon.getSetting("forceViewMode") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
viewMode = str(addon.getSetting("viewMode"))
translation = addon.getLocalizedString
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
urlMain = "http://www.tivi.de"
opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')]


def index():
    addDir(translation(30001), urlMain+"/tiviVideos/rueckblick?view=flashXml", 'listVideos', icon)
    addDir(translation(30002), urlMain+"/tiviVideos/?view=flashXml", 'listVideos', icon)
    addDir(translation(30003), "", 'listShows', icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    content = opener.open(url).read()
    spl = content.split('<ns3:video-teaser>')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        entry = entry[:entry.find('</ns3:video-teaser>')]
        match = re.compile('<ns3:headline>(.+?)</ns3:headline>', re.DOTALL).findall(entry)
        title = ""
        if match:
            title = match[0]
        match = re.compile('<ns3:text>(.+?)</ns3:text>', re.DOTALL).findall(entry)
        desc = ""
        if match:
            desc = match[0]
            title += ": "+desc
        match = re.compile('<ns3:duration>P0Y0M0DT0H(.+?)M', re.DOTALL).findall(entry)
        duration = 1
        if match:
            duration = match[0]
        if duration=="0":
            duration=1
        title = cleanTitle(title).strip(" :")
        match = re.compile('<ns3:page>(.+?)</ns3:page>', re.DOTALL).findall(entry)
        url = urlMain+match[0]
        match = re.compile('<ns3:image>(.+?)</ns3:image>', re.DOTALL).findall(entry)
        thumb = urlMain+match[0]
        thumb = thumb[:thumb.rfind('/')].replace('tiviTeaserbild', 'tivi9teaserbild')
        if "7-Tage-R%C3%BCckblick" not in url:
            addLink(title, url, 'playVideo', thumb, desc, duration)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listShows():
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    content = opener.open(urlMain+"/tiviVideos/navigation?view=flashXml").read()                            
    content=content.replace("\n","")
    content=content.replace("</ns2:node>","</ns2:node>\n")
    print content
    match = re.compile('label="([^"]+)" +?image="([^"]+)" +?type="broadcast">([^<]+)', re.DOTALL).findall(content)
    print match
    x=0
    for title, thumb, url in match:
        x=x+1
        print "XXXXX", str(x)
        thumb = urlMain+thumb[:thumb.rfind('/')]
        addDir(title, urlMain+url, 'listVideos', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    content = opener.open(url).read()
    match1 = re.compile('<high>(.+?)</high>', re.DOTALL).findall(content)
    match2 = re.compile('<medium>(.+?)</medium>', re.DOTALL).findall(content)
    url = ""
    if match1:
        url = match1[0]
    elif match2:
        url = match2[1]
    if "http://" in url:
        content = opener.open(url).read()
        match = re.compile('<default-stream-url>(.+?)</default-stream-url>', re.DOTALL).findall(content)
        url = match[0]
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name, thumb):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
    playlist.add(url, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
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


def addLink(name, url, mode, iconimage, desc, duration):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart:
        liz.setProperty("fanart_image", iconimage)
    liz.addContextMenuItems([(translation(30004), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+str(name)+'&thumb='+urllib.quote_plus(iconimage)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if useThumbAsFanart and iconimage!=icon:
        liz.setProperty("fanart_image", iconimage.replace('tiviNavBild', 'tiviMStartHg'))
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
thumb = urllib.unquote_plus(params.get('thumb', ''))

if mode == 'listShows':
    listShows()
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'queueVideo':
    queueVideo(url, name, thumb)
else:
    index()
