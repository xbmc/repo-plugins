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

#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
addonID = 'plugin.video.welt_der_wunder'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
forceViewMode = addon.getSetting("forceView") == "true"
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
viewMode = str(addon.getSetting("viewID"))
translation = addon.getLocalizedString
urlMain = "http://www.wissensthek.de"


def index():
    addDir("LiveTV", "", 'listLive', icon)
    addDir("Mediathek", "", 'videosMain', icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def videosMain():
    #addDir("Aktuelles", urlMain+"/aktuelles.html", 'listVideos', "")
    addDir("Mensch & Natur", urlMain+"/mensch-natur.html", 'listVideos', "")
    addDir("Technik & Weltraum", urlMain+"/technik-weltraum.html", 'listVideos', "")
    addDir("Fragen & Antworten", urlMain+"/fragen-antworten.html", 'listVideos', "")
    addDir("Service & Lifestyle", urlMain+"/service-lifestyle.html", 'listVideos', "")
    addDir("Action & Highspeed", urlMain+"/action-highspeed.html", 'listVideos', "")
    addDir("Gadgets & Tests", urlMain+"/gadgets-tests.html", 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listLive():
    content = getUrl("http://www.weltderwunder.tv/index.php?id=133")
    spl = content.split('<tr class="pionteve_programs">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<td class="pionteve_title">(.+?)</td>', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        match = re.compile('<i><span class=".+?">.+?</span>.+?-(.+?)</i>', re.DOTALL).findall(entry)
        time = match[0].strip()[:5]
        title = time+" - "+title
        #match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        #thumb = match[0]
        thumb = icon
        addLink(title, "", 'playLive', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    xbmcplugin.setContent(pluginhandle, "episodes")
    content = getUrl(url)
    spl = content.split('<div class="description-box">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('class="test">(.+?)<', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        match = re.compile('/entry_id/(.+?)/', re.DOTALL).findall(entry)
        id = match[0]
        match = re.compile('<div class="text-desc">.+?<p>(.+?)</p>', re.DOTALL).findall(entry)
        desc = ""
        if match:
            desc = match[0]
        match = re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry)
        date = match[0]
        splDate = date.split(".")
        date = splDate[2]+"-"+splDate[1]+"-"+splDate[0]
        match = re.compile('<span class="time-video">(.+?)</span>', re.DOTALL).findall(entry)
        length = match[0]
        if length.startswith("00:"):
            length = 1
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace("/width/200/height/131/","/width/600/height/393/")
        thumb = thumb[:thumb.rfind("/")]
        addLink(title, id, 'playVideo', thumb, length, desc, date)
    content = content[content.find('<div class="pager">'):]
    content = content[:content.find('</div>')]
    content = content[content.rfind("target='_self'"):]
    match = re.compile('<li><a href="(.+?)" >(.+?)</a></li>', re.DOTALL).findall(content)
    nextUrl = ""
    for url, title in match:
        if "&raquo;" in title:
            nextUrl = url
    if nextUrl:
        if " " in nextUrl:
          nextUrl = nextUrl[:nextUrl.find(" ")]
        addDir(translation(30001), urlMain+"/"+nextUrl, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(id):
    listitem = xbmcgui.ListItem(path="http://medianac.nacamar.de/p/249/sp/24900/raw/entry_id/"+id+"/version/0")
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def playLive():
    listitem = xbmcgui.ListItem(path="rtmp://mf.weltderwunder.c.nmdn.net:1935/wdw_pc playpath=wdwpc.sdp swfUrl=http://medianac.nacamar.de/p/249/sp/24900/flash/kdp3/v3.4.10.1/kdp3.swf pageUrl=http://www.weltderwunder.tv/live.html")
    listitem.setInfo(type='Video', infoLabels={'Title':'LIVE: Welt der Wunder TV'})
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


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


def addLink(name, url, mode, iconimage, length="", desc="", date=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Duration": length, "Plot": desc, "Aired": date, "Episode": 1})
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
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'listLive':
    listLive()
elif mode == 'playLive':
    playLive()
elif mode == 'videosMain':
    videosMain()
else:
    index()
