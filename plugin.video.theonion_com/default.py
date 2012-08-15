#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.theonion_com')
translation = settings.getLocalizedString

forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))

def index():
        addDir(translation(30002),"http://www.theonion.com/ajax/onn_playlist/mostrecent/1/",'listVideos',"")
        content = getUrl("http://www.theonion.com/articles/latest/video/")
        matchPage=re.compile('<a class="next_page" rel="next" href="(.+?)">', re.DOTALL).findall(content)
        content = content[content.find('class="label">SHOWS</li>'):]
        content = content[:content.find('<li rel="featured">')]
        match=re.compile('<li rel="(.+?)"><a><span></span>(.+?)</a></li>', re.DOTALL).findall(content)
        for id, title in match:
          addDir(title.replace("<br>"," "),"http://www.theonion.com/ajax/onn_playlist/"+id+"/1/",'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<li class="element_')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('video_(.+?)"', re.DOTALL).findall(entry)
            id=match[0]
            match=re.compile('<p class="title"><a href="(.+?)">(.+?)</a></p>', re.DOTALL).findall(entry)
            title=match[0][1]
            title=cleanTitle(title)
            match=re.compile('<p class="teaser">(.+?)</p>', re.DOTALL).findall(entry)
            desc=""
            if len(match)>0:
              desc=match[0]
              desc=cleanTitle(desc)
            match=re.compile('<p class="info"><span class="showname">(.+?)</span> \\((.+?)\\)</p>', re.DOTALL).findall(entry)
            length=match[0][1]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,id,'playVideo',thumb,length,desc)
        match1=re.compile('<span id="nextpage">(.+?)</span>', re.DOTALL).findall(content)
        match2=re.compile('<span id="slug">(.+?)</span>', re.DOTALL).findall(content)
        if len(match1)>0:
          urlNext="http://www.theonion.com/ajax/onn_playlist/"+match2[0]+"/"+match1[0]+"/"
          addDir(translation(30001),urlNext,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(id):
        content = getUrl("http://www.theonion.com/videos/embed/"+id+".json")
        match=re.compile('"video_url": "(.+?)"', re.DOTALL).findall(content)
        listitem = xbmcgui.ListItem(path=match[0])
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/13.0')
        response = urllib2.urlopen(req)
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

def addLink(name,url,mode,iconimage,duration,desc):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Duration": duration, "Plot": desc } )
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
