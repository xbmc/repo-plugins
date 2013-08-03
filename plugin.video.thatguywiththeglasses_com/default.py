#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import re
import sys
import xbmcplugin
import xbmcgui
import xbmcaddon

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(id='plugin.video.thatguywiththeglasses_com')
translation = addon.getLocalizedString

forceViewMode = addon.getSetting("forceViewMode") == "true"
viewMode = str(addon.getSetting("viewMode"))


def index():
    addDir(translation(30001), "http://thatguywiththeglasses.com/videolinks", 'listLatest', "")
    addDir("ThatGuyWithTheGlasses", "/videolinks/thatguywiththeglasses/", 'listShows', "")
    addDir("BlisteredThumbs", "/bt/", 'listShows', "")
    addDir("Team TGWTG", "/videolinks/teamt/", 'listShows', "")
    addDir("Team NChick", "/videolinks/team-nchick/", 'listShows', "")
    addDir("InkedReality", "/videolinks/ir/", 'listShows', "")
    addDir("Brad Jones", "/videolinks/bj/", 'listShows', "")
    addDir("Linkara", "/videolinks/linkara/", 'listShows', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listShows(urlMain):
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    content = getUrl("http://thatguywiththeglasses.com/videolinks")
    spl = content.split('<a class="link" href="'+urlMain)
    for i in range(1, len(spl), 1):
        entry = spl[i]
        url = urlMain+entry[:entry.find('"')]
        match = re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        addDir(title, url, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listLatest(url):
    content = getUrl(url)
    content = content[content.find('<div id="video-list" class="video-list">'):]
    content = content[:content.find('<div class="side-mod">')]
    spl = content.split('<div class="video">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]
        match = re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        if "http://thatguywiththeglasses.com/podcasts/" not in url:
            addLink(title, url, 'playVideo', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listVideos(url):
    content = getUrl("http://thatguywiththeglasses.com"+url)
    match = re.compile('<input type="hidden" name="id" value="(.+?)"', re.DOTALL).findall(content)
    id = match[0]
    match = re.compile('<input type="hidden" name="sectionid" value="(.+?)"', re.DOTALL).findall(content)
    sectionId = match[0]
    content = getUrl("http://thatguywiththeglasses.com"+url+"?limit=0&id="+id+"&sectionid="+sectionId+"&task=category&filter_order=a.created&filter_order_Dir=desc&limitstart=0")
    spl = content.split('<tr class="sectiontableentry')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<a href="(.+?)">\n(.+?)</a>', re.DOTALL).findall(entry)
        url = "http://thatguywiththeglasses.com"+match[0][0]
        title = match[0][1]
        title = cleanTitle(title)
        match = re.compile('<td  headers="tableOrdering2">\n(.+?)</td>', re.DOTALL).findall(entry)
        date = ""
        if match:
            date = " ("+match[0].strip()+")"
        addLink(title+date, url, 'playVideo', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    content = getUrl(url)
    content = content[:content.find('<div id="video-list" class="video-list">')]
    match1 = re.compile('src="http://blip.tv/play/(.+?)"', re.DOTALL).findall(content)
    match3 = re.compile('name="movie" value="http://www.springboardplatform.com/mediaplayer/springboard/video/(.+?)/(.+?)/(.+?)/">', re.DOTALL).findall(content)
    match4 = re.compile('src="http://www.youtube.com/embed/(.+?)"', re.DOTALL).findall(content)
    match5 = re.compile('<a href="http://www.blisteredthumbs.net/(.+?)">', re.DOTALL).findall(content)
    if match3:
        id1 = match3[0][1]
        id2 = match3[0][2]
        content = getUrl("http://cms.springboard.gorillanation.com/xml_feeds_advanced/index/"+id1+"/rss3/"+id2+"/")
        match = re.compile('<media:content duration="(.+?)" medium="video" bitrate="(.+?)" fileSize="(.+?)" url="(.+?)"', re.DOTALL).findall(content)
        listitem = xbmcgui.ListItem(path=match[0][3])
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    elif match1:
        if len(match1) > 1 and "http://www.blisteredthumbs.net/" not in url:
            url = listParts(match1)
        else:
            url = "http://blip.tv/play/"+match1[0]
            url = url.replace(".x?p=1", "")
        content = urllib.unquote_plus(getRedirectedUrl(url))
        if content.find("http://blip.tv/rss/flash/") >= 0:
            id = content[content.find("http://blip.tv/rss/flash/")+25:]
        if xbox == True:
            listitem = xbmcgui.ListItem(path="plugin://video/BlipTV/?path=/root/video&action=play_video&videoid="+id)
        else:
            listitem = xbmcgui.ListItem(path="plugin://plugin.video.bliptv/?path=/root/video&action=play_video&videoid="+id)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    elif match4:
        id = match4[0]
        if xbox == True:
            listitem = xbmcgui.ListItem(path="plugin://video/Youtube/?path=/root/video&action=play_video&videoid="+id)
        else:
            listitem = xbmcgui.ListItem(path="plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid="+id)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    elif match5:
        playVideo("http://www.blisteredthumbs.net/"+match5[0])


def listParts(match):
    i = 1
    partNames = []
    partUrls = []
    for url in match:
        partNames.append("Part "+str(i))
        partUrls.append("http://blip.tv/play/"+url.replace(".x?p=1", ""))
        i += 1
    dialog = xbmcgui.Dialog()
    nr = dialog.select("Parts", partNames)
    if nr >= 0:
        return partUrls[nr]


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


def getRedirectedUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
    response = urllib2.urlopen(req)
    response.close()
    return str(response.geturl())


def getUrl(url, data=None):
    if data != None:
        req = urllib2.Request(url, data)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    else:
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
elif mode == 'listShows':
    listShows(url)
elif mode == 'listLatest':
    listLatest(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
