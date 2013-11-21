#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
xbox = xbmc.getCondVisibility("System.Platform.xbox")
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
forceViewMode = addon.getSetting("forceView") == "true"
viewMode = str(addon.getSetting("viewID"))
translation = addon.getLocalizedString
urlMain = "http://www.vice.com"
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
addonUserdataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
subFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/sub.srt")
favsFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/favourites")
subtitleLanguage = addon.getSetting("subtitleLanguage")
subtitleLanguage = ["-", "ro", "pt", "pl", "nl", "it", "es", "ru", "fr", "de", "en"][int(subtitleLanguage)]

if not os.path.isdir(addonUserdataFolder):
    os.mkdir(addonUserdataFolder)

while (not os.path.exists(xbmc.translatePath("special://profile/addon_data/"+addonID+"/settings.xml"))):
    addon.openSettings()

def index():
    addDir(translation(30002), "", 'listLatest', icon)
    addDir(translation(30003), "", 'listShows', icon)
    addDir(translation(30004), "", 'listShowsFavs', icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def listLatest():
    content = getUrl(urlMain+"/video")
    spl = content.split('<li class="story" data-vr-contentbox="vice-vbs-index-video')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
        desc = match[0]
        match = re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry)
        date = match[0]
        match = re.compile('<h2>.+?>(.+?)<', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = urlMain+match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace("_190x165.jpg","_669x375.jpg").replace(" ","%20")
        addLink(title, url, 'playVideo', thumb, date+"\n"+desc)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listShows():
    content = getUrl(urlMain+"/shows")
    spl = content.split('<li class="story story-square">')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
        url = urlMain+match[0][0]
        title = cleanTitle(match[0][1])
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]
        match = re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
        desc = match[0]
        addShowDir(title, url, 'listVideos', thumb, desc)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listShowsFavs():
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    if os.path.exists(favsFile):
        fh = open(favsFile, 'r')
        all_lines = fh.readlines()
        for line in all_lines:
            title = line[line.find("###TITLE###=")+12:]
            title = title[:title.find("#")]
            url = line[line.find("###URL###=")+10:]
            url = url[:url.find("#")]
            thumb = line[line.find("###THUMB###=")+12:]
            thumb = thumb[:thumb.find("#")]
            addShowFavDir(title, urllib.unquote_plus(url), "listVideos", thumb)
        fh.close()
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listVideos(url):
    content = getUrl(url)
    spl = content.split('<li class="story" data-vr-contentbox="vice-vbs-episode')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
        desc = ""
        if match:
            desc = match[0]
        match = re.compile('<span>(.+?)</span>', re.DOTALL).findall(entry)
        date = match[0]
        match = re.compile('<h2>.+?>(.+?)<', re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = urlMain+match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace("_220x124.jpg","_669x375.jpg").replace(" ","%20")
        addLink(title, url, 'playVideo', thumb, date+"\n"+desc)
    match = re.compile('<li class="next"><a href="(.+?)"', re.DOTALL).findall(content)
    if match:
        addDir(translation(30001), urlMain+match[0], 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    content = getUrl(url)
    matchOO = re.compile('embedCode=(.+?)&', re.DOTALL).findall(content)
    matchYT = re.compile('youtube.com/v/(.+?)"', re.DOTALL).findall(content)
    streamUrl = ""
    if matchOO:
        content = getUrl("http://player.ooyala.com/player.js?embedCode="+matchOO[0])
        match = re.compile('mobile_player_url="(.+?)"', re.DOTALL).findall(content)
        content = getUrl(match[0]+"ipad").replace("\\","")
        matchStream = re.compile('"ipad_url":"(.+?)"', re.DOTALL).findall(content)
        streamUrl = matchStream[0].replace("u0026","&")
        matchSubtitle = re.compile('"closed_caption_url":"(.+?)"', re.DOTALL).findall(content)
        subtitleUrl = matchSubtitle[0].replace("\\","")
        listitem = xbmcgui.ListItem(path=streamUrl)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        if subtitleLanguage!="-":
            setSubtitle(subtitleUrl)
    elif matchYT:
        if xbox:
            streamUrl = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + matchYT[0]
        else:
            streamUrl = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + matchYT[0]
        listitem = xbmcgui.ListItem(path=streamUrl)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    if url.endswith("part-1"):
        urlNext = url.replace("part-1","part-2")
        req = urllib2.Request(urlNext)
        try:
            urllib2.urlopen(req)
            xbmc.sleep(3000)
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            listitem = xbmcgui.ListItem(name+" - Part 2")
            playlist.add("plugin://plugin.video.vice_com/?url="+urllib.quote_plus(urlNext)+"&mode=playVideo", listitem)
        except:
            pass


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def favs(param):
    mode = param[param.find("###MODE###=")+11:]
    mode = mode[:mode.find("###")]
    channelEntry = param[param.find("###TITLE###="):]
    if mode == "ADD":
        if os.path.exists(favsFile):
            fh = open(favsFile, 'r')
            content = fh.read()
            fh.close()
            if content.find(channelEntry) == -1:
                fh = open(favsFile, 'a')
                fh.write(channelEntry+"\n")
                fh.close()
        else:
            fh = open(favsFile, 'a')
            fh.write(channelEntry+"\n")
            fh.close()
    elif mode == "REMOVE":
        refresh = param[param.find("###REFRESH###=")+14:]
        refresh = refresh[:refresh.find("#")]
        fh = open(favsFile, 'r')
        content = fh.read()
        fh.close()
        entry = content[content.find(channelEntry):]
        fh = open(favsFile, 'w')
        fh.write(content.replace(channelEntry+"\n", ""))
        fh.close()
        if refresh == "TRUE":
            xbmc.executebuiltin("Container.Refresh")


def setSubtitle(url):
    if os.path.exists(subFile):
        os.remove(subFile)
    try:
        content = getUrl(url)
    except:
        content = ""
    if content:
        try:
            if '<div xml:lang="'+subtitleLanguage+'"' in content:
                content = content[content.find('<div xml:lang="'+subtitleLanguage+'"'):]
                content = content[:content.find('</div>')]
                matchLine = re.compile('<p xml:id=".+?" begin="(.+?)" dur="(.+?)">(.+?)</p>', re.DOTALL).findall(content)
                fh = open(subFile, 'a')
                count = 1
                for begin, duration, line in matchLine:
                    beginFull = begin.replace(".",",")
                    begin = begin.split(":")
                    beginH = float(begin[0])
                    beginM = float(begin[1])
                    beginS = float(begin[2])
                    beginSTotal = beginS+60*beginM+3600*beginH
                    duration = duration.split(":")
                    durationH = float(duration[0])
                    durationM = float(duration[1])
                    durationS = float(duration[2])
                    durationSTotal = durationS+60*durationM+3600*durationH
                    endSTotal = beginSTotal+durationSTotal
                    endH = str(int(endSTotal/60/60))
                    if len(endH)==1:
                        endH = "0"+endH
                    endM = str(int(endSTotal/60))
                    if len(endM)==1:
                        endM = "0"+endM
                    endS = str(endSTotal%60)
                    endFull = endH+":"+endM+":"+endS.replace(".",",")
                    line = line.replace("<br/>","\n").strip()
                    fh.write(str(count)+"\n"+beginFull+" --> "+endFull+"\n"+cleanTitle(line)+"\n\n")
                    count+=1
                fh.close()
                xbmc.sleep(1000)
                xbmc.Player().setSubtitles(subFile)
        except:
            pass


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
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


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+str(name)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart:
        liz.setProperty("fanart_image", iconimage)
    liz.addContextMenuItems([(translation(30005), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addShowDir(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    playListInfos = "###MODE###=ADD###TITLE###="+name+"###URL###="+urllib.quote_plus(url)+"###THUMB###="+iconimage+"###END###"
    liz.addContextMenuItems([(translation(30006), 'RunPlugin(plugin://'+addonID+'/?mode=favs&url='+urllib.quote_plus(playListInfos)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addShowFavDir(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    playListInfos = "###MODE###=REMOVE###TITLE###="+name+"###URL###="+urllib.quote_plus(url)+"###THUMB###="+iconimage+"###END###"
    liz.addContextMenuItems([(translation(30007), 'RunPlugin(plugin://'+addonID+'/?mode=favs&url='+urllib.quote_plus(playListInfos)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listLatest':
    listLatest()
elif mode == 'listShows':
    listShows()
elif mode == 'listShowsFavs':
    listShowsFavs()
elif mode == 'playVideo':
    playVideo(url)
elif mode == "queueVideo":
    queueVideo(url, name)
elif mode == "favs":
    favs(url)
else:
    index()
