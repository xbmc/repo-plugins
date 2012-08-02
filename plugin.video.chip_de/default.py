#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,string,xbmcaddon,socket

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
settings = xbmcaddon.Addon(id='plugin.video.chip_de')
translation = settings.getLocalizedString

forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))

def index():
        addDir(string.upper(translation(30001)),"http://www.chip.de/Video_17367032.html?tid1=30593&tid2=0&of=0","listVideos","")
        content=getUrl("http://www.chip.de/Video_17367032.html")
        content=content[content.find('<table width="468" border="0" cellspacing="0" cellpadding="0">'):]
        content=content[:content.find('</table><br><br>')]
        spl=content.split("<td><a href")
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('name="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            addDir(string.upper(title),url+"&of=0","listVideos",thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<div class="mi-beitragsliste-videos chipTeaser')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('<span class="bl-b">(.+?)</span>', re.DOTALL).findall(entry)
            title=match[0]
            match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,url,"playVideo","http://www.chip.de"+thumb)
        match=re.compile('</a>\n        \n    \n\n    \n\n\n\n    <a href="(.+?)"><span> &gt; </span></a>', re.DOTALL).findall(entry)
        if len(match)>0:
            url=match[0]
            addDir(translation(30002),url,"listVideos","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        content = getUrl(url)
        match=re.compile('data-mp4="(.+?)"', re.DOTALL).findall(content)
        url=match[0]
        listitem = xbmcgui.ListItem(path=url)
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
         
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
