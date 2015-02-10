#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcaddon,xbmcplugin,xbmcgui,sys,urllib,urllib2,re,socket

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(id='plugin.video.ebaumsworld_com')
translation = addon.getLocalizedString

forceViewMode=addon.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(addon.getSetting("viewMode"))

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def index():
        addDir(translation(30001),"http://www.ebaumsworld.com/newest/video/","listVideos","")
        addDir(translation(30002),"http://www.ebaumsworld.com/newest/video/featured/","listVideos","")
        addDir(translation(30003),"http://www.ebaumsworld.com/popular/week/video/","listVideos","")
        addDir(translation(30004),"http://www.ebaumsworld.com/popular/video/","listVideos","")
        addDir(translation(30005),"http://www.ebaumsworld.com/popular/all/video/","listVideos","")
        addDir(translation(30008),"http://www.ebaumsworld.com/tags/b-o-m/video/","listVideos","")
        addDir(translation(30006),"","search","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        matchPage=re.compile('<a class="next" href="(.+?)">', re.DOTALL).findall(content)
        content = content[content.find('<ul class="mediaListingGrid" id="mediaList">'):]
        content = content[:content.find('<div class="paginationControl">')]
        spl=content.split('<li class="mediaGridItem ">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<li class="title">.+?<span>(.+?)</span>', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('href="/video/watch/(.+?)/"', re.DOTALL).findall(entry)
            id=match[0]
            match=re.compile('<li class="viewStat">(.+?)</li>', re.DOTALL).findall(entry)
            views=match[0].strip()
            match=re.compile('<li class="commentStat">(.+?)</li>', re.DOTALL).findall(entry)
            comments=match[0]
            match=re.compile('<span class="uploadTime">(.+?)</span>', re.DOTALL).findall(entry)
            date=match[0]
            match=re.compile('<span class="listingStars"><span title="(.+?) stars"', re.DOTALL).findall(entry)
            if len(match)>0:
              try:
                rating=int(float(match[0])*20)
                title=title+" ("+str(rating)+"%)"
              except:
                pass
            match=re.compile('<li class="description">(.+?)</li>', re.DOTALL).findall(entry)
            desc=match[0]
            desc=date+" - "+views+" Views - "+comments+" Comments\nDescription: "+desc
            match=re.compile('data-src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,id,'playVideo',thumb,desc)
        if len(matchPage)>0:
          urlNext="http://www.ebaumsworld.com"+matchPage[0]
          addDir(translation(30007),urlNext,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', translation(30006))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listVideos('http://www.ebaumsworld.com/search/'+search_string+'/video/')

def playVideo(id):
        content = getUrl("http://www.ebaumsworld.com/video/player/"+id+"?env=id0")
        match=re.compile('<file>(.+?)</file>', re.DOTALL).findall(content)
        url=match[0]
        if url.find("youtube.com")>0:
          id=url[url.find("=")+1:]
          if xbox==True:
            url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
          else:
            url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
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

def addLink(name,url,mode,iconimage,desc):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
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
elif mode == 'search':
    search()
else:
    index()
