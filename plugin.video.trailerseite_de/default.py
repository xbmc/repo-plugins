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
addonId = 'plugin.video.trailerseite_de'
addon = xbmcaddon.Addon(id=addonId)
translation = addon.getLocalizedString
xbox = xbmc.getCondVisibility("System.Platform.xbox")
maxVideoQuality = str(addon.getSetting("maxVideoQuality"))
showAllTrailers = addon.getSetting("showAllTrailers") == "true"
forceViewMode = addon.getSetting("forceViewMode") == "true"
viewMode = str(addon.getSetting("viewMode"))
baseUrl = "http://www.trailerseite.de"


def index():
    addDir(translation(30001), baseUrl+"/kino/neustarts-film-trailer.html", 'listMoviesMain', "")
    addDir(translation(30002), baseUrl+"/kino/film-trailer-vorschau.html", 'listMoviesMain', "")
    addDir(translation(30003), baseUrl+"/kino/highlights-film-trailer.html", 'listMoviesMain', "")
    addDir(translation(30004), baseUrl+"/kino/arthouse-film-trailer.html", 'listMoviesMain', "")
    addDir(translation(30005), baseUrl+"/kino/charts/deutsche-kino-top-10.html", 'listMoviesMain', "")
    addDir(translation(30006), baseUrl+"/kino/charts/us-kino-top-10.html", 'listMoviesMain', "")
    addDir(translation(30007), baseUrl+"/kino/charts/arthouse-kino-top-10.html", 'listMoviesMain', "")
    addDir(translation(30015), "http://feeds.feedburner.com/updates?format=xml", 'listLastTrailer', "")
    addDir(translation(30016), "http://feeds.feedburner.com/updates?format=xml", 'listLastVideos', "")
    addDir(translation(30014), baseUrl+"/kino/starttermine-kinofilme-24075.html", 'listMoviesDate', "")
    addDir(translation(30008), baseUrl+"/kino/film-trailer-a-z.html", 'listMoviesAZ', "")
    addDir(translation(30009), baseUrl+"/trailer-dvd/neustarts/", 'listMoviesMain', "")
    addDir(translation(30010), baseUrl+"/trailer-dvd/dvd-vorschau.html", 'listMoviesMain', "")
    addDir(translation(30011), baseUrl+"/trailer-dvd/dvd-top-10.html", 'listMoviesMain', "")
    addDir(translation(30012), baseUrl+"/filmkritiken/16007-film-specials.html", 'listMoviesMain', "")
    addDir("Der ehrliche Dennis", baseUrl+"/der-ehrliche-dennis/index.html", 'listMoviesMain', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listMoviesMain(url):
    content = getUrl(url)
    spl = content.split('<div class="expoteaser">')
    listMovies(url, spl)
    spl = content.split('<div class="teasermultiple">')
    listMovies(url, spl)
    spl = content.split('<div class="rightteaser">')
    listMovies(url, spl)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listMovies(mainUrl, spl):
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = baseUrl+match[0]
        match = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = baseUrl+"/"+match[0]
        thumbNew = thumb.replace("-expo.jpg", ".jpg").replace("-right.jpg", ".jpg").replace(".jpg", "-right.jpg")
        req = urllib2.Request(thumbNew)
        try:
            urllib2.urlopen(req)
            thumb = thumbNew
        except:
            thumbNew = thumb.replace("-expo.jpg", ".jpg").replace("-right.jpg", ".jpg").replace(".jpg", "-expo.jpg")
            req = urllib2.Request(thumbNew)
            try:
                urllib2.urlopen(req)
                thumb = thumbNew
            except:
                pass
        if showAllTrailers and mainUrl not in [baseUrl+"/der-ehrliche-dennis/index.html", baseUrl+"/filmkritiken/16007-film-specials.html"]:
            addDir(title, url, 'listTrailers', thumb)
        else:
            addLink(title, url, 'playVideo', thumb, "")


def listTrailers(url, name, thumb):
    content = getUrl(url)
    spl = content.split('<div class="extraplayer">')
    addLink(name+" Trailer", url, 'playVideo', thumb, "")
    for i in range(1, len(spl), 1):
        entry = spl[i]
        if 'class="aFLVPlayer"' not in entry:
            entry = entry[entry.find("<a href=")+1:]
            match = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
            url = match[0][0]
            title = match[0][1]
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0]
            addLink(title, url, 'playVideo', thumb, "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listLastTrailer(url):
    content = getUrl(url)
    spl = content.split('<item>')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<link>(.+?)</link>', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('<title>(.+?)</title>', re.DOTALL).findall(entry)
        title = match[0]
        match = re.compile('<date>(.+?)-(.+?)-(.+?) ', re.DOTALL).findall(entry)
        month = match[0][1]
        day = match[0][2]
        title = day+"."+month+" - "+title
        if '/film/' in url and "Trailer" in title:
            addLink(title, url, 'playVideo', "", "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listLastVideos(url):
    content = getUrl(url)
    spl = content.split('<item>')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<link>(.+?)</link>', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('<title>(.+?)</title>', re.DOTALL).findall(entry)
        title = match[0]
        match = re.compile('<date>(.+?)-(.+?)-(.+?) ', re.DOTALL).findall(entry)
        month = match[0][1]
        day = match[0][2]
        title = day+"."+month+" - "+title
        if '/film/' in url and "Trailer" not in title:
            addLink(title, url, 'playVideo', "", "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listMoviesAZ(url):
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    content = getUrl(url)
    content = content[content.find('<div class="abhaken">'):]
    content = content[:content.find('</table>'):]
    match = re.compile('<a href="(.+?)" title=".+?" >(.+?)</a>', re.DOTALL).findall(content)
    for url, title in match:
        match2 = re.compile('<a href=".+?" title="(.+?)"', re.DOTALL).findall(title)
        if match2:
            title = cleanTitle(match2[0][0])
        else:
            title = cleanTitle(title)
        if showAllTrailers:
            addDir(title, baseUrl+url, 'listTrailers', "")
        else:
            addLink(title, baseUrl+url, 'playVideo', "", "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listMoviesDate(url):
    content = getUrl(url)
    spl = content.split('<div class="textbox-white">')
    for i in range(1, len(spl), 1):
        entry = spl[i].replace('">', '" title="TEST" >')
        entry = entry[:entry.find("</tr>")]
        match = re.compile('<h3>Ab (.+?).20', re.DOTALL).findall(entry)
        date = match[0]
        match = re.compile('<a href="(.+?)" title=".+?" >(.+?)</a>', re.DOTALL).findall(entry)
        for url, title in match:
            title = date+" - "+cleanTitle(title)
            if showAllTrailers:
                addDir(title, baseUrl+url, 'listTrailers', "")
            else:
                addLink(title, baseUrl+url, 'playVideo', "", "")
    xbmcplugin.endOfDirectory(pluginhandle)


def playVideo(url):
    content = getUrl(url)
    matchDM = re.compile('src="http://www.dailymotion.com/embed/video/(.+?)\\?', re.DOTALL).findall(content)
    content = content[content.find('<div class="flashplayer">'):]
    matchSD = re.compile('href="(.+?)"', re.DOTALL).findall(content)
    matchHD = re.compile('<a class="aFLVPlayer" href="(.+?)"></a>', re.DOTALL).findall(content)
    streamUrl = ""
    if matchHD and maxVideoQuality == "1":
        streamUrl = matchHD[0]
    elif matchSD:
        streamUrl = matchSD[0]
    elif matchDM:
        streamUrl = getDailyMotionUrl(matchDM[0])
    listitem = xbmcgui.ListItem(path=streamUrl)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def getDailyMotionUrl(id):
    if xbox:
        url = "plugin://video/DailyMotion.com/?url="+id+"&mode=playVideo"
    else:
        url = "plugin://plugin.video.dailymotion_com/?url="+id+"&mode=playVideo"
    return url


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#038;", "&").replace("&#39;", "'")
    title = title.replace("&#039;", "'").replace("&#8211;", "-").replace("&#8220;", "-").replace("&#8221;", "-").replace("&#8217;", "'")
    title = title.replace("&quot;", "\"").replace("&uuml;", "ü").replace("&auml;", "ä").replace("&ouml;", "ö")
    title = title.replace("Trailer", "").strip()
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


def addLink(name, url, mode, iconimage, desc):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    liz.setProperty('IsPlayable', 'true')
    liz.addContextMenuItems([(translation(30013), 'RunPlugin(plugin://'+addonId+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)+"&name="+urllib.quote_plus(name)+"&thumb="+urllib.quote_plus(iconimage)
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

if mode == 'listMoviesMain':
    listMoviesMain(url)
elif mode == 'listLastTrailer':
    listLastTrailer(url)
elif mode == 'listLastVideos':
    listLastVideos(url)
elif mode == 'listVideosCharts':
    listVideosCharts(url)
elif mode == 'listMoviesAZ':
    listMoviesAZ(url)
elif mode == 'listMoviesDate':
    listMoviesDate(url)
elif mode == 'listTrailers':
    listTrailers(url, name, thumb)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'queueVideo':
    queueVideo(url, name)
else:
    index()
