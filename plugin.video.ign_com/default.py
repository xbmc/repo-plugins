#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.video.ign_com')
translation = addon.getLocalizedString

maxVideoQuality=addon.getSetting("maxVideoQuality")
forceViewMode=addon.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(addon.getSetting("viewMode"))

qual=[500000,1000000,2500000,3000000]
maxVideoQuality=qual[int(maxVideoQuality)]

def index():
        addDir(translation(30002),"http://www.ign.com/videos/all/filtergalleryajax?filter=all",'listVideos',"")
        addDir("IGN Daily Fix","http://www.ign.com/videos/series/ign-daily-fix",'listVideos',"")
        addDir("IGN Live","http://www.ign.com/videos/series/ign-live",'listVideos',"")
        addDir(translation(30003),"http://www.ign.com/videos/all/filtergalleryajax?filter=games-review",'listVideos',"")
        addDir(translation(30004),"http://www.ign.com/videos/all/filtergalleryajax?filter=games-trailer",'listVideos',"")
        addDir(translation(30005),"http://www.ign.com/videos/all/filtergalleryajax?filter=movies-trailer",'listVideos',"")
        #addDir(translation(30006),"http://www.ign.com/videos/all/filtergalleryajax?filter=series",'listVideos',"")
        addDir(translation(30007),"http://www.ign.com/videos/allseriesajax",'listSeries',"")
        addDir(translation(30008),"",'search',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<div class="grid_16 alpha bottom_2">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<li>(.+?)</li>', re.DOTALL).findall(entry)
            if len(match)>0:
              length=match[0].replace(" mins","")
              match=re.compile('<p class="video-description">\n                    <span class="publish-date">(.+?)</span> -(.+?)</p>', re.DOTALL).findall(entry)
              date=match[0][0]
              desc=match[0][1]
              desc=cleanTitle(desc)
              match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
              title=match[0]
              title=cleanTitle(title)
              match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
              url=match[0]
              match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
              thumb=match[0]
              addLink(title,url,'playVideo',thumb,date+"\n"+desc,length)
        matchPage=re.compile('<a id="moreVideos" href="(.+?)"', re.DOTALL).findall(content)
        if len(matchPage)>0:
          urlNext="http://www.ign.com"+matchPage[0]
          addDir(translation(30001),urlNext,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listSeries(url):
        content = getUrl(url)
        spl=content.split('<div class="grid_16 alpha bottom_2">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<li>(.+?)</li>', re.DOTALL).findall(entry)
            date=match[0]
            match=re.compile('<p class="video-description">(.+?)</p>', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            thumb=""
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            if len(match)>0:
              thumb=match[0]
            addDir(title,url,'listVideos',thumb,date)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', translation(30008))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listSearchResults('http://www.ign.com/search/video?query='+search_string+'&sort=&videotype=')

def listSearchResults(url):
        content = getUrl(url)
        spl=content.split('<div class="video-result clear">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<span class="publisherLink">(.+?)</span>', re.DOTALL).findall(entry)
            date=match[0]
            match=re.compile('<a class="video-title" href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
            url=match[0][0]
            title=match[0][1]
            title=cleanTitle(title)
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,url,'playVideo',thumb,date)
        matchPage=re.compile('href="(.+?)">(.+?)</a>', re.DOTALL).findall(content)
        for url, title in matchPage:
          if title=="Next&nbsp;&raquo;":
            urlNext="http://www.ign.com"+url
            addDir(translation(30001),urlNext,'listSearchResults',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        content = getUrl(url)
        match=re.compile('data-video-id="(.+?)"', re.DOTALL).findall(content)
        content = getUrl("http://apis.ign.com/video/v3/videos/osmf/"+match[0]+".smil")
        match=re.compile('<video src="(.+?)" system-bitrate="(.+?)"/>', re.DOTALL).findall(content)
        finalUrl=""
        for url, bitrate in match:
          if int(bitrate)<=maxVideoQuality:
            finalUrl="http://"+url
        listitem = xbmcgui.ListItem(path=finalUrl)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:16.0) Gecko/20100101 Firefox/16.0')
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

def addLink(name,url,mode,iconimage,desc="",duration=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc, "Duration": duration } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage,desc=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
         
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listSeries':
    listSeries(url)
elif mode == 'listSearchResults':
    listSearchResults(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
else:
    index()
