#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(id='plugin.video.lachschon_de')
translation = addon.getLocalizedString

forceViewMode=addon.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(addon.getSetting("viewMode"))

def index():
        addDir(translation(30005),"http://www.lachschon.de/gallery/new/?set_gallery_type=video&set_image_type=small&page=1","listVideos","")
        addDir(translation(30001),"http://www.lachschon.de/gallery/trend/?set_gallery_type=video&set_image_type=small&page=1","listVideos","")
        addDir(translation(30002),"http://www.lachschon.de/gallery/top/?set_gallery_type=video&set_image_type=small&page=1","listVideos","")
        addDir(translation(30007),"http://www.lachschon.de/gallery/mostvoted/?set_gallery_type=video&set_image_type=small&page=1","listVideos","")
        addDir(translation(30003),"http://www.lachschon.de/gallery/random/?set_gallery_type=video&set_image_type=small&page=1","listVideos","")
        addDir(translation(30004),"SEARCH","search","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', str(translation(30004)))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listVideos("http://www.lachschon.de/gallery/search_item/?set_gallery_type=video&set_image_type=small&q="+search_string)

def listVideos(url):
        content = getUrl(url)
        match=re.compile('<a class="direction forward" href="\\?page=(.+?)">weiter <', re.DOTALL).findall(content)
        urlNextPage=""
        if len(match)>0:
          urlNextPage=url[:url.find("&page=")]+"&page="+match[0]
        content = content[content.find('<ul id="itemlist">'):content.find('<p class="advert-notice">')]
        spl=content.split('<li>')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<a href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('<span class="rating">(.+?)</span>', re.DOTALL).findall(entry)
            rating=-1
            if len(match)>0:
              rating=int(int(match[0].replace(".",""))/10)
            match=re.compile('class="title" href="(.+?)"(.+?)title="(.+?)">(.+?)\n', re.DOTALL).findall(entry)
            title=match[0][3]
            title=cleanTitle(title)
            if rating!=-1:
              title=title+" ("+str(rating)+"%)"
            addLink(title,"http://www.lachschon.de"+url,"playVideo",thumb)
        if urlNextPage!="":
          addDir(translation(30006),urlNextPage,"listVideos",'')
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        content = getUrl(url)
        youtubeID=content[content.find('http://www.youtube.com/embed/')+29:]
        youtubeID=youtubeID[:youtubeID.find('?')]
        if xbox==True:
          fullData = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + youtubeID
        else:
          fullData = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + youtubeID
        listitem = xbmcgui.ListItem(path=fullData)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&#39;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')
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
elif mode == 'search':
    search()
else:
    index()
