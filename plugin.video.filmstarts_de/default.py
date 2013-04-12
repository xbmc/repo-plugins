#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import xbmcplugin
import xbmcaddon
import xbmcgui
import re
import sys

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addonId = 'plugin.video.filmstarts_de'
addon = xbmcaddon.Addon(id=addonId)
translation = addon.getLocalizedString
showAllTrailers = addon.getSetting("showAllTrailers") == "true"
forceViewMode = addon.getSetting("forceViewMode") == "true"
useCoverAsFanart = addon.getSetting("useCoverAsFanart") == "true"
viewMode = str(addon.getSetting("viewMode"))
maxCoverResolution = addon.getSetting("maxCoverResolution")
baseUrl = "http://www.filmstarts.de"


def index():
    addDir('Trailer: '+translation(30008), '', "search", '')
    addDir('Trailer: '+translation(30001), baseUrl + '/trailer/aktuell_im_kino.html?version=1', "showSortDirection", '')
    addDir('Trailer: '+translation(30002), baseUrl + '/trailer/bald_im_kino.html?version=1', "showSortDirection", '')
    addDir('Filmstarts: Interviews', baseUrl + '/trailer/interviews/', "listVideosInterview", '')
    addDir('Filmstarts: Fünf Sterne', baseUrl + '/videos/shows/funf-sterne', "listVideosMagazin", '')
    addDir('Filmstarts: Fehlerteufel', baseUrl + '/videos/shows/filmstarts-fehlerteufel', "listVideosMagazin", '')
    addDir('Meine Lieblings-Filmszene', baseUrl + '/videos/shows/meine-lieblings-filmszene', "listVideosMagazin", '')
    addDir('Serien-Trailer', baseUrl + '/trailer/serien/', "listVideosTV", '')
    xbmcplugin.endOfDirectory(pluginhandle)


def showSortDirection(url):
    addDir(translation(30006), url.replace("?version=1", "?sort_order=2&version=1"), "listVideosTrailer", '')
    addDir(translation(30003), url.replace("?version=1", "?sort_order=0&version=1"), "listVideosTrailer", '')
    addDir(translation(30004), url.replace("?version=1", "?sort_order=1&version=1"), "listVideosTrailer", '')
    addDir(translation(30005), url.replace("?version=1", "?sort_order=3&version=1"), "listVideosTrailer", '')
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(urlFull):
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
    if mode == "listVideosTrailer":
        match = re.compile('<img src=\'(.+?)\' alt=".+?" title=".+?" />\n</span>\n</div>\n<div class="contenzone">\n<div class="titlebar">\n<a class="link" href="(.+?)">\n<span class=\'bold\'>(.+?)</span>', re.DOTALL).findall(content)
        for thumb, url, title in match:
            if showAllTrailers:
                url = url[:url.find("/trailer/")]+"/trailers/"
                addDir(title, baseUrl + url, "listTrailers", get_better_thumb(thumb))
            else:
                addLink(title, baseUrl + url, "playVideo", get_better_thumb(thumb))
    elif mode == "listVideosMagazin":
        if currentPage == 1:
            match = re.compile('<a href=".+?">\n<img src="(.+?)" alt="" />\n</a>\n</div>\n<div style=".+?">\n<h2 class=".+?" style=".+?"><b>.+?</b> (.+?)</h2><br />\n<span style=".+?" class="purehtml fs11">\n.+?<a class="btn" href="(.+?)"', re.DOTALL).findall(content)
            for thumb, title, url in match:
                addSmallThumbLink(title, baseUrl + url, "playVideo", get_better_thumb(thumb))
        match = re.compile('<img src=\'(.+?)\' alt=".+?" title=".+?" />\n</span>\n</div>\n<div class="contenzone">\n<div class="titlebar">\n<a href=\'(.+?)\' class="link">\n<span class=\'bold\'><b>.+?</b> (.+?)</span>', re.DOTALL).findall(content)
        for thumb, url, title in match:
            addSmallThumbLink(title, baseUrl + url, "playVideo", get_better_thumb(thumb))
    elif mode == "listVideosInterview":
        match = re.compile('<img src=\'(.+?)\'.+?</span>\n</div>\n<div class="contenzone">\n<div class="titlebar">\n<a.+?href=\'(.+?)\'>\n<span class=\'bold\'>\n(.+?)\n</span>(.+?)\n</a>', re.DOTALL).findall(content)
        for thumb, url, title1, title2 in match:
            addSmallThumbLink(title1+title2, baseUrl + url, "playVideo", get_better_thumb(thumb))
    elif mode == "listVideosTV":
        spl = content.split('<div class="datablock vpadding10b">')
        for i in range(1, len(spl), 1):
            entry = spl[i]
            match = re.compile("<a href='(.+?)'>", re.DOTALL).findall(entry)
            url = match[0]
            match = re.compile("<img src='(.+?)'", re.DOTALL).findall(entry)
            thumb = match[0]
            if "<span class='bold'>" in entry:
                match = re.compile("<span class='bold'>(.+?)</span>(.+?)<br />", re.DOTALL).findall(entry)
                title = match[0][0]+' '+match[0][1]
            else:
                match = re.compile("<a href='(.+?)'>\n(.+?)<br />", re.DOTALL).findall(entry)
                title = match[0][1]
            addSmallThumbLink(title, baseUrl + url, "playVideo", get_better_thumb(thumb))
    if currentPage < maxPage:
        urlNew = ""
        if mode == "listVideosTrailer":
            sortNr = urlFull[urlFull.find('sort_order=')+11:]
            sortNr = sortNr[:sortNr.find('&')]
            urlNew = urlFull[:urlFull.find('?')]+"?page="+str(currentPage+1)+"&sort_order="+sortNr+"&version=1"
        elif '?page=' in urlFull and mode in ["listVideosMagazin", "listVideosInterview", "listVideosTV"]:
            match = re.compile('http://www.filmstarts.de/(.+?)?page=(.+?)', re.DOTALL).findall(urlFull)
            urlNew = baseUrl + '/'+match[0][0]+'page='+str(currentPage+1)
        elif not '?page=' in urlFull and mode in ["listVideosMagazin", "listVideosInterview", "listVideosTV"]:
            urlNew = urlFull + "?page="+str(currentPage+1)
        addDir(translation(30007)+" ("+str(currentPage+1)+")", urlNew, mode, '')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listTrailers(url, fanart):
    content = getUrl(url)
    splMain = content.split('<div class="media_list_02')
    for i in range(1, len(splMain), 1):
        entryMain = splMain[i]
        entryMain = entryMain[:entryMain.find('</div>')]
        spl = entryMain.split("<li>")
        for i in range(1, len(spl), 1):
            entry = spl[i]
            match = re.compile("src='(.+?)'", re.DOTALL).findall(entry)
            thumb = match[0]
            match = re.compile("title='(.+?)'", re.DOTALL).findall(entry)
            title = match[0].replace(" DF", " - "+str(translation(30009))).replace(" OV", " - "+str(translation(30010)))
            title = cleanTitle(title)
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            if match:
                url = baseUrl + match[0]
                addSmallThumbLink(title, url, 'playVideo', get_better_thumb(thumb), fanart)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&#38;", "&").replace("&#8230;", "...").replace("&#8211;", "-").replace("&#8220;", "-").replace("&#8221;", "-").replace("&#8217;", "'")
    title = title.replace("&#196;", "Ä").replace("&#220;", "Ü").replace("&#214;", "Ö").replace("&#228;", "ä").replace("&#252;", "ü").replace("&#246;", "ö").replace("&#223;", "ß").replace("&#176;", "°").replace("&#233;", "é").replace("&#224;", "à")
    title = title.strip()
    return title


def search():
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
        if forceViewMode:
            xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    content = getUrl(url)
    match1 = re.compile('"cmedia" : (.+?),', re.DOTALL).findall(content)
    match2 = re.compile("cmedia: '(.+?)'", re.DOTALL).findall(content)
    if match1:
        media = match1[0]
    elif match2:
        media = match2[0]
    match1 = re.compile('"ref" : (.+?),', re.DOTALL).findall(content)
    match2 = re.compile("ref: '(.+?)'", re.DOTALL).findall(content)
    if match1:
        ref = match1[0]
    elif match2:
        ref = match2[0]
    match1 = re.compile('"typeRef" : "(.+?)"', re.DOTALL).findall(content)
    match2 = re.compile("typeRef: '(.+?)'", re.DOTALL).findall(content)
    if match1:
        typeRef = match1[0]
    elif match2:
        typeRef = match2[0]
    content = getUrl(baseUrl + '/ws/AcVisiondataV4.ashx?media='+media+'&ref='+ref+'&typeref='+typeRef)
    finalUrl = ""
    match1 = re.compile('/nmedia/youtube:(.+?)"', re.DOTALL).findall(content)
    match2 = re.compile('hd_path="(.+?)"', re.DOTALL).findall(content)
    if match1:
        finalUrl = getYoutubeUrl(match1[0])
    elif match2:
        finalUrl = match2[0]
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
        if not p[0:2] in ('r_', 'c_', 'cx_', 'b_', 'o_')
    ])
    if maxCoverResolution == "0":
        thumb_url = thumb_url.replace("/medias/", "/r_300_400/medias/")
    elif maxCoverResolution == "1":
        thumb_url = thumb_url.replace("/medias/", "/r_600_800/medias/")
    elif maxCoverResolution == "2":
        thumb_url = thumb_url.replace("/medias/", "/r_1200_1600/medias/")
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
    liz.setProperty('IsPlayable', 'true')
    liz.addContextMenuItems([(translation(30011), 'RunPlugin(plugin://'+addonId+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
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
    liz.addContextMenuItems([(translation(30011), 'RunPlugin(plugin://'+addonId+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)+"&fanart="+urllib.quote_plus(iconimage)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if useCoverAsFanart:
        liz.setProperty("fanart_image", iconimage)
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
elif mode in ["listVideosMagazin", "listVideosInterview", "listVideosTV", "listVideosTrailer"]:
    listVideos(url)
elif mode == "search":
    search()
else:
    index()
