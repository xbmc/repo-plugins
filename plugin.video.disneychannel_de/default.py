#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import os
import json
import datetime
import xbmcplugin
import xbmcgui
import xbmcaddon

#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
addonID = 'plugin.video.disneychannel_de'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
forceViewMode = addon.getSetting("forceViewMode") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
viewMode = str(addon.getSetting("viewMode"))
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
urlMain = "http://disneychannel.de"
opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')]

def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    
def index():
    addDir(translation(30106), urlMain+"/_fta_stream/search.json?q=video&filter[type]=Video&filter[start_date_s]="+(datetime.date.today()-datetime.timedelta(days=0)).strftime("%Y-%m-%d")+"&limit=50&offset=0", 'listVideos', icon)
    addDir(translation(30001), urlMain+"/_fta_stream/search.json?q=video&filter[type]=Video&filter[start_date_s]="+(datetime.date.today()-datetime.timedelta(days=1)).strftime("%Y-%m-%d")+"&limit=50&offset=0", 'listVideos', icon)
    addDir(translation(30002), urlMain+"/_fta_stream/search.json?q=video&filter[type]=Video&filter[start_date_s]="+(datetime.date.today()-datetime.timedelta(days=2)).strftime("%Y-%m-%d")+"&limit=50&offset=0", 'listVideos', icon)
    addDir((datetime.date.today()-datetime.timedelta(days=3)).strftime("%b %d, %Y"), urlMain+"/_fta_stream/search.json?q=video&filter[type]=Video&filter[start_date_s]="+(datetime.date.today()-datetime.timedelta(days=3)).strftime("%Y-%m-%d")+"&limit=50&offset=0", 'listVideos', icon)
    addDir((datetime.date.today()-datetime.timedelta(days=4)).strftime("%b %d, %Y"), urlMain+"/_fta_stream/search.json?q=video&filter[type]=Video&filter[start_date_s]="+(datetime.date.today()-datetime.timedelta(days=4)).strftime("%Y-%m-%d")+"&limit=50&offset=0", 'listVideos', icon)
    addDir((datetime.date.today()-datetime.timedelta(days=5)).strftime("%b %d, %Y"), urlMain+"/_fta_stream/search.json?q=video&filter[type]=Video&filter[start_date_s]="+(datetime.date.today()-datetime.timedelta(days=5)).strftime("%Y-%m-%d")+"&limit=50&offset=0", 'listVideos', icon)
    addDir((datetime.date.today()-datetime.timedelta(days=6)).strftime("%b %d, %Y"), urlMain+"/_fta_stream/search.json?q=video&filter[type]=Video&filter[start_date_s]="+(datetime.date.today()-datetime.timedelta(days=6)).strftime("%Y-%m-%d")+"&limit=50&offset=0", 'listVideos', icon)
    addDir((datetime.date.today()-datetime.timedelta(days=7)).strftime("%b %d, %Y"), urlMain+"/_fta_stream/search.json?q=video&filter[type]=Video&filter[start_date_s]="+(datetime.date.today()-datetime.timedelta(days=7)).strftime("%Y-%m-%d")+"&limit=50&offset=0", 'listVideos', icon)
    addLink(translation(30003), "", 'playLive', icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    content = opener.open(url).read()
    content = json.loads(content)
    for item in content["data"]["results"]:
        title = item["title"].encode('utf-8')
        desc = item["ptitle"][0].encode('utf-8')
        url = item["href"]
        thumb = item["thumb"]
        duration = item["duration"]
        addLink(title, url, 'playVideo', thumb, desc, duration)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    debug("playVideo URL : "+url)
    content = opener.open(url).read()
    match = re.compile('embedURL":"(.+?)",', re.DOTALL).findall(content)
    debug("Playvideo URL2 : "+match[0])
    content = opener.open(match[0]).read()
    match2 = re.compile('"downloadUrl":"(.+?)"', re.DOTALL).findall(content)
    debug("Playvideo URL3 : "+match2[0])
    finalURL = match2[0]
    finalURL=finalURL.replace("https","http")
    listitem = xbmcgui.ListItem(path=finalURL)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def playLive():
    content = opener.open(urlMain+"/livestream").read()
    match = re.compile('"hlsStreamUrl":"(.+?)"', re.DOTALL).findall(content)
    listitem = xbmcgui.ListItem(path=match[0])
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name, thumb):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
    playlist.add(url, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


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
    liz.addContextMenuItems([(translation(30006), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+str(name)+'&thumb='+urllib.quote_plus(iconimage)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, desc="", audioUrl=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&audioUrl="+urllib.quote_plus(audioUrl)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    if useThumbAsFanart and iconimage!=icon:
        liz.setProperty("fanart_image", iconimage)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
thumb = urllib.unquote_plus(params.get('thumb', ''))
audioUrl = urllib.unquote_plus(params.get('audioUrl', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'queueVideo':
    queueVideo(url, name, thumb)
elif mode == 'playLive':
    playLive()
else:
    index()
