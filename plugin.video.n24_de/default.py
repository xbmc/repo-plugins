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
addonId = 'plugin.video.n24_de'
addon = xbmcaddon.Addon(id=addonId)
translation = addon.getLocalizedString
baseUrl = "http://www.n24.de"


def index():
    addDir(translation(30001), baseUrl+"/n24/Mediathek/videos/q?query=&hitsPerPage=50&pageNum=1&recent=0&docType=CMVideo&category=&from=&to=&taxonomy=&type=&sort=new", 'listVideos', "")
    addDir(translation(30002), baseUrl+"/n24/Mediathek/videos/q?query=&hitsPerPage=50&pageNum=1&recent=0&docType=CMVideo&category=&from=&to=&taxonomy=&type=888&sort=new", 'listVideos', "")
    addDir(translation(30003), baseUrl+"/n24/Mediathek/videos/q?query=&hitsPerPage=50&pageNum=1&recent=0&docType=CMVideo&category=&from=&to=&taxonomy=&type=6&sort=new", 'listVideos', "")
    addDir(translation(30004), baseUrl+"/n24/Mediathek/videos/q?query=&hitsPerPage=50&pageNum=1&recent=0&docType=CMVideo&category=&from=&to=&taxonomy=&type=32986&sort=new", 'listVideos', "")
    addDir(translation(30008), "", 'search', "")
    addLink(translation(30005), "http://www.n24.de/n24/Mediathek/Live/", 'playVideo', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    urlMain = url
    content = getUrl(url)
    spl = content.split('<div class="content">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('src=&#034;(.+?)&#034;', re.DOTALL).findall(entry)
        thumb = match[0]
        match = re.compile('<h4>.+?<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
        url = baseUrl+match[0][0]
        title = match[0][1]
        title = cleanTitle(title)
        addLink(title, url, 'playVideo', thumb)
    match = re.compile('&pageNum=(.+?)&', re.DOTALL).findall(urlMain)
    currentPage = match[0]
    nextPage = str(int(currentPage)+1)
    urlNew = urlMain.replace("&pageNum="+currentPage+"&", "&pageNum="+nextPage+"&")
    addDir(translation(30006), urlNew, "listVideos", '')
    xbmcplugin.endOfDirectory(pluginhandle)


def playVideo(url):
    content = getUrl(url)
    matchBase = re.compile('videoFlashconnectionUrl = "(.+?)"', re.DOTALL).findall(content)
    matchPlaypath = re.compile('videoFlashSource = "(.+?)"', re.DOTALL).findall(content)
    if matchPlaypath:
      if url == "http://www.n24.de/n24/Mediathek/Live/":
          filename = matchBase[0] + " playpath="+matchPlaypath[0] + " swfUrl=http://www.n24.de/_swf/HomePlayer.swf live=true timeout=60"
      else:
          filename = matchBase[0] + " playpath="+matchPlaypath[0] + " swfUrl=http://www.n24.de/_swf/HomePlayer.swf"
      listitem = xbmcgui.ListItem(path=filename)
      xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    else:
      xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30009).encode('utf-8')+',5000)')


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def search():
    keyboard = xbmc.Keyboard('', translation(30008))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        listVideos(baseUrl+"/n24/Mediathek/videos/q?query="+search_string+"&hitsPerPage=50&pageNum=1&recent=0&docType=CMVideo&category=&from=&to=&taxonomy=&type=&sort=new")


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


def addLink(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)+"&name="+urllib.quote_plus(name)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('IsPlayable', 'true')
    liz.addContextMenuItems([(translation(30007), 'RunPlugin(plugin://'+addonId+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)
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
elif mode == 'playLiveStream':
    playLiveStream(url)
elif mode == 'queueVideo':
    queueVideo(url, name)
elif mode == 'search':
    search()
else:
    index()
