#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import json
import xbmcplugin
import xbmcgui
import xbmcaddon

addonID = 'plugin.video.cbsnews_com'
addon = xbmcaddon.Addon(id=addonID)
#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
forceViewMode = addon.getSetting("forceView") == "true"
viewID = str(addon.getSetting("viewIDNew"))
urlMain = "http://www.cbsnews.com"


def index():
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    addDir("- "+translation(30002), "", "search", icon)
    content = getUrl(urlMain+"/videos")
    match = re.compile('<a href="/videos/topics/([^\/]+)/"([^>]+)?>([^<]+)</a>', re.DOTALL).findall(content)
    for id, ignored_grouping, title in match:
        if id=="48-hours":
            addDir(title, urlMain+"/latest/"+id+"/full-episodes/1", 'listEpisodes', icon)
        elif id=="60-minutes":
            addDir(title, id, 'list60MinutesMain', icon)
        elif id=="evening-news":
            addDir(title, id, 'listEveningNewsMain', icon)
        else:
            addDir2(title.replace("Popular","- Popular"), 'listVideos', icon, "category", id.replace("popular",""), "0")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(type, value, offset):
    xbmcplugin.setContent(pluginhandle, "episodes")
    content = getUrl(urlMain+"/videos/loadmore?type="+type+"&value="+value+"&offset="+offset)
    content = json.loads(content)
    for item in content:
        video = content[item]
        url = urlMain+"/videos/"+video["slug"]+"/"
        #GetImageHash - unable to stat url (randomly)
        #thumb = video["image"]["full"]
        thumb = video["image"]["path"]
        if "?" in thumb:
            thumb = thumb[:thumb.find("?")]
        addLink(video["title"], url, 'playVideo', thumb, video["dek"], video["date"].split(" ")[0], video["duration"], video["season"], video["episode"])
    addDir2(translation(30001), 'listVideos', "", type, value, str(int(offset)+30))
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewID+')')


def listEpisodes(url):
    xbmcplugin.setContent(pluginhandle, "episodes")
    content = getUrl(url)
    content = content[content.find('<div class="media-list'):]
    content = content[:content.find('</ul>')]
    spl=content.split('<li')
    for i in range(1,len(spl),1):
        entry=spl[i]
        match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        urlEpisode=urlMain+match[0]
        match=re.compile('<h3 class="title".+?>(.+?)</h3>', re.DOTALL).findall(entry)
        title=cleanTitle(match[0])
        match=re.compile('<p class="dek">(.+?)</p>', re.DOTALL).findall(entry)
        desc=cleanTitle(match[0])
        match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb=match[0]
        #GetImageHash - unable to stat url (randomly)
        #thumb=match[0].replace("/140x90/","/640x360/")
        if "?" in thumb:
            thumb = thumb[:thumb.find("?")]
        match=re.compile('<span class="date">(.+?)</span>', re.DOTALL).findall(entry)
        date=match[0]
        addLink(title, urlEpisode, 'playVideo', thumb, date+"\n"+desc)
    currentPage = url.split("/")[-1]
    nextPage = str(int(currentPage)+1)
    addDir(translation(30001), url.replace("/full-episodes/"+currentPage, "/full-episodes/"+nextPage), 'listEpisodes', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewID+')')


def list60MinutesMain(id):
    addDir(translation(30003), urlMain+"/latest/"+id+"/full-episodes/1", 'listEpisodes', "")
    addDir2(translation(30004), 'listVideos', "", "category", id, "0")
    xbmcplugin.endOfDirectory(pluginhandle)


def listEveningNewsMain(id):
    addLink(translation(30005),"",'playEveningNewsLatest',"")
    addDir(translation(30003), urlMain+"/latest/"+id+"/full-episodes/1", 'listEpisodes', "")
    addDir2(translation(30004), 'listVideos', "", "category", id, "0")
    xbmcplugin.endOfDirectory(pluginhandle)


def playEveningNewsLatest():
    content = getUrl(urlMain+"/latest/evening-news/full-episodes/1")
    content = content[content.find('<div class="media-list'):]
    content = content[:content.find('<ul>')]
    spl=content.split('<li')
    entry=spl[1]
    match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
    url=urlMain+match[0]
    match=re.compile('<h3 class="title".+?>(.+?)</h3>', re.DOTALL).findall(entry)
    title=cleanTitle(match[0])
    match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
    thumb=match[0]
    thumb = thumb[:thumb.find("?")]
    playVideo(url, title, thumb)


def playVideo(url, title="", thumb="DefaultVideo.png"):
    content = getUrl(url)
    match=re.compile('"mediaHlsURI":"(.+?)"', re.DOTALL).findall(content)
    streamUrl = match[0].replace("\\","")
    if thumb!="DefaultVideo.png":
        listitem = xbmcgui.ListItem(path=streamUrl, thumbnailImage=thumb)
    else:
        listitem = xbmcgui.ListItem(path=streamUrl)
    if title:
        listitem.setInfo( type="Video", infoLabels={ "Title": title } )
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def search():
    keyboard = xbmc.Keyboard('', translation(30002))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        listVideos("search", search_string, "0")


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def translation(id):
    return addon.getLocalizedString(id).encode('utf-8')


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, desc="", date="", duration="", season="", episode=""):
    u = sys.argv[0]+"?mode="+urllib.quote_plus(mode)+"&url="+urllib.quote_plus(url)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"title": name, "plot": desc, "aired": date, "season": season, "episode": episode})
    liz.setProperty('IsPlayable', 'true')
    if duration:
        liz.addStreamInfo('video', {'duration': int(duration)})
    if useThumbAsFanart:
        liz.setProperty("fanart_image", iconimage)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name,url,mode,iconimage):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name } )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok


def addDir2(name, mode, iconimage, type="", value="", offset=""):
    u = sys.argv[0]+"?mode="+urllib.quote_plus(mode)+"&type="+urllib.quote_plus(type)+"&value="+urllib.quote_plus(value)+"&offset="+urllib.quote_plus(offset)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
type = urllib.unquote_plus(params.get('type', ''))
value = urllib.unquote_plus(params.get('value', ''))
offset = urllib.unquote_plus(params.get('offset', ''))

if mode == 'listVideos':
    listVideos(type, value, offset)
elif mode == 'listEpisodes':
    listEpisodes(url)
elif mode == 'list60MinutesMain':
    list60MinutesMain(url)
elif mode == 'listEveningNewsMain':
    listEveningNewsMain(url)
elif mode == 'playEveningNewsLatest':
    playEveningNewsLatest()
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
else:
    index()
