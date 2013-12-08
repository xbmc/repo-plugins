#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import os
import json
import time
import random
import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
xbox = xbmc.getCondVisibility("System.Platform.xbox")
forceViewMode = addon.getSetting("forceViewMode") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
viewModeVideos = str(addon.getSetting("viewModeVideos"))
viewModeChannels = str(addon.getSetting("viewModeChannels"))
translation = addon.getLocalizedString
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
versionFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/version")
cacheFolder = xbmc.translatePath("special://profile/addon_data/"+addonID+"/cache")
urlMain = "http://spiegeltv-ivms2-restapi.s3.amazonaws.com"
opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')]

if not os.path.isdir(addonUserDataFolder):
    os.mkdir(addonUserDataFolder)
if not os.path.isdir(cacheFolder):
    os.mkdir(cacheFolder)

def index():
    content = getUrl(urlMain+"/version.json")
    content = json.loads(content)
    fh = open(versionFile, 'w')
    fh.write(content["version_name"])
    fh.close()
    addDir(translation(30003), "", 'listChannels', icon)
    addDir(translation(30004), "", 'listTopics', icon)
    addDir(translation(30002), "0", 'listVideos', icon)
    addDir(translation(30007), "0", 'listVideos', icon, "", "", "true")
    addDir(translation(30005), "", 'playRandom', icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def listChannels(url):
    xbmcplugin.setContent(pluginhandle, "episodes")
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    content = getUrl(urlMain+"/"+getVersion()+"/restapi/channels.json")
    content = json.loads(content)
    for item in content:
        channel = getUrl(urlMain+"/"+getVersion()+"/restapi/channels/"+str(item)+".json")
        channel = json.loads(channel)
        ids = ""
        for id in channel["media"]:
            ids += str(id)+","
        if ids:
            ids = ids[:-1]
        date = ""
        if channel["updated"]:
            date = channel["updated"]
            date = date[:date.find("T")]
        thumbUrl = ""
        for thumb in channel["images"]:
            if thumb["spec_slug"]=="k2-kanal-moodbox":
                thumbUrl = thumb["url"]
        addDir(channel["title"].replace("ANZEIGE ",""), "0", 'listVideos', thumbUrl, ids, date)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeChannels+')')


def listTopics(url):
    xbmcplugin.setContent(pluginhandle, "episodes")
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    content = getUrl(urlMain+"/"+getVersion()+"/restapi/playlists.json")
    content = json.loads(content)
    for item in content:
        channel = getUrl(urlMain+"/"+getVersion()+"/restapi/playlists/"+str(item)+".json")
        channel = json.loads(channel)
        ids = ""
        for id in channel["media"]:
            ids += str(id)+","
        if ids:
            ids = ids[:-1]
        date = ""
        if channel["updated"]:
            date = channel["updated"]
            date = date[:date.find("T")]
        thumbUrl = ""
        for thumb in channel["images"]:
            if thumb["spec_slug"]=="t2-thema-moodbox":
                thumbUrl = thumb["url"]
        addDir(channel["title"], "0", 'listVideos', thumbUrl, ids, date)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeChannels+')')


def listVideos(ids, index, rnd):
    xbmcplugin.setContent(pluginhandle, "episodes")
    if not ids:
        content = getUrl(urlMain+"/"+getVersion()+"/restapi/media.json")
        content = json.loads(content)
    else:
        content = ids.split(",")
    if rnd=="true":
        random.shuffle(content)
    for i in range(index, index+12, 1):
        video = getUrl(urlMain+"/"+getVersion()+"/restapi/media/"+str(content[i])+".json")
        video = json.loads(video)
        try:
            date = video["web_airdate"]
        except:
            date = ""
        try:
            subtitle = video["subtitle"].encode('utf-8')
        except:
            subtitle = ""
        try:
            duration = str(int(video["duration_in_ms"]/60000))
        except:
            duration = "1"
        if duration=="0":
            duration="1"
        try:
            description = video["description"].encode('utf-8')
        except:
            description = ""
        try:
            uuid = video["uuid"]
        except:
            uuid = ""
        try:
            isWide = video["is_wide"]
        except:
            isWide = True
        if isWide:
            aspect = "16x9"
        else:
            aspect = "4x3"
        playpath = "mp4:"+uuid+"_spiegeltv_0500_"+aspect+".m4v"
        desc = video["title"].encode('utf-8')+" - "+subtitle+"\n\n"+description
        thumbUrl = ""
        for thumb in video["images"]:
            if thumb["spec_slug"]=="f3-film-embed":
                thumbUrl = thumb["url"]
        if uuid:
            addLink(video["title"].encode('utf-8'), playpath, 'playVideo', thumbUrl, desc, duration, date)
        if i==len(content)-1:
            break
    if rnd=="true":
        addDir(translation(30001), "0", 'listVideos', "", "", "", "true")
    elif (int(index)+12)<len(content):
        addDir(translation(30001), str(int(index)+12), 'listVideos', "", ids)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeVideos+')')


def playRandom():
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    content = getUrl(urlMain+"/"+getVersion()+"/restapi/media.json")
    content = json.loads(content)
    random.shuffle(content)
    count = 1
    for id in content:
        if xbox==True:
            url="plugin://video/Spiegel.tv/?url="+str(id)+"&mode=playVideoRandom"
        else:
            url="plugin://plugin.video.spiegel_tv/?url="+str(id)+"&mode=playVideoRandom"
        listitem = xbmcgui.ListItem("Video: "+str(count))
        playlist.add(url, listitem)
        count += 1
    xbmc.Player().play(playlist)


def playVideo(playpath):
    listitem = xbmcgui.ListItem(path="rtmpe://fms.edge.newmedia.nacamar.net/schnee_vod/flashmedia/ playpath="+playpath)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name, thumb):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
    playlist.add(url, listitem)


def playVideoRandom(id):
    video = getUrl(urlMain+"/"+getVersion()+"/restapi/media/"+id+".json")
    video = json.loads(video)
    thumbUrl = ""
    for thumb in video["images"]:
        if thumb["spec_slug"]=="f3-film-embed":
            thumbUrl = thumb["url"]
    try:
        isWide = video["is_wide"]
    except:
        isWide = True
    if isWide:
        aspect = "16x9"
    else:
        aspect = "4x3"
    playpath = "mp4:"+video["uuid"]+"_spiegeltv_0500_"+aspect+".m4v"
    title = video["title"].encode('utf-8')
    try:
        subtitle = video["subtitle"].encode('utf-8')
    except:
        subtitle = ""
    if subtitle:
        title += ": "+subtitle
    listitem = xbmcgui.ListItem(title, path="rtmpe://fms.edge.newmedia.nacamar.net/schnee_vod/flashmedia/ playpath="+playpath, thumbnailImage=thumbUrl)
    listitem.setInfo(type="Video", infoLabels={"Title": title})
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


def getVersion():
    fh = open(versionFile, 'r')
    content = fh.read()
    fh.close()
    return content


def getUrl(url):
    cacheFile = os.path.join(cacheFolder, url.split("/")[-1])
    if os.path.exists(cacheFile) and ("/media.json" in url or "/channels/" in url) and (time.time()-os.path.getmtime(cacheFile) < 60*60*6):
        fh = open(cacheFile, 'r')
        content = fh.read()
        fh.close()
    elif os.path.exists(cacheFile) and ("/media.json" not in url and "/channels/" not in url and "/version.json" not in url):
        fh = open(cacheFile, 'r')
        content = fh.read()
        fh.close()
    else:
        content = opener.open(url).read()
        fh = open(cacheFile, 'w')
        fh.write(content)
        fh.close()
    return content


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, desc, duration, date):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration, "Aired": date, "Episode": 1})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart:
        liz.setProperty("fanart_image", iconimage)
    liz.addContextMenuItems([(translation(30006), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+str(name)+'&thumb='+urllib.quote_plus(iconimage)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, ids="", date="", rnd="false"):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&ids="+str(ids)+"&rnd="+str(rnd)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Aired": date, "Episode": len(ids.split(","))})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
ids = urllib.unquote_plus(params.get('ids', ''))
name = urllib.unquote_plus(params.get('name', ''))
thumb = urllib.unquote_plus(params.get('thumb', ''))
rnd = urllib.unquote_plus(params.get('rnd', ''))

if mode == 'listChannels':
    listChannels(url)
elif mode == 'listTopics':
    listTopics(url)
elif mode == 'listVideos':
    listVideos(ids, int(url), rnd)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'queueVideo':
    queueVideo(url, name, thumb)
elif mode == 'playVideoRandom':
    playVideoRandom(url)
elif mode == 'playRandom':
    playRandom()
else:
    index()
