#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])

settings = xbmcaddon.Addon(id='plugin.video.lachschon_de')
translation = settings.getLocalizedString

def index():
        addDir(translation(30001),"http://www.lachschon.de/gallery/trend/?set_gallery_type=video&set_image_type=small&page=1",1,"")
        addDir(translation(30002),"http://www.lachschon.de/gallery/mostvoted/?set_gallery_type=video&set_image_type=small&page=1",1,"")
        addDir(translation(30003),"http://www.lachschon.de/gallery/top/?set_gallery_type=video&set_image_type=small&page=1",1,"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(50)')

def listVideos(url):
        content = getUrl(url)
        urlNextPage=""
        if content.find('">weiter <')>=0:
          nextPage=content[content.find('<a class="direction" href="?page=')+33:]
          nextPage=nextPage[:nextPage.find('"')]
          urlNextPage=url[:url.find("&page=")]+"&page="+nextPage
        content = content[content.find('<ul id="itemlist">'):content.find('<p class="advert-notice">')]
        spl=content.split('<li>')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<a href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('<span class="subtitle">(.+?)</span>', re.DOTALL).findall(entry)
            title=match[0]
            addLink(title,"http://www.lachschon.de"+url,2,thumb)
        if urlNextPage!="":
          addDir("Next Page",urlNextPage,1,'')
        xbmcplugin.endOfDirectory(pluginhandle)
        if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(500)')

def playVideo(url):
        content = getUrl(url)
        id=content[content.find('http://www.youtube.com/embed/')+29:]
        id=id[:id.find('?')]
        fullData = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
        listitem = xbmcgui.ListItem(path=fullData)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
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
url=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass


if mode==None or url==None or len(url)<1:
        index()
       
elif mode==1:
        listVideos(url)
elif mode==2:
        playVideo(url)
