#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import xbmcplugin
import xbmcaddon
import xbmcgui
import datetime
import sys
import re
import os

#addon = xbmcaddon.Addon()
#addonID = addon.getAddonInfo('id')
addonID = 'plugin.video.ardmediathek_de'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
translation = addon.getLocalizedString
baseUrl = "http://www.ardmediathek.de"
showSubtitles = addon.getSetting("showSubtitles") == "true"
forceViewMode = addon.getSetting("forceViewMode") == "true"
useThumbAsFanart=addon.getSetting("useThumbAsFanart") == "true"
showDateInTitle=addon.getSetting("showDateInTitle") == "true"
viewMode = str(addon.getSetting("viewIDVideos"))
viewModeShows = str(addon.getSetting("viewIDShows"))
defaultThumb = baseUrl+"/ard/static/pics/default/16_9/default_webM_16_9.jpg"
defaultBackground = "http://www.ard.de/pool/img/ard/background/base_xl.jpg"
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
addon_work_folder = xbmc.translatePath("special://profile/addon_data/"+addonID)
channelFavsFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/fav_new")
subFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/sub.srt")

if not os.path.isdir(addon_work_folder):
    os.mkdir(addon_work_folder)


def index():
    addDir(translation(30011), "", 'listShowsFavs', "")
    addDir(translation(30001), baseUrl+"/tv/Neueste-Videos/mehr?documentId=21282466", 'listVideos', "")
    addDir(translation(30002), baseUrl+"/tv/Meistabgerufene-Videos/mehr?documentId=21282514", 'listVideos', "")
    addDir(translation(30004), baseUrl+"/tv/Film-Highlights/mehr?documentId=21301808", 'listVideos', "")
    addDir(translation(30003), baseUrl+"/tv/Reportage-Doku/mehr?documentId=21301806", 'listVideos', "")
    addDir(translation(30005), "", 'listShowsAZMain', "")
    addDir(translation(30006), "mehr", 'listCats', "")
    addDir(translation(30007), "Dossier", 'listCats', "")
    addDir(translation(30014), "", 'listEinsLike', "")
    addDir(translation(30020), "", 'listChannels', "")
    addDir(translation(30008), "", 'search', "")
    addDir(translation(30013), "", 'listLiveChannels', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    content = getUrl(url)
    spl = content.split('<div class="teaser" data-ctrl')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('documentId=(.+?)&', re.DOTALL).findall(entry)
        videoID = match[0]
        matchTitle = re.compile('class="headline">(.+?)<', re.DOTALL).findall(entry)
        match = re.compile('class="dachzeile">(.+?)<', re.DOTALL).findall(entry)
        if match and match[0].endswith("Uhr"):
            date = match[0]
            date = date.split(" ")[0]
            date = date[:date.rfind(".")]
            if showDateInTitle:
                title = date+" - "+matchTitle[0]
        elif match:
            title = match[0]+" - "+matchTitle[0]
        else:
            title = matchTitle[0]
        match = re.compile('class="subtitle">(.+?) \\| (.+?) min(.+?)</p>', re.DOTALL).findall(entry)
        match2 = re.compile('class="subtitle">(.+?) min.*?</p>', re.DOTALL).findall(entry)
        duration = ""
        desc = ""
        if match:
            date = match[0][0]
            date = date[:date.rfind(".")]
            duration = match[0][1]
            channel = match[0][2].replace("<br/>","")
            if "00:" in duration:
                duration = 1
            if showDateInTitle:
                title = date+" - "+title
            desc = channel+" ("+date+")\n"+title
        elif match2:
            duration = match2[0]
            if "00:" in duration:
                duration = 1
        title = cleanTitle(title)
        match = re.compile('/image/(.+?)/16x9/', re.DOTALL).findall(entry)
        thumb = baseUrl+"/image/"+match[0]+"/16x9/448"
        addLink(title, videoID, 'playVideo', thumb, duration, desc)
    match = re.compile('class="entry" data-ctrl-.*Loader-source="{&#039;pixValue&#039;.+?href="(.+?)">(.+?)<', re.DOTALL).findall(content)
    for url, type in match:
        if "&gt;" in type:
            addDir(translation(30009), baseUrl+url.replace("&amp;","&"), "listVideos", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listChannelVideos(url):
    content = getUrl(url)
    spl = content.split('class="headline" data-ctrl')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('documentId=(.+?)&', re.DOTALL).findall(entry)
        if match:
            videoID = match[0]
            match = re.compile('class="titel">(.+?)<', re.DOTALL).findall(entry)
            title = match[0]
            match = re.compile('class="date">(.+?)<', re.DOTALL).findall(entry)
            title = match[0]+" - "+title
            addLink(cleanTitle(title), videoID, 'playVideo', icon)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listLiveChannels():
    addLink("Das Erste", "", "playLiveARD", "http://m-service.daserste.de/appservice/1.4.1/image/broadcast/fallback/jpg/512")
    content = getUrl(baseUrl+"/tv/live?kanal=Alle")
    spl = content.split('<div class="teaser" data-ctrl')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('kanal=(.+?)"', re.DOTALL).findall(entry)
        channelID = match[0]
        match = re.compile('class="headline">(.+?)<', re.DOTALL).findall(entry)
        title = match[0]
        match = re.compile('/image/(.+?)/16x9/', re.DOTALL).findall(entry)
        thumb = baseUrl+"/image/"+match[0]+"/16x9/448"
        if title!="Das Erste":
            addLink(cleanTitle(title), channelID, 'playLive', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeShows+')')


def listShowsAZMain():
    addDir("0-9", "0-9", 'listShowsAZ', "")
    letters = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
    for letter in letters:
        addDir(letter.upper(), letter.upper(), 'listShowsAZ', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listShowsAZ(letter):
    content = getUrl(baseUrl+"/tv/sendungen-a-z?buchstabe="+letter)
    spl = content.split('<div class="teaser" data-ctrl')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('documentId=(.+?)&', re.DOTALL).findall(entry)
        showID = match[0]
        match = re.compile('class="headline">(.+?)<', re.DOTALL).findall(entry)
        title = match[0]
        match = re.compile('/image/(.+?)/16x9/', re.DOTALL).findall(entry)
        thumb = baseUrl+"/image/"+match[0]+"/16x9/448"
        addShowDir(cleanTitle(title), baseUrl+"/tv/Sendung?documentId="+showID, 'listVideos', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeShows+')')


def listShowsFavs():
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    if os.path.exists(channelFavsFile):
        fh = open(channelFavsFile, 'r')
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
        xbmc.executebuiltin('Container.SetViewMode('+viewModeShows+')')


def listEinsLike():
    addDir(translation(30001), baseUrl+"/einslike/Neueste-Videos/mehr?documentId=21282466", 'listVideos', "")
    addDir(translation(30002), baseUrl+"/einslike/Meistabgerufene-Videos/mehr?documentId=21282464", 'listVideos', "")
    addDir(translation(30015), baseUrl+"/einslike/Musik/mehr?documentId=21301894", 'listVideos', "")
    addDir(translation(30016), baseUrl+"/einslike/Leben/mehr?documentId=21301896", 'listVideos', "")
    addDir(translation(30017), baseUrl+"/einslike/Netz-Tech/mehr?documentId=21301898", 'listVideos', "")
    addDir(translation(30018), baseUrl+"/einslike/Info/mehr?documentId=21301900", 'listVideos', "")
    addDir(translation(30019), baseUrl+"/einslike/Spa%C3%9F-Fiktion/mehr?documentId=21301902", 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listChannels():
    addDir("Das Erste", "208", 'listChannel', icon)
    addDir("BR", "2224", 'listChannel', icon)
    addDir("HR", "5884", 'listChannel', icon)
    addDir("MDR", "5882", 'listChannel', icon)
    addDir("NDR", "5906", 'listChannel', icon)
    addDir("RB", "5898", 'listChannel', icon)
    addDir("RBB", "5874", 'listChannel', icon)
    addDir("SR", "5870", 'listChannel', icon)
    addDir("SWR", "5310", 'listChannel', icon)
    addDir("WDR", "5902", 'listChannel', icon)
    addDir("Tagesschau24", "5878", 'listChannel', icon)
    addDir("EinsPlus", "4178842", 'listChannel', icon)
    addDir("EinsFestival", "673348", 'listChannel', icon)
    addDir("DW-TV", "5876", 'listChannel', icon)
    xbmcplugin.endOfDirectory(pluginhandle)


def listChannel(channel):
    addDir("Heute", baseUrl+"/tv/sendungVerpasst?kanal="+channel+"&tag=0", 'listChannelVideos', "")
    addDir("Gestern", baseUrl+"/tv/sendungVerpasst?kanal="+channel+"&tag=1", 'listChannelVideos', "")
    addDir((datetime.date.today()-datetime.timedelta(days=2)).strftime("%b %d, %Y"), baseUrl+"/tv/sendungVerpasst?kanal="+channel+"&tag=2", 'listChannelVideos', "")
    addDir((datetime.date.today()-datetime.timedelta(days=3)).strftime("%b %d, %Y"), baseUrl+"/tv/sendungVerpasst?kanal="+channel+"&tag=3", 'listChannelVideos', "")
    addDir((datetime.date.today()-datetime.timedelta(days=4)).strftime("%b %d, %Y"), baseUrl+"/tv/sendungVerpasst?kanal="+channel+"&tag=4", 'listChannelVideos', "")
    addDir((datetime.date.today()-datetime.timedelta(days=5)).strftime("%b %d, %Y"), baseUrl+"/tv/sendungVerpasst?kanal="+channel+"&tag=5", 'listChannelVideos', "")
    addDir((datetime.date.today()-datetime.timedelta(days=6)).strftime("%b %d, %Y"), baseUrl+"/tv/sendungVerpasst?kanal="+channel+"&tag=6", 'listChannelVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listCats(type):
    content = getUrl(baseUrl+"/tv")
    spl = content.split('<div class="teaser" data-ctrl')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = match[0]
        if "/"+type+"?" in url:
            match = re.compile('documentId=(.+?)&', re.DOTALL).findall(entry)
            showID = match[0]
            match = re.compile('class="headline">(.+?)<', re.DOTALL).findall(entry)
            if match:
                title = match[0]
                match = re.compile('/image/(.+?)/16x9/', re.DOTALL).findall(entry)
                thumb = baseUrl+"/image/"+match[0]+"/16x9/448"
                addDir(cleanTitle(title), baseUrl+"/tv/?documentId="+showID, 'listVideos', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewModeShows+')')


def playVideo(videoID):
    content = getUrl(baseUrl+"/tv/?documentId="+videoID)
    match = re.compile('<div class="box fsk.*?class="teasertext">(.+?)</p>', re.DOTALL).findall(content)
    if match:
        xbmc.executebuiltin('XBMC.Notification(Info:,'+match[0].strip()+',15000)')
    else:
        content = getUrl(baseUrl+"/play/media/"+videoID+"?devicetype=pc&features=flash")
        match1 = re.compile('"_stream":\\[(.+?)\\]', re.DOTALL).findall(content)
        match2 = re.compile('"_quality":.+?,"_server":"(.*?)","_cdn":".*?","_stream":"(.+?)"', re.DOTALL).findall(content)
        matchUT = re.compile('"_subtitleUrl":"(.+?)"', re.DOTALL).findall(content)
        matchLive = re.compile('"_isLive":(.+?),', re.DOTALL).findall(content)
        url = ""
        if match1:
            url = match1[0].split(",")[0].replace('"','')
        elif match2:
            for server, stream in match2:
                if server.startswith("rtmp"):
                    if matchLive[0]=="true":
                        url = server+" playpath="+stream+" live=true"
                    elif server:
                        url = server+stream
                elif matchLive[0]=="true" or not server:
                    url = stream
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        if showSubtitles and matchUT:
            setSubtitle(baseUrl+matchUT[0])


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def playLive(liveID):
    content = getUrl(baseUrl+"/tv/live?kanal="+liveID)
    match = re.compile('/play/media/(.+?)&', re.DOTALL).findall(content)
    playVideo(match[0])


def playLiveARD():
    content = getUrl("http://live.daserste.de/de/livestream.xml")
    match = re.compile('<asset type=".*?Live HLS">.+?<fileName>(.+?)</fileName>', re.DOTALL).findall(content)
    url = ""
    if match:
        url = match[0]
    if url:
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def setSubtitle(url):
    if os.path.exists(subFile):
        os.remove(subFile)
    try:
        content = getUrl(url)
    except:
        content = ""
    if content:
        matchLine = re.compile('<p id=".+?" begin="1(.+?)" end="1(.+?)".+?>(.+?)</p>', re.DOTALL).findall(content)
        fh = open(subFile, 'a')
        count = 1
        for begin, end, line in matchLine:
            begin = "0"+begin.replace(".",",")[:-1]
            end = "0"+end.replace(".",",")[:-1]
            match = re.compile('<span(.+?)>', re.DOTALL).findall(line)
            for span in match:
                line = line.replace("<span"+span+">","")
            line = line.replace("<br />","\n").replace("</span>","").strip()
            fh.write(str(count)+"\n"+begin+" --> "+end+"\n"+cleanTitle(line)+"\n\n")
            count+=1
        fh.close()
        xbmc.sleep(1000)
        xbmc.Player().setSubtitles(subFile)


def search():
    keyboard = xbmc.Keyboard('', translation(30008))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        listVideos(baseUrl+"/tv/suche?searchText="+search_string)


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#034;", "\"").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö").replace("&eacute;", "é").replace("&egrave;", "è")
    title = title.replace("&#x00c4;","Ä").replace("&#x00e4;","ä").replace("&#x00d6;","Ö").replace("&#x00f6;","ö").replace("&#x00dc;","Ü").replace("&#x00fc;","ü").replace("&#x00df;","ß")
    title = title.replace("&apos;","'").strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def favs(param):
    mode = param[param.find("###MODE###=")+11:]
    mode = mode[:mode.find("###")]
    channelEntry = param[param.find("###TITLE###="):]
    if mode == "ADD":
        if os.path.exists(channelFavsFile):
            fh = open(channelFavsFile, 'r')
            content = fh.read()
            fh.close()
            if content.find(channelEntry) == -1:
                fh = open(channelFavsFile, 'a')
                fh.write(channelEntry+"\n")
                fh.close()
        else:
            fh = open(channelFavsFile, 'a')
            fh.write(channelEntry+"\n")
            fh.close()
    elif mode == "REMOVE":
        refresh = param[param.find("###REFRESH###=")+14:]
        refresh = refresh[:refresh.find("#")]
        fh = open(channelFavsFile, 'r')
        content = fh.read()
        fh.close()
        entry = content[content.find(channelEntry):]
        fh = open(channelFavsFile, 'w')
        fh.write(content.replace(channelEntry+"\n", ""))
        fh.close()
        if refresh == "TRUE":
            xbmc.executebuiltin("Container.Refresh")


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, duration="", desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=defaultThumb, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Duration": duration, "Plot": desc})
    liz.setProperty('IsPlayable', 'true')
    if useThumbAsFanart:
        if not iconimage or iconimage==icon or iconimage==defaultThumb:
            iconimage = defaultBackground
        liz.setProperty("fanart_image", iconimage)
    else:
        liz.setProperty("fanart_image", defaultBackground)
    liz.addContextMenuItems([(translation(30012), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    if useThumbAsFanart:
        if not iconimage or iconimage==icon or iconimage==defaultThumb:
            iconimage = defaultBackground
        liz.setProperty("fanart_image", iconimage)
    else:
        liz.setProperty("fanart_image", defaultBackground)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addShowDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=defaultThumb, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if useThumbAsFanart:
        if not iconimage or iconimage==icon or iconimage==defaultThumb:
            iconimage = defaultBackground
        liz.setProperty("fanart_image", iconimage)
    else:
        liz.setProperty("fanart_image", defaultBackground)
    playListInfos = "###MODE###=ADD###TITLE###="+name+"###URL###="+urllib.quote_plus(url)+"###THUMB###="+iconimage+"###END###"
    liz.addContextMenuItems([(translation(30028), 'RunPlugin(plugin://'+addonID+'/?mode=favs&url='+urllib.quote_plus(playListInfos)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addShowFavDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=defaultThumb, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if useThumbAsFanart:
        if not iconimage or iconimage==icon or iconimage==defaultThumb:
            iconimage = defaultBackground
        liz.setProperty("fanart_image", iconimage)
    else:
        liz.setProperty("fanart_image", defaultBackground)
    playListInfos = "###MODE###=REMOVE###REFRESH###=TRUE###TITLE###="+name+"###URL###="+urllib.quote_plus(url)+"###THUMB###="+iconimage+"###END###"
    liz.addContextMenuItems([(translation(30029), 'RunPlugin(plugin://'+addonID+'/?mode=favs&url='+urllib.quote_plus(playListInfos)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listChannelVideos':
    listChannelVideos(url)
elif mode == 'listEinsLike':
    listEinsLike()
elif mode == 'listShowsFavs':
    listShowsFavs()
elif mode == 'listChannel':
    listChannel(url)
elif mode == 'listChannels':
    listChannels()
elif mode == 'listLiveChannels':
    listLiveChannels()
elif mode == 'listShowsAZMain':
    listShowsAZMain()
elif mode == 'listShowsAZ':
    listShowsAZ(url)
elif mode == 'listCats':
    listCats(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == "queueVideo":
    queueVideo(url, name)
elif mode == 'playLiveARD':
    playLiveARD()
elif mode == 'playLive':
    playLive(url)
elif mode == 'search':
    search()
elif mode == 'favs':
    favs(url)
else:
    index()
