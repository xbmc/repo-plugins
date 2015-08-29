#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import httplib
import socket
import sys
import re
import os
import random
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmc
import subprocess

#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
addonID = 'plugin.video.servustv_com'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
forceViewMode = addon.getSetting("forceView") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
addonDir = xbmc.translatePath(addon.getAddonInfo('path'))
defaultFanart = os.path.join(addonDir ,'fanart.png')
siteVersion = addon.getSetting("siteVersion")
siteVersion = ["de", "at"][int(siteVersion)]
quality = addon.getSetting("quality")
quality = [240, 480, 720][int(quality)]
qualityLive = addon.getSetting("qualityLive")
viewMode = str(addon.getSetting("viewID"))
translation = addon.getLocalizedString
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:30.0) Gecko/20100101 Firefox/30.0')]
urlMain = "http://www.servustv.com"


def index():
    content = opener.open(urlMain+"/"+siteVersion+"/Videos").read()
    match = re.compile('<section id="block-.+?<a href="(.+?)".*?>(.+?)<', re.DOTALL).findall(content)
    for url, title in match:
        title = cleanTitle(title)
        if title:
            addDir(cleanTitle(title), urlMain+url, 'listVideos', defaultFanart)
    addDir(translation(30001), "", 'listGenres', defaultFanart)
    addDir(translation(30002), "", 'search', defaultFanart)
    addLink(translation(30004), "", 'playLiveStream', defaultFanart)
    xbmcplugin.endOfDirectory(pluginhandle)


def listGenres():
    genres = []
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    content = opener.open(urlMain+"/"+siteVersion+"/Videos/Themen").read()
    content = content[content.find('class="slider-videorubiken-head-container"'):]
    match = re.compile('class="inner-teaser teaser-videorubriken">.+?href="(.+?)".*?>.*?src="(.+?)".*?class="ato text.*?">(.+?)<', re.DOTALL).findall(content)
    for url, thumb, title in match:
        title = cleanTitle(title)
        thumb = urlMain+thumb.replace("_stvd_teaser_small.jpg",".jpg").replace("_stvd_teaser_large.jpg",".jpg")
        if "/img/fallback_" in thumb:
            thumb = defaultFanart
        if title and not url in genres:
            addDir(cleanTitle(title), urlMain+url, 'listVideos', thumb)
            genres.append(url)
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    xbmc.log("XXX listVideos url :"+ url)
    content = opener.open(url).read()
    if 'class="white-background video-liste"' in content:
        content = content[content.find('class="white-background video-liste"'):]
    elif 'result-container' in content:
        content = content[content.find('result-container'):]
    spl = content.split('class="mol teaser large-')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        if 'class="ato btn playbutton"' in entry:
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url = urlMain+match[0]
            match = re.compile('class="ato headline.*?">(.+?)<', re.DOTALL).findall(entry)
            if match:
                title = match[0].strip()
                match = re.compile('class="ato text  teaser-sendungsdetail-subtitel">(.+?)<', re.DOTALL).findall(entry)
                if match:
                    title = title+" - "+match[0].strip()
                title = cleanTitle(title)
                match = re.compile('class="ato videoleange">(.+?)<', re.DOTALL).findall(entry)
                duration = ""
                if match:
                    duration = match[0]
                match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
                thumb = urlMain+match[0].replace("_stvd_teaser_small.jpg",".jpg").replace("_stvd_teaser_large.jpg",".jpg")
                addLink(title, url, 'playVideo', thumb, "", duration)
    match = re.compile('class="next-site">.+?href="(.+?)"', re.DOTALL).findall(content)
    if match:        
        addDir(translation(30003), urlMain+cleanTitle(match[0]), 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url,name):
    content = opener.open(url).read()
    match = re.compile('data-videoid="(.+?)"', re.DOTALL).findall(content)
    content = opener.open("http://c.brightcove.com/services/mobile/streaming/index/master.m3u8?videoId="+match[0]).read()
    match = re.compile('RESOLUTION=(.+?)x(.+?)\n(.+?)\n', re.DOTALL).findall(content)
    for resX, resY, url in match:
        if int(resY)<=quality:
            finalURL=url
    
    listitem = xbmcgui.ListItem(path=finalURL)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def download (url,name):    
    xbmc.log("star download url"+ url)
    probe_args = [ffmpg, "-i", url, folder+name+".mp4" ]
    proc = runCommand(probe_args)
    temp_output = proc.communicate()[0]

def runCommand(args):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            proc = subprocess.Popen(args,startupinfo=startupinfo)
        except:
            xbmc.log("Couldn't run command")
            return False
        else:
            xbmc.log("Returning process", 5)
            return proc
    
def playLiveStream():
    #streamUrl=" http://hdiosstv-f.akamaihd.net/i/servustvhdde_1@75540/master.m3u8?b=0-1500"    
    #http://hdiosstv-f.akamaihd.net/i/servustvhdde_1@75540/index_912_av-b.m3u8?sd=10&b=0-1500&rebase=on
    xbmc.log("XXX uRL: " + qualityLive)
    if qualityLive=="1": 
      streamUrl="http://hdiosstv-f.akamaihd.net/i/servustvhdde_1@75540/index_1112_av-b.m3u8?sd=10&b=0-1500&rebase=on"
    else :
       streamUrl="http://hdiosstv-f.akamaihd.net/i/servustvhdde_1@75540/index_912_av-b.m3u8?sd=10&b=0-1500&rebase=on"
    xbmc.log("XXX uRLx: " + streamUrl)
    listitem = xbmcgui.ListItem(path=streamUrl)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name, thumb):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name, thumbnailImage=thumb)
    playlist.add(url, listitem)


def search():
    keyboard = xbmc.Keyboard('', translation(30002))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        listVideos(urlMain+"/"+siteVersion+"/search?stvd_form_search[name]="+search_string)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


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
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+str(name)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart and iconimage!=icon:
        liz.setProperty("fanart_image", iconimage)
    liz.addContextMenuItems([(translation(30007), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+str(name)+'&thumb='+urllib.quote_plus(iconimage)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if useThumbAsFanart and iconimage!=icon:
        liz.setProperty("fanart_image", defaultFanart)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
thumb = urllib.unquote_plus(params.get('thumb', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listGenres':
    listGenres()
elif mode == 'playVideo':
    playVideo(url,name)
elif mode == 'playLiveStream':
    playLiveStream()
elif mode == 'queueVideo':    
    queueVideo(url, name, thumb)
elif mode == 'search':
    search()
else:
    index()
