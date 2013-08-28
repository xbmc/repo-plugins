#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import re
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")


def index():
    content = getUrl("http://wochenwebschau.tumblr.com/")
    spl = content.split('<div class="post-panel"')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        match = re.compile('<div class="copy">(.+?)</div>', re.DOTALL).findall(entry)
        title = match[0]
        match = re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(title)
        if match:
            title = match[0]
        title = title.replace("<p>", "").replace("</p>", "").replace("<span>", "").replace("</span>", "")
        if ">" in title:
            title = title[title.find(">")+1:]
            if ">" in title:
                title = title[title.find(">")+1:]
        if title[len(title)-1:]==":":
            title = title[:-1]
        title = cleanTitle(title)
        match = re.compile('src="http://www.youtube.com/embed/(.+?)\\?', re.DOTALL).findall(entry)
        id = match[0]
        thumb = "http://img.youtube.com/vi/"+id+"/0.jpg"
        addLink(title, id, 'playVideo', thumb)
    xbmcplugin.endOfDirectory(pluginhandle)


def playVideo(id):
    listitem = xbmcgui.ListItem(path=getYoutubePluginUrl(id))
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def getYoutubePluginUrl(id):
    if xbox:
        return "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
    else:
        return "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id


def cleanTitle(title):
    title = title = title.replace("&#039;", "'").replace("&#8211;", "-").replace("&#8220;", "-").replace("&#8221;", "-").replace("&#8217;", "'").replace("&#8230;", "…")
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:23.0) Gecko/20100101 Firefox/23.0')
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


def addLink(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))

if mode == 'playVideo':
    playVideo(url)
else:
    index()
