#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import re
import xbmcplugin
import xbmcgui
import sys
import xbmcaddon
import socket

#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
addonID = 'plugin.video.myspass_de'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
forceViewMode = addon.getSetting("forceViewMode") == "true"
viewMode = str(addon.getSetting("viewMode"))
urlMain = "http://www.myspass.de"


def index():
    addDir(translation(30007), urlMain+"/myspass/includes/php/ajax.php?v=2&ajax=true&action=getVideoList&sortBy=newest&category=clips&ajax=true&timeSpan=month&pageNumber=0", 'listVideos', "")
    addDir(translation(30006), urlMain+"/myspass/includes/php/ajax.php?v=2&ajax=true&action=getVideoList&sortBy=newest&category=full_episodes&ajax=true&timeSpan=all&pageNumber=0", 'listVideos', "")
    addDir(translation(30002), "tvshows", 'listShows', "")
    addDir(translation(30003), "webshows", 'listShows', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listShows(type):
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    content = getUrl(urlMain)
    match = re.compile('<li><a href="(.+?)" title="(.+?)"', re.DOTALL).findall(content)
    for url, title in match:
        if url.find("/myspass/shows/"+type+"/") >= 0:
            addDir(title, urlMain+url, "listMediaTypes", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listMediaTypes(url):
    addDir(translation(30004), url+"#seasonlist_full_episode", 'listSeasons', "")
    addDir(translation(30005), url+"#seasonlist_clip", 'listSeasons', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listSeasons(url):
    spl = url.split("#")
    url = spl[0]
    type = spl[1]
    content = getUrl(url)
    spl = content.split('class="episodeListSeasonList')
    content = ""
    for str in spl:
        if type in str:
            content = str
    if content != "":
        content = content[:content.find('<div class="refresh"></div>')]
        spl = content.split('<li')
        urlNewVideos = ""
        titleMain = ""
        for i in range(1, len(spl), 1):
            entry = spl[i]
            match = re.compile("'_trackEvent', 'Textlink', '.+?', '(.+?)'", re.DOTALL).findall(entry)
            title = match[0]
            title = cleanTitle(title)
            titleMain = title.split("-")[0].strip()
            match = re.compile('data-query="(.+?)"', re.DOTALL).findall(entry)
            url = match[0].replace("&amp;", "&")
            url = urlMain+"/myspass/includes/php/ajax.php?v=2&ajax=true&action="+url+"&pageNumber=0"
            if "&sortBy=votes&" in url:
                urlNewVideos = urlMain+"/myspass/includes/php/ajax.php?action=getEpisodeListFromSeason"+url.replace("&sortBy=votes&", "&sortBy=episode_desc&")+"&pageNumber=0"
            addDir(title, url, 'listVideosAZ', "")
    if urlNewVideos:
        addDir(titleMain+" - "+translation(30008), urlNewVideos, 'listVideosAZ', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listVideosAZ(url):
    currentUrl = url
    content = getUrl(url)
    spl = content.split('<div class="tooltip"')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile('<div class="spacer5"></div>(.+?)<', re.DOTALL).findall(entry)
        desc = match[0]
        desc = cleanTitle(desc)
        match = re.compile("location.href='(.+?)'", re.DOTALL).findall(entry)
        id = match[0].split("/")[-2]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = urlMain+match[0].replace("_135x76.jpg", "_294x165.jpg")
        entry = entry[entry.find('<td class="duration"'):]
        entry = entry[entry.find('<a href='):]
        match = re.compile('>(.+?)<', re.DOTALL).findall(entry)
        duration = match[0]
        match = re.compile('(.+?):(.+?):(.+?)', re.DOTALL).findall(duration)
        if match:
            duration = str(int(match[0][0])*60+int(match[0][1]))
        if duration.startswith("0:"):
            duration = "1"
        addLink(title, id, 'playVideo', thumb, desc, duration)
    currentPage = int(currentUrl.split("=")[-1])
    urlNext = currentUrl.replace("&pageNumber="+str(currentPage), "&pageNumber="+str(currentPage+1))
    addDir(translation(30001)+" ("+str(currentPage+2)+")", urlNext, 'listVideosAZ', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listVideos(url):
    currentUrl = url
    content = getUrl(url)
    spl = content.split('<div class="teaser teaserSmall">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile('href="/myspass/shows/(.+?)/(.+?)/(.+?)/(.+?)/"', re.DOTALL).findall(entry)
        id = match[0][3]
        match = re.compile('data-original="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace("_135x76.jpg", "_294x165.jpg")
        match = re.compile('<span class="length">(.+?)</span>', re.DOTALL).findall(entry)
        duration = match[0]
        match = re.compile('(.+?):(.+?):(.+?)', re.DOTALL).findall(duration)
        if len(match) > 0:
            duration = str(int(match[0][0])*60+int(match[0][1]))
        if duration.startswith("0:"):
            duration = "1"
        addLink(title, id, 'playVideo', thumb, "", duration)
    currentPage = int(currentUrl.split("=")[-1])
    urlNext = currentUrl.replace("&pageNumber="+str(currentPage), "&pageNumber="+str(currentPage+1))
    addDir(translation(30001)+" ("+str(currentPage+2)+")", urlNext, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(id):
    content = getUrl(urlMain+"/myspass/includes/apps/video/getvideometadataxml.php?id="+id)
    match = re.compile('<url_flv><!\\[CDATA\\[(.+?)\\]\\]></url_flv>', re.DOTALL).findall(content)
    listitem = xbmcgui.ListItem(path=match[0])
    return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:23.0) Gecko/20100101 Firefox/23.0')
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


def addLink(name, url, mode, iconimage, desc="", duration=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration})
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
elif mode == 'listVideosAZ':
    listVideosAZ(url)
elif mode == 'listShows':
    listShows(url)
elif mode == 'listMediaTypes':
    listMediaTypes(url)
elif mode == 'listSeasons':
    listSeasons(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
