#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import xbmcplugin
import xbmcaddon
import xbmcgui
import os
import re
import sys

#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
addonID = 'plugin.video.filmstarts_de'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
translation = addon.getLocalizedString
addonDir = xbmc.translatePath(addon.getAddonInfo('path'))
defaultFanart = os.path.join(addonDir ,'fanart.png')
icon = os.path.join(addonDir ,'icon.png')
xbox = xbmc.getCondVisibility("System.Platform.xbox")
showAllTrailers = addon.getSetting("showAllTrailers") == "true"
forceView = addon.getSetting("forceView") == "true"
useCoverAsFanart = addon.getSetting("useCoverAsFanart") == "true"
viewID = str(addon.getSetting("viewID"))
maxCoverResolution = addon.getSetting("maxCoverResolution")
baseUrl = "http://www.filmstarts.de"


def index():
    addDir('Trailer: '+translation(30008), '', "search", '')
    addDir('Trailer: '+translation(30001), baseUrl + '/trailer/aktuell_im_kino.html?version=1', "showSortDirection", '')
    addDir('Trailer: '+translation(30002), baseUrl + '/trailer/bald_im_kino.html?version=1', "showSortDirection", '')
    addDir('Filmstarts: Fünf Sterne', baseUrl + '/videos/shows/funf-sterne', "listVideos", '')
    addDir('Filmstarts: Interviews', baseUrl + '/trailer/interviews/', "listVideos", '')
    addDir('Filmstarts: Fehlerteufel', baseUrl + '/videos/shows/filmstarts-fehlerteufel', "listVideos", '')
    addDir('Meine Lieblings-Filmszene', baseUrl + '/videos/shows/meine-lieblings-filmszene', "listVideos", '')
    #addDir('Serien-Trailer', baseUrl + '/serien/videos/neueste/', "listVideos", '')
    xbmcplugin.endOfDirectory(pluginhandle)


def showSortDirection(url):
    addDir(translation(30006), url.replace("?version=1", "?sort_order=2&version=1"), "listVideos", '')
    addDir(translation(30003), url.replace("?version=1", "?sort_order=0&version=1"), "listVideos", '')
    addDir(translation(30004), url.replace("?version=1", "?sort_order=1&version=1"), "listVideos", '')
    addDir(translation(30005), url.replace("?version=1", "?sort_order=3&version=1"), "listVideos", '')
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(urlFull):
    xbmcplugin.setContent(pluginhandle, "movies")
    content = getUrl(urlFull)
    currentPage = -1
    maxPage = -1
    try:
        match = re.compile('<span class="navcurrpage">(.+?)</span> / (.+?)</li><li class="navnextbtn">', re.DOTALL).findall(content)
        currentPage = int(match[0][0])
        maxPage = int(match[0][1])
    except:
        try:
            match = re.compile('<em class="current">(.+?)</em></li><li class="navcenterdata"><span class="(.+?)">(.+?)</span>', re.DOTALL).findall(content)
            currentPage = int(match[0][0])
            maxPage = int(match[0][2])
        except:
            pass
    spl = content.split('class="datablock')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile("src='(.+?)'", re.DOTALL).findall(entry)
        thumb = match[0]
        match1 = re.compile("href='(.+?)'.*?>(.+?)</a>", re.DOTALL).findall(entry)
        match2 = re.compile('href="(.+?)".*?>(.+?)</a>', re.DOTALL).findall(entry)
        match = ""
        if match1:
            match=match1
        elif match2:
            match=match2
        url = match[0][0]
        title = match[0][1].replace("<strong>","").replace("</strong>","").replace("<span class='bold'>","").replace("</span>","").replace("\n","")
        if "Trailer" in title:
            title = title[:title.find("Trailer")]
        if "Teaser" in title:
            title = title[:title.find("Teaser")]
        title = cleanTitle(title)
        if showAllTrailers and "/trailer/" in url:
            url = url[:url.find("/trailer/")]+"/trailers/"
            addDir(title, baseUrl + url, "listTrailers", get_better_thumb(thumb))
        else:
            addLink(title, baseUrl + url, "playVideo", get_better_thumb(thumb))
    if currentPage < maxPage:
        sortNr = urlFull[urlFull.find('sort_order=')+11:]
        sortNr = sortNr[:sortNr.find('&')]
        urlNew = urlFull[:urlFull.find('?')]+"?page="+str(currentPage+1)+"&sort_order="+sortNr+"&version=1"
        addDir(translation(30007)+" ("+str(currentPage+1)+")", urlNew, "listVideos", '')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceView and ".html" in urlFull:
        xbmc.executebuiltin('Container.SetViewMode('+viewID+')')


def listTrailers(url, fanart):
    content = getUrl(url)
    content = content[:content.find('<div class="social">')]
    spl = content.split('<figure class="media-meta-fig">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        if match:
            url = baseUrl + match[0]
            match = re.compile('"src":"(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0]
            match = re.compile('<span class="title fs14 ">.+?>(.+?)</span>', re.DOTALL).findall(entry)
            title = match[0].replace("<b>","").replace("</b>"," -").replace("</a>","").replace("<strong>","").replace("</strong>","")
            title = title.replace(" DF", " - "+str(translation(30009))).replace(" OV", " - "+str(translation(30010)))
            title = cleanTitle(title)
            addSmallThumbLink(title, url, 'playVideo', get_better_thumb(thumb), fanart)
    xbmcplugin.endOfDirectory(pluginhandle)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&#38;", "&").replace("&#8230;", "...").replace("&#8211;", "-").replace("&#8220;", "-").replace("&#8221;", "-").replace("&#8217;", "'")
    title = title.replace("&#196;", "Ä").replace("&#220;", "Ü").replace("&#214;", "Ö").replace("&#228;", "ä").replace("&#252;", "ü").replace("&#246;", "ö").replace("&#223;", "ß").replace("&#176;", "°").replace("&#233;", "é").replace("&#224;", "à")
    title = title.strip()
    return title


def search():
    xbmcplugin.setContent(pluginhandle, "movies")
    keyboard = xbmc.Keyboard('', str(translation(30008)))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        content = getUrl(baseUrl + "/suche/1/?q="+search_string)
        spl = content.split('<tr><td style=" vertical-align:middle;">')
        for i in range(1, len(spl), 1):
            entry = spl[i]
            match = re.compile("src='(.+?)'", re.DOTALL).findall(entry)
            thumb = match[0]
            match = re.compile("'>\n(.+?)</a>", re.DOTALL).findall(entry)
            title = match[0].replace("<b>", "").replace("</b>", "")
            title = cleanTitle(title)
            match = re.compile("href='(.+?)'", re.DOTALL).findall(entry)
            url = baseUrl + match[0].replace(".html", "/trailers/")
            addDir(title, url, 'listTrailers', get_better_thumb(thumb))
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceView:
            xbmc.executebuiltin('Container.SetViewMode('+viewID+')')


def playVideo(url):
    content = getUrl(url)
    match = re.compile('"html5PathHD":"(.*?)"', re.DOTALL).findall(content)
    finalUrl=""
    if match[0] and match[0].startswith("http://"):
        finalUrl=match[0]
    else:
        match = re.compile('"refmedia":(.+?),', re.DOTALL).findall(content)
        media = match[0]
        match = re.compile('"relatedEntityId":(.+?),', re.DOTALL).findall(content)
        ref = match[0]
        match = re.compile('"relatedEntityType":"(.+?)"', re.DOTALL).findall(content)
        typeRef = match[0]
        content = getUrl(baseUrl + '/ws/AcVisiondataV4.ashx?media='+media+'&ref='+ref+'&typeref='+typeRef)
        finalUrl = ""
        match = re.compile('hd_path="(.+?)"', re.DOTALL).findall(content)
        finalUrl = match[0]
        if finalUrl.startswith("youtube:"):
            finalUrl = getYoutubeUrl(finalUrl.split(":")[1])
    if finalUrl:
        listitem = xbmcgui.ListItem(path=finalUrl)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name):
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        listitem = xbmcgui.ListItem(name)
        playlist.add(url, listitem)


def getYoutubeUrl(id):
    if xbox:
        url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
    else:
        url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
    return url


def get_better_thumb(thumb_url):
    thumb_url = '/'.join([
        p for p in thumb_url.split('/')
        if not p[0:2] in ('r_', 'c_', 'cx', 'b_', 'o_')
    ])
    if maxCoverResolution == "0":
        thumb_url = thumb_url.replace("/medias/", "/r_300_400/medias/")
        thumb_url = thumb_url.replace("/videothumbnails", "")
    elif maxCoverResolution == "1":
        thumb_url = thumb_url.replace("/medias/", "/r_600_800/medias/")
        thumb_url = thumb_url.replace("/videothumbnails", "")
    elif maxCoverResolution == "2":
        thumb_url = thumb_url.replace("/medias/", "/r_1200_1600/medias/")
        thumb_url = thumb_url.replace("/videothumbnails", "")
    return thumb_url


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


def addLink(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if useCoverAsFanart:
        liz.setProperty("fanart_image", iconimage)
    else:
        liz.setProperty("fanart_image", defaultFanart)
    liz.setProperty('IsPlayable', 'true')
    liz.addContextMenuItems([(translation(30011), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addSmallThumbLink(name, url, mode, iconimage, fanart=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('IsPlayable', 'true')
    if useCoverAsFanart:
        liz.setProperty("fanart_image", fanart)
    else:
        liz.setProperty("fanart_image", defaultFanart)
    liz.addContextMenuItems([(translation(30011), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)+"&fanart="+urllib.quote_plus(iconimage)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if useCoverAsFanart and iconimage:
        liz.setProperty("fanart_image", iconimage)
    else:
        liz.setProperty("fanart_image", defaultFanart)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
fanart = urllib.unquote_plus(params.get('fanart', ''))

if mode == "playVideo":
    playVideo(url)
elif mode == "queueVideo":
    queueVideo(url, name)
elif mode == "showSortDirection":
    showSortDirection(url)
elif mode == "listTrailers":
    listTrailers(url, fanart)
elif mode == "listVideos":
    listVideos(url)
elif mode == "search":
    search()
else:
    index()
