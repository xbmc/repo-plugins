#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import os
import re
import xbmcplugin
import xbmcaddon
import xbmcgui

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = 'plugin.video.euronews_com'
addon = xbmcaddon.Addon(id=addonID)
translation = addon.getLocalizedString

while (not os.path.exists(xbmc.translatePath("special://profile/addon_data/"+addonID+"/settings.xml"))):
    addon.openSettings()

forceViewMode = addon.getSetting("forceViewMode")
viewMode = str(addon.getSetting("viewMode"))
language = addon.getSetting("language")
languages = ["en", "gr", "fr", "de", "it",
             "es", "pt", "pl", "ru", "ua", "tr", "ar", "pe"]
language = languages[int(language)]
language2 = language.replace("en", "www").replace(
    "pe", "persian").replace("ar", "arabic")


def index():
    addLink(translation(30001), "", 'playLive', "")
    addDir(translation(30002), "", 'newsMain', "")
    content = getUrl("http://"+language2+".euronews.com")
    match = re.compile(
        '<li class="menu-element-programs"><a title="(.+?)" href="(.+?)">', re.DOTALL).findall(content)
    addDir(match[0][0], "http://"+language2+".euronews.com"+match[
           0][1], 'listShows', "")
    content = content[content.find('<ol id="categoryNav">'):]
    content = content[:content.find('</ol>')]
    spl = content.split('<a')
    for i in range(2, len(spl), 1):
        entry = spl[i]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = "http://"+language2+".euronews.com"+match[0]
        match = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        if "/nocomment/" in url:
            addDir(title, url, 'listNoComment', "")
        elif "/travel/" not in url and "/in-vogue/" not in url:
            addDir(title, url, 'listVideos', "")
    addDir(translation(30004), "", 'search', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode == "true":
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def newsMain():
    addDir(translation(30003), "http://"+language2 +
           ".euronews.com/news/", 'listVideos', "")
    content = getUrl("http://"+language2+".euronews.com")
    content = content[content.find('<ol class="lhsMenu">'):]
    content = content[:content.find('</ol>')]
    spl = content.split('<a')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = "http://"+language2+".euronews.com"+match[0]
        match = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        addDir(title, url, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode == "true":
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listVideos(url):
    content = getUrl(url)
    if 'class="topStoryTitle"' in content:
        content1 = content[content.find('class="topStoryTitle"'):]
        content1 = content1[:content1.find("</div>")]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(content1)
        url = "http://"+language2+".euronews.com"+match[0]
        match = re.compile('src="(.+?)"', re.DOTALL).findall(content1)
        thumb = match[0]
        match = re.compile('<p>(.+?)</p>', re.DOTALL).findall(content1)
        desc = ""
        if len(match) > 0:
            desc = match[0]
            desc = cleanTitle(desc)
        match = re.compile('title="(.+?)"', re.DOTALL).findall(content1)
        match2 = re.compile('alt="(.+?)"', re.DOTALL).findall(content1)
        if len(match) > 0:
            title = match[0]
        elif len(match2) > 0:
            title = match2[0]
        title = cleanTitle(title)
        match = re.compile(
            '<p class="cet" style="(.+?)">(.+?) (.+?)</p>', re.DOTALL).findall(content1)
        date = ""
        if len(match) > 0:
            date = match[0][1]
            title = date+" - "+title
        addLink(title, url, 'playVideo', thumb, desc)

    content2 = content
    content = content[content.find('id="main-content">'):]
    if "</ul></div>" in content:
        content = content[:content.find("</ul></div>")]
    elif 'id="headline-block">' in content:
        content = content[:content.find('id="headline-block">')]
    content2 = content2[content2.find('id="headline-block">'):]
    content2 = content2[:content2.find('</div>')]
    spl = content.split('<a class="imgWrap"')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        if 'class="vid"' in entry:
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url = "http://"+language2+".euronews.com"+match[0]
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0]
            match1 = re.compile('> \\| (.+?) (.+?)<', re.DOTALL).findall(entry)
            match2 = re.compile(
                '<span class="artDate">(.+?) (.+?)</span>', re.DOTALL).findall(entry)
            match3 = re.compile(
                '<p class="cet">(.+?) - (.+?) (.+?)</p>', re.DOTALL).findall(entry)
            date = ""
            if len(match1) > 0:
                date = match1[0][0]
            elif len(match2) > 0:
                date = match2[0][0]
            elif len(match3) > 0:
                date = match3[0][1]
            match = re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
            desc = ""
            if len(match) > 0:
                desc = match[0]
                desc = cleanTitle(desc)
            match = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            match2 = re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
            if len(match) > 0:
                title = match[0]
            elif len(match2) > 0:
                title = match2[0]
            title = cleanTitle(title)
            if date != "":
                title = date+" - "+title
            addLink(title, url, 'playVideo', thumb, desc)
    spl = content2.split('<li')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('>(.+?) -', re.DOTALL).findall(entry)
        date = match[0]
        match = re.compile(
            '  <a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
        url = "http://"+language2+".euronews.com"+match[0][0]
        title = match[0][1]
        title = date+" - "+cleanTitle(title)
        addLink(title, url, 'playVideo', "", "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode == "true":
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listNoComment(url):
    content = getUrl(url)
    match = re.compile(
        '<p id="topStoryImg"><a href="(.+?)" title="(.+?)"><img src="(.+?)"', re.DOTALL).findall(content)
    match2 = re.compile(
        '<span class="cet">(.+?) (.+?)</span>', re.DOTALL).findall(content)
    addLink(match2[0][0]+" - "+match[0][1], "http://"+language2 +
            ".euronews.com"+match[0][0], 'playVideo', match[0][2], "")
    spl = content.split('<div class="column span-8')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile(
            '<em>nocomment \\| (.+?) (.+?)</em>', re.DOTALL).findall(entry)
        date = match[0][0]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = "http://"+language2+".euronews.com"+match[0]
        match = re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        title = date+" - "+cleanTitle(title)
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]
        addLink(title, url, 'playVideo', thumb, "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode == "true":
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listShows(url):
    content = getUrl(url)
    spl = content.split('<a name')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
        url = "http://"+language2+".euronews.com"+match[0]
        match = re.compile('title="(.+?)"', re.DOTALL).findall(entry)
        title = match[0]
        title = cleanTitle(title)
        match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
        thumb = match[0]
        match = re.compile(
            'class="artTitle">(.+?)</p>', re.DOTALL).findall(entry)
        desc = ""
        if len(match) > 0:
            desc = match[0]
            desc = cleanTitle(desc)
        if "/nocomment/" in url:
            addDir(title, url, 'listNoComment', thumb, desc)
        elif "/travel/" not in url and "/in-vogue/" not in url:
            addDir(title, url, 'listVideos', thumb, desc)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode == "true":
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def search():
    keyboard = xbmc.Keyboard('', translation(30004))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        content = getUrl(
            "http://"+language2+".euronews.com/search/", data="q="+search_string)
        content = content[content.find('<ol class="searchRes">'):]
        content = content[:content.find('</ol>')]
        spl = content.split('<li')
        for i in range(1, len(spl), 1):
            entry = spl[i]
            match = re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url = "http://"+language2+".euronews.com"+match[0]
            match = re.compile('<em>(.+?)</em>', re.DOTALL).findall(entry)
            title = match[0].replace("<strong>", "").replace(
                "</strong>", "").replace("<br />", "")
            title = cleanTitle(title)
            match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0]
            addLink(title, url, 'playVideo', thumb, "")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode == "true":
            xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playVideo(url):
    content = getUrl(url)
    match = re.compile('videofile:"(.+?)"', re.DOTALL).findall(content)
    if len(match) > 0:
        listitem = xbmcgui.ListItem(
            path="http://video.euronews.com/"+match[0]+".flv")
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def playLive():
    content = getUrl("http://euronews.hexaglobe.com/json/")
    content = content[content.find('"'+language+'":'):]
    match = re.compile('"server":"(.+?)"', re.DOTALL).findall(content)
    server = match[0].replace("\\", "")
    url = server.replace("rtmp","rtsp")+language+"_video750_rtp.sdp"
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def cleanTitle(title):
    return title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#038;", "&").replace("&#39;", "'").replace("&#039;", "'").replace("&#8211;", "-").replace("&#8220;", "-").replace("&#8221;", "-").replace("&#8217;", "'").replace("&quot;", "\"").strip()


def getUrl(url, data=None, cookie=None):
    if data != None:
        req = urllib2.Request(url, data)
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    else:
        req = urllib2.Request(url)
    req.add_header(
        'User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
    if cookie != None:
        req.add_header('Cookie', cookie)
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


def addLink(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(
        name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(
        sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(
        name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    ok = xbmcplugin.addDirectoryItem(handle=int(
        sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listNoComment':
    listNoComment(url)
elif mode == 'listShows':
    listShows(url)
elif mode == 'newsMain':
    newsMain()
elif mode == 'playLive':
    playLive()
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
else:
    index()
