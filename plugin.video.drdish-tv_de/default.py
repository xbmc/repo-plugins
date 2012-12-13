#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])

settings = xbmcaddon.Addon(id='plugin.video.drdish-tv_de')
translation = settings.getLocalizedString

def index():
        addDir(translation(30001),"sendungen",'listCategories',"")
        addDir(translation(30002),"multimedia",'listCategories',"")
        addDir(translation(30003),"ratgeber",'listCategories',"")
        addDir(translation(30004),"leben-mit-zukunft",'listCategories',"")
        addDir(translation(30006),"gastformate",'listCategories',"")
        addDir(translation(30007),"http://www.drdish-tv.com/neueste-videos/",'listVideos',"")
        addDir(translation(30008),"http://www.drdish-tv.com/tv-programm/",'listVideosTV',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def listCategories(url):
        if url=="sendungen":
          listMultimedia()
          listRatgeber()
          listZukunft()
          listGastformate()
        elif url=="multimedia":
          listMultimedia()
        elif url=="ratgeber":
          listRatgeber()
        elif url=="leben-mit-zukunft":
          listZukunft()
        elif url=="gastformate":
          listGastformate()
        xbmcplugin.endOfDirectory(pluginhandle)

def listMultimedia():
          addDir("Pixel - Digital Lifestyle","http://www.drdish-tv.com/sendungen/multimedia/pixel/",'listVideos',"")
          addDir("Dr.Dish Magazin - Das Abenteuer","http://www.drdish-tv.com/sendungen/multimedia/dr-dish-magazin/",'listVideos',"")
          addDir("Hard & Soft - Produktneuheiten im Überblick","http://www.drdish-tv.com/sendungen/multimedia/hard-soft/",'listVideos',"")

def listRatgeber():
          addDir("Wissen Videos - Dr.Dish antwortet ","http://www.drdish-tv.com/sendungen/ratgeber/wissen-videos/",'listVideos',"")

def listZukunft():
          addDir("eTV - Erde Energie Effizienz ","http://www.drdish-tv.com/sendungen/wohnen-mit-zukunft/etv/",'listVideos',"")
          addDir("ESA TV","http://www.drdish-tv.com/sendungen/leben-mit-zukunft/esa-tv/",'listVideos',"")

def listGastformate():
          addDir("portalZINE TV","http://www.drdish-tv.com/sendungen/gastformate/portalzine-tv/",'listVideos',"")

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<div class="videocontent">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('tx_kaltura_pi1%5Bclipid%5D=(.+?)&amp;', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('<div class="videotitel"><h1>(.+?)</h1></div>', re.DOTALL).findall(entry)
            title=match[0]
            addLink(title,url,'playVideo',thumb)
        match=re.compile('<div class="kaltura-pagerBlockRight"><a href="(.+?)/">N(.+?)chste Seite', re.DOTALL).findall(content)
        if len(match)>0:
          url="http://www.drdish-tv.com/"+match[0][0]
          addDir("Next Page",url,'listVideos','')
        xbmcplugin.endOfDirectory(pluginhandle)

def listVideosTV(url):
        content = getUrl(url)
        spl=content.split('<div class="sendeplan-item">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('tx_kaltura_pi1%5Bclipid%5D=(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('<div class="sendeinhalt">(.+?)\n', re.DOTALL).findall(entry)
            title=urllib.unquote_plus(match[0])
            addLink(title,url,'playVideo',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
        content = getUrl("http://medianac.nacamar.de/p/435/sp/43500/playManifest/entryId/"+url+"/")
        match=re.compile('<media url="(.+?)"', re.DOTALL).findall(content)
        listitem = xbmcgui.ListItem(path=match[0])
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
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

if mode == 'listCategories':
    listCategories(url)
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'listVideosTV':
    listVideosTV(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
