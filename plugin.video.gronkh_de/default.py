#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcaddon,xbmcplugin,xbmcgui,sys,urllib,urllib2,re,socket

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
settings = xbmcaddon.Addon(id='plugin.video.gronkh_de')
translation = settings.getLocalizedString

forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))

def index():
        addDir(translation(30001),"http://gronkh.de/","listVideos","")
        addDir(translation(30002),"http://gronkh.de/lets-play","listGames","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<div class="entry entry-letsplay"')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('<a class="thumb" href="(.+?)" title=""><img src="(.+?)"', re.DOTALL).findall(entry)
          url=match[0][0]
          thumb=match[0][1]
          temp=entry[entry.find('<div class="text">'):]
          match=re.compile('title="(.+?)"', re.DOTALL).findall(temp)
          title=match[0]
          match=re.compile('<h2><a href="(.+?)" title="(.+?)">(.+?)</a></h2>', re.DOTALL).findall(entry)
          title2=match[0][2]
          title=title+" - "+title2
          title=cleanTitle(title)
          addLink(title,url,'playVideo',thumb)
          match=re.compile('</a></li><li><a href="(.+?)" class="next">', re.DOTALL).findall(entry)
          if len(match)>0:
            addDir(translation(30003),match[0],"listVideos","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listGames():
        content = getUrl("http://gronkh.de/lets-play")
        content = content[content.find('<div class="postpadding">'):]
        content = content[:content.find('</div>')]
        spl=content.split('<a href=')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('"(.+?)"', re.DOTALL).findall(entry)
          url="http://gronkh.de"+match[0]
          match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
          title=match[0]
          match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
          thumb=match[0]
          title=cleanTitle(title)
          addDir(title,url,'listVideos',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        content = getUrl(url)
        match=re.compile('src="http://www.youtube.com/embed/(.+?)\\?', re.DOTALL).findall(content)
        youtubeID=match[0]
        if xbox==True:
          fullData = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + youtubeID
        else:
          fullData = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + youtubeID
        listitem = xbmcgui.ListItem(path=fullData)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
        if xbox==True:
          socket.setdefaulttimeout(30)
          response = urllib2.urlopen(req)
        else:
          response = urllib2.urlopen(req,timeout=30)
        link=response.read()
        response.close()
        return link

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&#038;","&").replace("&#8230;","...").replace("&#8211;","-").replace("&#8220;","-").replace("&#8221;","-").replace("&#8217;","'")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def addLink(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

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

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listGames':
    listGames()
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
