#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.n24_de')
translation = settings.getLocalizedString

def index():
        addDir(translation(30001),"most_clicked",1,"")
        addDir("Dokumentationen","doku",1,"")
        addDir("Reportagen","reportage",1,"")
        addDir("Magazine","magazin",1,"")
        addDir("Computer/Technik","computer",1,"")
        addDir("Wirtschaft/Börse","wirtschaft",1,"")
        addDir("MM - Das Männermagazin","maennermagazin",1,"")
        addDir("History","history",1,"")
        addDir("Panorama","panorama",1,"")
        addDir("Politik","politik",1,"")
        addDir("Spezial","spezial",1,"")
        addDir("Auto","auto",1,"")
        addDir("Talks","talk",1,"")
        addDir("N24 "+str(translation(30002)),"search",8,"")
        addLink("N24 Live Stream","live",9,"")
        xbmcplugin.endOfDirectory(pluginhandle)

def catToUrl(cat):
        listVideos("http://www.n24.de/mediathek/api/box_renderer/GenerateExtendedBox?dataset_name="+cat+"&page=1&limit=40")

def listVideos(url1):
        content = getUrl(url1)
        match=re.compile('<a class="img_wrapper" href="(.+?)">\n                                    <img src="(.+?)" width="192" height="108" alt="(.+?)" />\n                                    <span class="play">abspielen</span>\n                                    <strong class="ellipsis">(.+?)</strong>\n                                </a>', re.DOTALL).findall(content)
        for url,thumb,temp,title in match:
                addLink(temp,"http://www.n24.de"+url,2,"http://www.n24.de/mediathek/"+thumb)
        match=re.compile('<span class="page_number">(.+?) von (.+?)</span>', re.DOTALL).findall(content)
        currentPage=int(match[0][0])
        maxPage=int(match[0][1])
        if currentPage<maxPage:
          urlNew=url1[:url1.find("&page=")]+"&page="+str(currentPage+1)+"&limit=40"
          addDir("Next Page",urlNew,7,'')
        xbmcplugin.endOfDirectory(pluginhandle)

def search():
        keyboard = xbmc.Keyboard('', 'Video Suche')
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText()
          listVideos("http://www.n24.de/mediathek/api/box_renderer/GenerateSearchResultsBox?search_string="+search_string+"&page=1&limit=40")

def liveStream():
        try:
          playLiveStream()
        except:
          try:
            playLiveStream()
          except:
            try:
              playLiveStream()
            except:
              xbmc.executebuiltin('XBMC.Notification(Info,'+str(translation(30001))+',5000)')

def playLiveStream():
        content = getUrl("http://www.n24.de/mediathek/n24-livestream/stream.html")
        match=re.compile('filename&quot;:&quot;(.+?)&quot;', re.DOTALL).findall(content)
        filename=match[0]
        listitem = xbmcgui.ListItem(path="rtmp://pssimn24livefs.fplive.net/pssimn24live-live/"+filename+" swfUrl=http://www.n24.de/media/flash/homeplayer_swf.swf live=true timeout=60")
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def playVideo(url):
        content = getUrl(url)
        match=re.compile('filename&quot;:&quot;(.+?)&quot;', re.DOTALL).findall(content)
        filename=match[0]
        listitem = xbmcgui.ListItem(path="rtmp://pssimn24livefs.fplive.net/pssimn24/"+filename)
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
        catToUrl(url)
elif mode==2:
        playVideo(url)
elif mode==7:
        listVideos(url)
elif mode==8:
        search()
elif mode==9:
        liveStream()
