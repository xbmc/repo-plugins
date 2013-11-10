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
addonID = addon.getAddonInfo('id')
translation = addon.getLocalizedString
forceViewMode = addon.getSetting("forceViewMode") == "true"
viewMode = str(addon.getSetting("viewMode"))
autoPlay = int(addon.getSetting("autoPlay"))
urlMain = "http://www.howstuffworks.com"
defaultIcon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')


def index():
    addDir(translation(30002), urlMain+"/videos", "listType", defaultIcon)
    addDir(translation(30005), "", "listCollections", defaultIcon)
    addDir(translation(30006), "", "listCats", defaultIcon)
    addDir(translation(30007), "", "search", defaultIcon)
    content = getUrl(urlMain+"/videos")
    content = content[content.find('<div class="module module-slider slider-paged pre shows"'):]
    content = content[:content.find('<div class="slider-ui">')]
    spl = content.split('<div class="fragment-media  media-vertical paged-member member-')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<div class="media-title">.+?>(.+?)</a>', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]  # .replace("/w_160/w_640/","/h_720/")
        addDir(title, url, 'listType', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listType(url):
    addDir(translation(30003), url, "listLatest", defaultIcon)
    addDir(translation(30004), url, "listMostWatched", defaultIcon)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listLatest(url):
    content = getUrl(url)
    spl = content.split('<div class="fragment-media  media-vertical grid-member member-')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<div class="media-title">.+?>(.+?)</a>', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0] # .replace("/w_160/w_640/","/h_720/")
        addLink(title, url, 'playVideo', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listMostWatched(url):
    content = getUrl(url)
    content = content[content.find('<div class="module module-slider slider-paged pre most-watched"'):]
    content = content[:content.find('<div class="slider-ui">')]
    spl = content.split('<div class="fragment-media  media-vertical paged-member member-')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<div class="media-title">.+?>(.+?)</a>', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]  # .replace("/w_160/w_640/","/h_720/")
        addLink(title, url, 'playVideo', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listCollections():
    content = getUrl(urlMain+"/videos")
    content = content[content.find('<div class="module module-slider slider-paged pre top-collections"'):]
    content = content[:content.find('<div class="slider-ui">')]
    spl = content.split('<div class="fragment-media  media-vertical paged-member member-')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<div class="media-title">.+?>(.+?)</a>', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]  # .replace("/w_160/w_640/","/h_720/")
        addDir(title, url, 'listType', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listCats():
    content = getUrl(urlMain+"/videos")
    content = content[content.find('<ul id="subChannelNav">'):]
    content = content[:content.find('</ul>')]
    match = re.compile('<a class="event-click-tracking" href="(.+?)".+?>(.+?)</a>', re.DOTALL).findall(content)
    for url, title in match:
        addDir(cleanTitle(title), url, 'listType', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def search():
    keyboard = xbmc.Keyboard('', translation(30003))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        listSearch('http://videos.howstuffworks.com/search.php?media=video&terms='+search_string)


def listSearch(url):
    results = []
    content = getUrl(url)
    spl = content.split('<div class="item video">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile('<h4>Time: (.+?)</h4>', re.DOTALL).findall(entry)
        length = match[0]
        if length.startswith("00:"):
            length="1"
        match = re.compile('<td colspan="2">(.+?)</td>', re.DOTALL).findall(entry)
        desc = match[0]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]
        if url not in results:
            results.append(url)
            addLink(title, url, 'playVideo', thumb, desc, length)
    if content.find('<div class="more-results">') > 0:
        content = content[content.find('<div class="more-results">'):]
        content = content[:content.find('</div>')]
        spl = content.split("<a href=")
        for i in range(1, len(spl), 1):
            entry = spl[i]
            if '<span class="uppercase">next</span>' in entry:
                match = re.compile('"(.+?)"', re.DOTALL).findall(entry)
                addDir(translation(30001), match[0].replace("&amp;", "&"), 'listSearch', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    content = getUrl(url)
    match = re.compile("m3u8 			: '(.*?)'", re.DOTALL).findall(content)
    finalUrl = match[0]
    if finalUrl:
        listitem = xbmcgui.ListItem(path=finalUrl)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    else:
        match = re.compile("reference_id 	: '(.+?)-title'", re.DOTALL).findall(content)
        content = getUrl("http://static.discoverymedia.com/videos/components/hsw/"+match[0]+"-title/smil-service.smil")
        match = re.compile('<meta name="httpBase".+?content="(.+?)"', re.DOTALL).findall(content)
        base = match[0]
        maxBitrate = 0
        match = re.compile('<video src="(.+?)" system-bitrate="(.+?)"', re.DOTALL).findall(content)
        for urlTemp, bitrateTemp in match:
            bitrate = int(bitrateTemp)
            if bitrate > maxBitrate:
                maxBitrate = bitrate
                finalUrl = urlTemp
        finalUrl = base+"/"+finalUrl+"?v=2.6.8&fp=&r=&g="
        listitem = xbmcgui.ListItem(path=finalUrl)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        if autoPlay > 0:
            xbmc.sleep(autoPlay*1000)
            if xbmc.Player().isPlaying() == True and int(xbmc.Player().getTime()) == 0:
                xbmc.Player().pause()


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
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
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, desc="", length=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": length})
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
elif mode == 'listLatest':
    listLatest(url)
elif mode == 'listType':
    listType(url)
elif mode == 'listMostWatched':
    listMostWatched(url)
elif mode == 'listCollections':
    listCollections()
elif mode == 'listCats':
    listCats()
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
elif mode == 'listSearch':
    listSearch(url)
else:
    index()
