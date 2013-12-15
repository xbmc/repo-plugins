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

addon = xbmcaddon.Addon()
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
forceViewMode = addon.getSetting("forceViewMode") == "true"
viewMode = str(addon.getSetting("viewMode"))
translation = addon.getLocalizedString
baseUrl = "http://www.upworthy.com"


def index():
    addDir(translation(30002), "", 'listLatestVideos', "")
    content = getUrl(baseUrl)
    content = content[content.find('<li class="browse">'):]
    content = content[:content.find('</ul>')]
    match = re.compile('<li><a href="(.+?)">(.+?)</a></li>', re.DOTALL).findall(content)
    for genreId, title in match:
        addDir(cleanTitle(title), baseUrl+"/"+genreId, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    xbmcplugin.setContent(pluginhandle, "episodes")
    content = getUrl(url)
    spl = content.split("<div class='nugget clickable analytic_event'")
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<h3>.+?>(.+?)<', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        match = re.compile('data-href="(.+?)"', re.DOTALL).findall(entry)
        url = baseUrl+match[0]
        match = re.compile('<time datetime="(.+?)"', re.DOTALL).findall(entry)
        date = match[0]
        match = re.compile('class="thumb"><img alt=".+?src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace("//","http://")
        #Not working on all thumbs
        #thumb = match[0].replace("//","http://").replace("/web_287","/web_600")
        addLink(title, url, 'playVideo', thumb, title, date)
    match = re.compile('<li><a rel="next" href="(.+?)"', re.DOTALL).findall(content)
    if match:
        addDir(translation(30001), baseUrl+match[0], 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listLatestVideos():
    xbmcplugin.setContent(pluginhandle, "episodes")
    content = getUrl("http://feeds.feedburner.com/upworthy?format=xml")
    months = {"Jan":"1","Feb":"2","Mar":"3","Apr":"4","May":"5","Jun":"6","Jul":"7","Aug":"8","Sep":"9","Oct":"10","Nov":"11","Dec":"12"}
    spl = content.split('<item>')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<title>(.+?)</title>', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        match = re.compile('<description>(.+?)</description>', re.DOTALL).findall(entry)
        description = match[0]
        match = re.compile('<pubDate>(.+?)</pubDate>', re.DOTALL).findall(entry)
        pubDate = match[0]
        pubDate = pubDate[:pubDate.find("+")-1]
        match = re.compile('.+?, (.+?) (.+?) (.+?) ', re.DOTALL).findall(pubDate)
        date = match[0][2]+"-"+months[match[0][1]]+"-"+match[0][0]
        match = re.compile('<enclosure url="(.+?)"', re.DOTALL).findall(entry)
        #thumb = match[0].replace("//","http://")
        #Not working on all thumbs
        thumb = match[0].replace("//","http://").replace("/rss_77","/web_287")
        matchYoutube = re.compile('youtube.com/embed/(.+?)\\?', re.DOTALL).findall(description)
        matchVimeo = re.compile('player.vimeo.com/video/(.+?)\\?', re.DOTALL).findall(description)
        description = description[description.find("&lt;p&gt;")+9:]
        description = description[:description.find("&lt;/p&gt;")]
        description = pubDate+"\n"+description
        if matchYoutube:
            addLink(title, matchYoutube[0], 'playYoutubeVideo', thumb, description, date)
        elif matchVimeo:
            addLink(title, matchVimeo[0], 'playVimeoVideo', thumb, description, date)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    content = getUrl(url)
    matchYoutube = re.compile('youtube.com/embed/(.+?)\\?', re.DOTALL).findall(content)
    matchVimeo = re.compile('player.vimeo.com/video/(.+?)\\?', re.DOTALL).findall(content)
    finalUrl = ""
    if matchYoutube:
        finalUrl = getYoutubeUrl(matchYoutube[0])
    elif matchVimeo:
        finalUrl = getVimeoUrl(matchVimeo[0])
    if finalUrl:
        listItem = xbmcgui.ListItem(path=finalUrl)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listItem)
    else:
        xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30003))+',5000)')


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


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#038;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.replace("&#8211;", "-").replace("&#8220;", "-").replace("&#8221;", "-").replace("&#8217;", "'").replace("&#8216;", "‘").replace("&#x27;", "'")
    title = title.strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.2; WOW64; rv:25.0) Gecko/20100101 Firefox/25.0')
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


def addLink(name, url, mode, iconimage, desc, date):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Aired": date, "Episode": 1})
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
elif mode == 'listLatestVideos':
    listLatestVideos()
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'playYoutubeVideo':
    playYoutubeVideo(url)
elif mode == 'playVimeoVideo':
    playVimeoVideo(url)
else:
    index()
