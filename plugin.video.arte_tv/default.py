#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import os
import json
import xbmcplugin
import xbmcaddon
import xbmcgui
import time

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = "plugin.video.arte_tv"
addon = xbmcaddon.Addon(id=addonID)
forceViewMode = addon.getSetting("forceView") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
viewMode = str(addon.getSetting("viewID"))
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
baseUrl = "http://www.arte.tv"

while (not os.path.exists(xbmc.translatePath("special://profile/addon_data/"+addonID+"/settings.xml"))):
    addon.openSettings()

language = addon.getSetting("language")
language = ["de", "fr"][int(language)]
maxVideoQuality = addon.getSetting("maxVideoQuality")
maxVideoQuality = ["480p", "720p"][int(maxVideoQuality)]


def index():
    addDir(translation(30001), baseUrl+"/guide/"+language+"/plus7/plus_recentes.json", "listVideosNew", "")
    addDir(translation(30002), baseUrl+"/guide/"+language+"/plus7/selection.json", "listVideosNew", "")
    addDir(translation(30003), baseUrl+"/guide/"+language+"/plus7/plus_vues.json", "listVideosNew", "")
    addDir(translation(30004), baseUrl+"/guide/"+language+"/plus7/derniere_chance.json", "listVideosNew", "")
    addDir(translation(30005), "by_channel", "listCats", "")
    addDir(translation(30006), "by_cluster", "listCats", "")
    addDir(translation(30007), "by_date", "listCats", "")
    addDir(translation(30008), "", "search", "")
    addDir(translation(30012), "", "listWebLiveMain", "")
    addLink(translation(30009), "", "playLiveStream", icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideosNew(url):
    xbmcplugin.setContent(pluginhandle, "episodes")
    content = getUrl(url)
    content = json.loads(content)
    for item in content["videos"]:
        title = item["title"].encode('utf-8')
        try:
            desc = item["desc"].encode('utf-8')
        except:
            desc = ""
        try:
            duration = str(item["duration"])
        except:
            duration = ""
        try:
            date = item["airdate_long"].encode('utf-8')
        except:
            date = ""
        try:
            url = item["url"]
        except:
            url = ""
        try:
            thumb = item["image_url"]
        except:
            thumb = ""
        try:
            channels = item["video_channels"].encode('utf-8')
        except:
            channels = ""
        try:
            views = str(item["video_views"])
        except:
            views = ""
        try:
            until = item["video_rights_until"].encode('utf-8')
        except:
            until = ""
        try:
            rank = str(item["video_rank"])
        except:
            rank = ""
        desc = views+"   |   "+date+"\n"+channels+"\n"+desc
        addLink(cleanTitle(title), baseUrl+url, 'playVideoNew', thumb, desc, duration)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listSearchVideos(urlMain):
    xbmcplugin.setContent(pluginhandle, "episodes")
    try:
        content = getUrl(urlMain)
        spl = content.split('<div class="video-block has-play"')
        for i in range(1, len(spl), 1):
            entry = spl[i]
            match = re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
            title = cleanTitle(match[0])
            match = re.compile('data-description="(.+?)"', re.DOTALL).findall(entry)
            desc = ""
            if match:
                desc = cleanTitle(match[0])
            match = re.compile('<p class="time-row">.+?<span class=".+?">.+?</span>(.+?)</p>.+?<p class=".+?">.+?<span class=".+?">.+?</span>(.+?)</p>', re.DOTALL).findall(entry)
            if match:
                date = match[0][0].strip()
                desc = date+"\n"+desc
                duration = match[0][1].strip()
                duration = duration.split(" ")[0]
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url = match[0]
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0]
            addLink(title, url, 'playVideoNew', thumb, desc, duration)
        currentPage = urlMain[urlMain.find("page=")+5:]
        nextPage = str(int(currentPage)+1)
        addDir(translation(30010), urlMain.replace("page="+currentPage,"page="+nextPage), "listSearchVideos", "")
    except:
        pass
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listCats(type):
    content = getUrl(baseUrl+"/guide/"+language+"/plus7")
    content = content[content.find('<ul class="span12" data-filter="'+type+'">'):]
    content = content[:content.find('</ul>')]
    match = re.compile('<a href="(.+?)" data-controller="catchup" data-action="refresh" >(.+?)</a>', re.DOTALL).findall(content)
    for url, title in match:
        title = cleanTitle(title)
        url = baseUrl+url.replace("?", ".json?").replace("&amp;", "&")
        addDir(title, url, 'listVideosNew', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def search():
    keyboard = xbmc.Keyboard('', translation(30008))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        if language == "de":
            url = "http://www.arte.tv/guide/de/suchergebnisse?keyword="+search_string+"&page=1"
        elif language == "fr":
            url = "http://www.arte.tv/guide/fr/resultats-de-recherche?keyword="+search_string+"&page=1"
        listSearchVideos(url)


def searchWebLive():
    keyboard = xbmc.Keyboard('', translation(30008))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        url = "http://liveweb.arte.tv/searchEvent.do?method=displayElements&globalNames="+search_string+"&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=norah%20jones&classification=0&categoryId=&displayMode=0&eventTagName="
        listWebLive(url)


def listWebLiveMain():
    addDir(translation(30011), "http://liveweb.arte.tv/searchEvent.do?method=displayElements&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&categoryId=&displayMode=0&eventTagName=", "listWebLive", "")
    addDir(translation(30013), "http://liveweb.arte.tv/searchEvent.do?method=displayElements&categoryId=8&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&displayMode=0&eventTagName=", "listWebLive", "")
    addDir(translation(30014), "http://liveweb.arte.tv/searchEvent.do?method=displayElements&categoryId=1&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&displayMode=0&eventTagName=", "listWebLive", "")
    addDir(translation(30015), "http://liveweb.arte.tv/searchEvent.do?method=displayElements&categoryId=11&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&displayMode=0&eventTagName=", "listWebLive", "")
    addDir(translation(30016), "http://liveweb.arte.tv/searchEvent.do?method=displayElements&categoryId=7&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&displayMode=0&eventTagName=", "listWebLive", "")
    addDir(translation(30017), "http://liveweb.arte.tv/searchEvent.do?method=displayElements&categoryId=3&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&displayMode=0&eventTagName=", "listWebLive", "")
    addDir(translation(30008), "", "searchWebLive", "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listWebLive(url):
    urlMain = url
    hasNextPage = False
    content = getUrl(url, cookie="liveweb-language="+language.upper())
    if 'class="next off"' not in content:
        hasNextPage = True
    content = content[content.find('<div id="wall-mosaique"'):]
    content = content[:content.find('<div class="pagination-new">')]
    spl = content.split('<div class="block')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        if entry.find("/video/") > 0 or entry.find("/festival/") > 0:
            match = re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(entry)
            if match:
                title = cleanTitle(match[0])
            else:
                match1 = re.compile('/video/(.+?)/', re.DOTALL).findall(entry)
                match2 = re.compile('/festival/(.+?)/', re.DOTALL).findall(entry)
                if match1:
                    title = cleanTitle(match1[0]).replace("_", " ")
                elif match2:
                    title = cleanTitle(match2[0]).replace("_", " ")
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url = match[0]
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0]
            addLink(title, url, 'playLiveEvent', thumb, "")
    match = re.compile('moveValue=(.+?)&', re.DOTALL).findall(urlMain)
    page = int(match[0])
    if hasNextPage:
        nextPage = str(page+1)
        addDir(translation(30010)+" ("+nextPage+")", urlMain.replace("moveValue="+str(page)+"&", "moveValue="+nextPage+"&"), "listWebLive", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideoNew(url):
    listitem = xbmcgui.ListItem(path=getStreamUrlNew(url))
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def getStreamUrlNew(url):
    content = getUrl(url)
    match = re.compile('arte_vp_url="(.+?)">', re.DOTALL).findall(content)
    url = match[0].replace("/player/","/")
    content = getUrl(url)
    match1 = re.compile('"HBBTV","VQU":"SQ","VMT":"mp4","VUR":"(.+?)"', re.DOTALL).findall(content)
    match2 = re.compile('"HBBTV","VQU":"EQ","VMT":"mp4","VUR":"(.+?)"', re.DOTALL).findall(content)
    if match1 and maxVideoQuality == "720p":
        return match1[0]
    elif match2:
        return match2[0]


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def playLiveEvent(url):
    content = getUrl(url)
    match = re.compile("eventId=(.+?)&", re.DOTALL).findall(content)
    id = match[0]
    content = getUrl("http://download.liveweb.arte.tv/o21/liveweb/events/event-"+id+".xml")
    match1 = re.compile('<urlHd>(.+?)</urlHd>', re.DOTALL).findall(content)
    match2 = re.compile('<urlSd>(.+?)</urlHd>', re.DOTALL).findall(content)
    urlNew = ""
    if match1:
        urlNew = match1[0]
    elif match2:
        urlNew = match2[0]
    if urlNew == "":
        xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30018)+'!,5000)')
    else:
        match = re.compile('e=(.+?)&', re.DOTALL).findall(urlNew)
        expire = int(match[0])
        if expire < time.time():
            xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30019)+'!,5000)')
        else:
            urlNew = urlNew[:urlNew.find("?")].replace("/MP4:", "/mp4:")
            base = urlNew[:urlNew.find("mp4:")]
            playpath = urlNew[urlNew.find("mp4:"):]
            listitem = xbmcgui.ListItem(path=base+" playpath="+playpath)
            xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def playLiveStream():
    if language == "de":
        url = "http://org-www.arte.tv/papi/tvguide/videos/livestream/player/D/"
    elif language == "fr":
        url = "http://org-www.arte.tv/papi/tvguide/videos/livestream/player/F/"
    content = getUrl(url)
    match = re.compile('"RMTP_HQ":\\{"quality":"SD - 400p","width":.+?,"height":.+?,"mediaType":"rtmp","mimeType":"application/x-fcs","bitrate":.+?,"streamer":"(.+?)","url":"(.+?)"', re.DOTALL).findall(content)
    listitem = xbmcgui.ListItem(path=match[0][0] + match[0][1] + " swfUrl=http://www.arte.tv/flash/mediaplayer/mediaplayer.swf live=1 swfVfy=1")
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#39;", "'").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.replace('\\"', '"').strip()
    return title


def getUrl(url, cookie=None):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
    if cookie != None:
        req.add_header('Cookie', cookie)
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


def addLink(name, url, mode, iconimage, desc="", duration=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart and iconimage!=icon:
        liz.setProperty("fanart_image", iconimage)
    liz.addContextMenuItems([(translation(30020), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
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
name = urllib.unquote_plus(params.get('name', ''))

if mode == 'listVideosNew':
    listVideosNew(url)
elif mode == 'listSearchVideos':
    listSearchVideos(url)
elif mode == 'listCats':
    listCats(url)
elif mode == 'queueVideo':
    queueVideo(url, name)
elif mode == 'playVideoNew':
    playVideoNew(url)
elif mode == 'playLiveEvent':
    playLiveEvent(url)
elif mode == 'playLiveStream':
    playLiveStream()
elif mode == 'listWebLive':
    listWebLive(url)
elif mode == 'listWebLiveMain':
    listWebLiveMain()
elif mode == 'search':
    search()
elif mode == 'searchWebLive':
    searchWebLive()
else:
    index()
