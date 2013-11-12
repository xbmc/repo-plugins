#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import os
import datetime
import xbmcplugin
import xbmcgui
import xbmcaddon

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon()
addonID = addon.getAddonInfo('id')
thumbsDir = xbmc.translatePath('special://home/addons/'+addonID+'/resources/thumbs')
forceViewMode = addon.getSetting("forceViewMode") == "true"
useThumbAsFanart = addon.getSetting("useThumbAsFanart") == "true"
autoPlay = int(addon.getSetting("autoPlay"))
viewModeNewsShows = str(addon.getSetting("viewModeNewsShows"))
viewModeVideos = str(addon.getSetting("viewModeVideos"))
bitrate = addon.getSetting("bitrate")
bitrate = [600, 800, 1500, 3500][int(bitrate)]
itemsPerPage = addon.getSetting("itemsPerPage")
itemsPerPage = ["25", "50", "75", "100"][int(itemsPerPage)]
urlMain = "http://dsc.discovery.com"
urlMainNews = "http://news.discovery.com"
iconPathNews = os.path.join(thumbsDir, "discovery_news.png")


def index():
    addDir("Discovery News", "", 'listNewsMain', iconPathNews)
    addDir("Discovery Channel", urlMain+"/videos", 'listShows', os.path.join(thumbsDir, "discovery_channel.png"), "", "", "Discovery")
    addDir("Animal Planet", "http://animal.discovery.com/videos", 'listShows', os.path.join(thumbsDir, "animal_planet.png"), "", "", "APL")
    addDir("Animal Planet Live", "", 'listAPL', os.path.join(thumbsDir, "animal_planet_live.png"))
    addDir("TLC", "http://www.tlc.com/videos", 'listShows', os.path.join(thumbsDir, "tlc.png"), "", "", "TLC")
    addDir("Science Channel", "http://science.discovery.com/videos", 'listShows', os.path.join(thumbsDir, "science_channel.png"), "", "", "Science%2520Channel")
    addDir("Destination America", "http://america.discovery.com/videos", 'listShows', os.path.join(thumbsDir, "destination_america.png"), "", "", "DAM")
    addDir("Investigation Discovery", "http://investigation.discovery.com/videos", 'listShows', os.path.join(thumbsDir, "investigation_discovery.png"), "", "", "Investigation%2520Discovery")
    addDir("Military Channel", "http://military.discovery.com/videos", 'listShows', os.path.join(thumbsDir, "military_channel.png"), "", "", "Military%2520Channel")
    addDir("Velocity", "http://velocity.discovery.com/videos", 'listShows', os.path.join(thumbsDir, "velocity.png"), "", "", "Velocity")
    addDir("Discovery fit&health", "http://health.discovery.com/tv-shows", 'listShows', os.path.join(thumbsDir, "discovery_fit_health.png"), "", "", "Health")
    addPluginDir("HowStuffWorks", "plugin://plugin.video.howstuffworks_com", os.path.join(thumbsDir, "how_stuff_works.png"))
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeNewsShows+')')
    xbmcplugin.endOfDirectory(pluginhandle)


def listNewsMain():
    addDir("Latest", "latest", 'listNews', iconPathNews)
    addDir("Most watched", "mostWatched", 'listNews', iconPathNews)
    addDir("Collections", "collectionsMain", 'listNews', iconPathNews)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeNewsShows+')')
    xbmcplugin.endOfDirectory(pluginhandle)


def listNews(type):
    content = getUrl(urlMainNews+"/videos")
    if type == "latest":
        splStr = '<div class="fragment-media  media-vertical grid-member'
    elif type == "mostWatched":
        content = content[content.find('<div class="module module-slider slider-paged pre " data-current="0" >'):]
        splStr = '<div class="fragment-media  media-vertical paged-member'
    elif type == "collectionsMain":
        content = content[:content.find('<div class="module module-slider slider-paged pre " data-current="0" >')]
        splStr = '<div class="fragment-media  media-vertical paged-member'
    spl = content.split(splStr)
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<div class="media-title">.+?>(.+?)<', re.DOTALL).findall(entry)
        title = cleanTitle(match[0]).title()
        match = re.compile('<span class="playlist-count">(.+?)</span>', re.DOTALL).findall(entry)
        desc = ""
        if match:
            desc = cleanTitle(match[0])
        match = re.compile('<div class="media-sub">(.+?)</div>', re.DOTALL).findall(entry)
        if match:
            desc += "   |   "+cleanTitle(match[0])
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0].replace(" ", "%20")
        if type == "collectionsMain":
            addDir(title, url, 'listNewsCollections', thumb, "", desc)
        else:
            addLink(title, url, 'playVideo', thumb, desc)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeNewsShows+')')
    xbmcplugin.endOfDirectory(pluginhandle)


def listNewsCollections(url):
    content = getUrl(url)
    content = content[content.find("var videoData = [];"):]
    content = content[:content.find("</script>")]
    spl = content.split("var clip = {")
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile("clip_title 		: '(.+?)'", re.DOTALL).findall(entry)
        title = cleanTitle(match[0])
        match = re.compile("thumbnail_url 	: '(.+?)'", re.DOTALL).findall(entry)
        thumb = match[0]
        match = re.compile("m3u8 			: '(.+?)'", re.DOTALL).findall(entry)
        url = match[0]
        addLink(title, url, 'playVideo', thumb, "")
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeNewsShows+')')
    xbmcplugin.endOfDirectory(pluginhandle)


def listShows(url, channelID, channelThumb):
    currentUrl = url
    content = getUrl(url)
    #addDir(translation(30003), urlMain+"/services/taxonomy/"+channelID+"/?num="+itemsPerPage+"&page=0&filter=fullepisode&tpl=dds%2Fmodules%2Fvideo%2Fall_assets_list.html&order=desc&feedGroup=video", 'listVideos', channelThumb, "fullepisode")
    content = content[content.find('<div class="module-all-shows-carousel shows-other">'):]
    content = content[:content.find('<div class="navigation')]
    spl = content.split('<a href="/tv-shows')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('/(.+?)"', re.DOTALL).findall(entry)
        id = match[0]
        if "/" in id:
            id = id[:id.find("/")]
        if currentUrl.endswith("/videos"):
            url = currentUrl[:currentUrl.find("/videos")]+"/tv-shows/"+id
        elif currentUrl.endswith("/tv-shows"):
            url = currentUrl[:currentUrl.find("/tv-shows")]+"/tv-shows/"+id
        match = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
        if match:
            title = cleanTitle(match[0]).replace(" Videos", "")
        else:
            title = id.replace("-", " ").title()
        match = re.compile('data-original="(.+?)"', re.DOTALL).findall(entry)
        thumb = ""
        if match:
            thumb = match[0].replace(" ", "%20")
        addDir(title, url, 'listVideos', thumb)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeNewsShows+')')
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideosMain(url, channelThumb):
    content = getUrl(url)
    if '<div class="module-videos-carousel full-episode-assets">' in content:
        addDir(translation(30003), url, 'listVideos', channelThumb, "fullepisode")
        addDir(translation(30004), url, 'listVideos', channelThumb, "clip")
        if forceViewMode:
            xbmc.executebuiltin('Container.SetViewMode('+viewModeNewsShows+')')
        xbmcplugin.endOfDirectory(pluginhandle)
    else:
        listVideos(url)


def listVideos(url, type="clip"):
    content = getUrl(url)
    xbmcplugin.setContent(pluginhandle, "episodes")
    if ("/services/taxonomy/" in url and '<div class="thumbnail still-small">' in content) or "data-service-uri=" in content:
        if "/services/taxonomy/" not in url:
            match = re.compile('data-service-uri="(.+?)"', re.DOTALL).findall(content)
            url = urlMain+match[0]+"?num="+itemsPerPage+"&page=0&filter="+type+"&tpl=dds%2Fmodules%2Fvideo%2Fall_assets_list.html&sort=date&order=desc&feedGroup=video"
            content = getUrl(url)
        currentUrl = url
        spl = content.split('<div class="thumbnail still-small">')
        for i in range(1, len(spl), 1):
            entry = spl[i]
            match = re.compile('<h4>.+?>(.+?)<', re.DOTALL).findall(entry)
            title = cleanTitle(match[0])
            match = re.compile('<h5>(.+?)</h5>', re.DOTALL).findall(entry)
            title2 = cleanTitle(match[0])
            if type=="fullepisode":
                title = title2 + ": " + title
            match = re.compile('<p class="description">(.+?)</p>', re.DOTALL).findall(entry)
            desc = ""
            if match:
                desc = cleanTitle(match[0])
            match = re.compile('<div class="length">(.+?)</div>', re.DOTALL).findall(entry)
            length = match[0]
            splLength = length.split(":")
            length = int(splLength[0])*60+int(splLength[1])
            match = re.compile('<div class="views">(.+?)</div>', re.DOTALL).findall(entry)
            views = match[0]+" Views"
            match = re.compile('<div class="date">(.+?)</div>', re.DOTALL).findall(entry)
            splDate = match[0].split("/")
            date = splDate[1]+"-"+splDate[0]+"-"+splDate[2]
            desc = views+"\n"+desc
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url = match[0]
            if not url.startswith("http://"):
                url = urlMain+url
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0].replace(" ", "%20")
            addLink(title, url, 'playVideo', thumb, desc, length, date, str(i))
        if ';">Next' in content:
            match = re.compile('page=(.+?)&', re.DOTALL).findall(currentUrl)
            currentPage = int(match[0])
            nextPage = currentPage+1
            addDir(translation(30001)+" ("+str(nextPage+1)+")", currentUrl.replace("page="+str(currentPage), "page="+str(nextPage)), 'listVideos', "")
        if forceViewMode:
            xbmc.executebuiltin('Container.SetViewMode('+viewModeVideos+')')
        xbmcplugin.endOfDirectory(pluginhandle)
    else:
        xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30002))+'!,5000)')


def playVideo(url):
    if url.endswith(".m3u8"):
        match = re.compile(',(.+?)k,', re.DOTALL).findall(url)
        maxBitrate = 0
        for br in match:
            br = int(br)
            if br <= bitrate:
                maxBitrate = br
        url = url.split(",")[0]+","+str(maxBitrate)+"k,.mp4.csmil/master.m3u8"
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    else:
        content = getUrl(url)
        match1 = re.compile('"m3u8": "(.*?)"', re.DOTALL).findall(content)
        match2 = re.compile("m3u8 			: '(.*?)'", re.DOTALL).findall(content)
        finalUrl = ""
        if match1 and match1[0]:
            finalUrl = match1[0]
        elif match2 and match2[0]:
            finalUrl = match2[0]
        if finalUrl:
            match = re.compile(',(.+?)k,', re.DOTALL).findall(finalUrl)
            maxBitrate = 0
            for br in match:
                br = int(br)
                if br <= bitrate:
                    maxBitrate = br
            finalUrl = finalUrl.split(",")[0]+","+str(maxBitrate)+"k,.mp4.csmil/master.m3u8"
            listitem = xbmcgui.ListItem(path=finalUrl)
            xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        else:
            match = re.compile('"contentId": "(.+?)"', re.DOTALL).findall(content)
            content = getUrl("http://services.media.dp.discovery.com/videos/"+match[0]+"/smil-service.smil")
            match = re.compile('<meta name="httpBase".+?content="(.+?)"', re.DOTALL).findall(content)
            base = match[0]
            maxBitrate = 0
            match = re.compile('<video src="(.+?)" system-bitrate="(.+?)"', re.DOTALL).findall(content)
            for urlTemp, bitrateTemp in match:
                bitrateTemp = int(bitrateTemp)
                if bitrateTemp > maxBitrate:
                    maxBitrate = bitrateTemp
                    finalUrl = urlTemp
            finalUrl = base+"/"+finalUrl+"?v=2.6.8&fp=&r=&g="
            listitem = xbmcgui.ListItem(path=finalUrl)
            xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
            if autoPlay > 0:
                xbmc.sleep(autoPlay*1000)
                if xbmc.Player().isPlaying() == True and int(xbmc.Player().getTime()) == 0:
                    xbmc.Player().pause()


def listAPL():
    content = getUrl("http://www.apl.tv/")
    match = re.compile('<div data-num=".+?">.*?<a href="(.+?)" title="(.+?)".+?<img src="(.+?)">', re.DOTALL).findall(content)
    for url, title, thumb in match:
        if title != "TV Highlights":
            addLink("LIVE: "+title, url, "playVideoLive", thumb, "")
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeNewsShows+')')
    xbmcplugin.endOfDirectory(pluginhandle)


def playVideoLive(url):
    content = getUrl(url)
    match = re.compile('content="https://www.ustream.tv/embed/(.+?)"', re.DOTALL).findall(content)
    m3u8_url = "http://iphone-streaming.ustream.tv/ustreamVideo/"+match[0]+"/streams/live/playlist.m3u8"
    listitem = xbmcgui.ListItem(path=m3u8_url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:23.0) Gecko/20100101 Firefox/23.0')
    response = urllib2.urlopen(req)
    content = response.read()
    response.close()
    return content


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


def addLink(name, url, mode, iconimage, desc, length="", date="", nr=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Aired": date, "Episode": "1"})
    if length:
        liz.addStreamInfo('video', {'duration': int(length)})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart:
        liz.setProperty("fanart_image", iconimage)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, type="", desc="", channelID=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&type="+str(type)+"&channelID="+str(channelID)+"&channelThumb="+urllib.quote_plus(iconimage)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addPluginDir(name, url, iconimage):
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
type = urllib.unquote_plus(params.get('type', ''))
channelID = urllib.unquote_plus(params.get('channelID', ''))
channelThumb = urllib.unquote_plus(params.get('channelThumb', ''))

if mode == 'listVideos':
    listVideos(url, type)
elif mode == 'listVideosMain':
    listVideosMain(url, channelThumb)
elif mode == 'listNewsMain':
    listNewsMain()
elif mode == 'listNewsCollections':
    listNewsCollections(url)
elif mode == 'listNews':
    listNews(url)
elif mode == 'listShows':
    listShows(url, channelID, channelThumb)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'playVideoLive':
    playVideoLive(url)
elif mode == 'listAPL':
    listAPL()
else:
    index()
