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
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(id='plugin.video.infinitylist_com')
forceViewMode = addon.getSetting("forceViewMode") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
viewMode = str(addon.getSetting("viewMode"))
translation = addon.getLocalizedString
urlMain = "http://www.infinitylist.com"


def index():
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    addDir(translation(30002), "ALL", 'listVideosMain', "")
    content = getUrl(urlMain)
    content = content[content.find('<ul id="mainMenu" class="menu">'):]
    content = content[:content.find('</ul>')]
    match = re.compile('<li class="menuItem-.+?"><h2><a href="http://www.infinitylist.com/(.+?)/">(.+?)</a></h2></li>', re.DOTALL).findall(content)
    for id, title in match:
        addDir(title, id, 'listVideosMain', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideosMain(id):
    if id == "ALL":
        addDir(translation(30003), urlMain+"/page/1/?burnt_inline_load=true", 'listVideos', "")
        addDir(translation(30004), urlMain+"/shuffle/?burnt_inline_load=true", 'playRandom', "")
        addDir(translation(30005), urlMain+"/weeks-most-hyped/?burnt_inline_load=true", 'listVideos', "")
        addDir(translation(30006), urlMain+"/months-most-hyped/?burnt_inline_load=true", 'listVideos', "")
        addDir(translation(30007), urlMain+"/most-hyped/?burnt_inline_load=true", 'listVideos', "")
    else:
        addDir(translation(30003), urlMain+"/"+id+"/page/1/?burnt_inline_load=true", 'listVideos', "")
        addDir(translation(30004), urlMain+"/"+id+"/shuffle/?burnt_inline_load=true", 'playRandom', "")
        addDir(translation(30005), urlMain+"/"+id+"/weeks-most-hyped/?burnt_inline_load=true", 'listVideos', "")
        addDir(translation(30006), urlMain+"/"+id+"/months-most-hyped/?burnt_inline_load=true", 'listVideos', "")
        addDir(translation(30007), urlMain+"/"+id+"/most-hyped/?burnt_inline_load=true", 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    content = getUrl(url)
    if '<a class="nextLink"' in content:
        content = content[content.find('<a class="nextLink"'):]
    elif '<nav id="highlightMySection"' in content:
        content = content[content.find('<nav id="highlightMySection"'):]
    spl = content.split('<div id="videoPost-')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<h5 class="date">(.+?)</h5>', re.DOTALL).findall(entry)
        date = ""
        if match:
            date = match[0]
        match = re.compile('data-duration-in-seconds="(.*?)"', re.DOTALL).findall(entry)
        length = ""
        if match:
            if match[0]:
                length = str(int(match[0])/60)
                if length == "0":
                    length = "1"
        match = re.compile('<span class="text">(.+?)</span>', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        match = re.compile('data-thumbnail-image-u-r-l="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]
        matchYoutube = re.compile('data-youtube-video-i-d="(.+?)"', re.DOTALL).findall(entry)
        matchVimeo = re.compile('data-vimeo-video-i-d="(.+?)"', re.DOTALL).findall(entry)
        matchYoutube2 = re.compile('http://www.youtube.com/embed/(.+?)\\?', re.DOTALL).findall(entry)
        matchVimeo2 = re.compile('http://player.vimeo.com/video/(.+?)\\?', re.DOTALL).findall(entry)
        url = ""
        if matchYoutube:
            addLink(title, matchYoutube[0], 'playYoutubeVideo', thumb, date, length)
        elif matchVimeo:
            addLink(title, matchVimeo[0], 'playVimeoVideo', thumb, date, length)
        elif matchYoutube2:
            addLink(title, matchYoutube2[0], 'playYoutubeVideo', thumb, date, length)
        elif matchVimeo2:
            addLink(title, matchVimeo2[0], 'playVimeoVideo', thumb, date, length)
    match = re.compile('<div id="featuredContentPageNumbers" class="featuredContentPageNumbers pageNavigation infinite">.+?<a href="(.+?)">.+?</a>', re.DOTALL).findall(content)
    if match:
        url = match[0]+"?burnt_inline_load=true"
        addDir(translation(30001), url, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playYoutubeVideo(id):
    listItem = xbmcgui.ListItem(path=getYoutubeUrl(id))
    xbmcplugin.setResolvedUrl(pluginhandle, True, listItem)


def playVimeoVideo(id):
    listItem = xbmcgui.ListItem(path=getVimeoUrl(id))
    xbmcplugin.setResolvedUrl(pluginhandle, True, listItem)


def getYoutubeUrl(id):
    if xbox:
        url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
    else:
        url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
    return url


def getVimeoUrl(id):
    if xbox:
        url = "plugin://video/Vimeo/?path=/root/video&action=play_video&videoid=" + id
    else:
        url = "plugin://plugin.video.vimeo/?path=/root/video&action=play_video&videoid=" + id
    return url


def playRandom(url):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    content = getUrl(url)
    spl = content.split('<div id="videoPost-')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<span class="text">(.+?)</span>', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        matchYoutube = re.compile('data-youtube-video-i-d="(.+?)"', re.DOTALL).findall(entry)
        matchVimeo = re.compile('data-vimeo-video-i-d="(.+?)"', re.DOTALL).findall(entry)
        matchYoutube2 = re.compile('http://www.youtube.com/embed/(.+?)\\?', re.DOTALL).findall(entry)
        matchVimeo2 = re.compile('http://player.vimeo.com/video/(.+?)\\?', re.DOTALL).findall(entry)
        url = ""
        if matchYoutube:
            url = getYoutubeUrl(matchYoutube[0])
        elif matchVimeo:
            url = getVimeoUrl(matchVimeo[0])
        elif matchYoutube2:
            url = getYoutubeUrl(matchYoutube2[0])
        elif matchVimeo2:
            url = getVimeoUrl(matchVimeo2[0])
        if url:
            listitem = xbmcgui.ListItem(title)
            playlist.add(url, listitem)
    xbmc.Player().play(playlist)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#038;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.replace("&#8211;", "-").replace("&#8220;", "-").replace("&#8221;", "-").replace("&#8217;", "'").replace("&#8216;", "‘")
    title = title.strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0')
    req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
    req.add_header('Accept-Language', 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3')
    req.add_header('Accept-Encoding', 'deflate')
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


def addLink(name, url, mode, iconimage, desc, length):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": length})
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
elif mode == 'listVideosMain':
    listVideosMain(url)
elif mode == 'playYoutubeVideo':
    playYoutubeVideo(url)
elif mode == 'playVimeoVideo':
    playVimeoVideo(url)
elif mode == 'playRandom':
    playRandom(url)
else:
    index()
