#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import random
import re
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

addon = xbmcaddon.Addon()
pluginhandle = int(sys.argv[1])
forceViewMode = addon.getSetting("forceViewMode") == "true"
viewMode = str(addon.getSetting("viewMode"))
urlMain = "http://pantoffel.tv"


def index():
    xbmcplugin.setContent(pluginhandle, "episodes")
    content = getUrl(urlMain+"/magazin/")
    spl = content.split('<h1 class="magtitle"')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('>(.+?)<', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        match = re.compile('<small class="pull-right">(.+?)</small>', re.DOTALL).findall(entry)
        desc1 = cleanTitle(match[0])
        match = re.compile('<p style=".+?">(.+?)</p>', re.DOTALL).findall(entry)
        desc2 = cleanTitle(match[0])
        desc = desc1+"\n"+desc2
        if " " in title:
            nr = title.split(" ")[1]
        else:
            nr = "1"
        length = desc1.split(" ")[0]
        date = desc1.split("/")[1].strip()
        splDate = date.split(".")
        date = splDate[2]+"-"+splDate[1]+"-"+splDate[0]
        match = re.compile('<a href="/watch/(.+?)"', re.DOTALL).findall(entry)
        url = urlMain+"/watch/"+match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]
        addLink(title, url, 'playVideo', thumb, length, desc, date, nr)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
    xbmcplugin.endOfDirectory(pluginhandle)


def playVideo(url):
    content = getUrl(url)
    content  = content[content.find('playlist = ['):]
    content  = content[:content.find('];')]
    match = re.compile("'(.+?)'", re.DOTALL).findall(content)
    urlFull="stack://"
    for file in match:
        urlFull += 'http://dl' + str(random.randint(2, 3)) + '.fernsehkritik.tv/deliver/ptv/limited/ptv' + file + " , "
    urlFull=urlFull[:-3]
    listitem = xbmcgui.ListItem(path=urlFull)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&#38;", "&").replace("&#8230;", "...").replace("&#8211;", "-").replace("&#8220;", "-").replace("&#8221;", "-").replace("&#8217;", "'")
    title = title.replace("&#196;", "Ä").replace("&#220;", "Ü").replace("&#214;", "Ö").replace("&#228;", "ä").replace("&#252;", "ü").replace("&#246;", "ö").replace("&#223;", "ß").replace("&#176;", "°").replace("&#233;", "é").replace("&#224;", "à")
    title = title.strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
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


def addLink(name, url, mode, iconimage, length, desc, date, nr):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Duration": length, "Plot": desc, "Aired": date, "Episode": nr})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))

if mode == 'playVideo':
    playVideo(url)
else:
    index()
