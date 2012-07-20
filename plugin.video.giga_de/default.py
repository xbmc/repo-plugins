#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
settings = xbmcaddon.Addon(id='plugin.video.giga_de')
translation = settings.getLocalizedString

forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))

maxVideoQuality=settings.getSetting("maxVideoQuality")
qual=["360p","720p"]
maxVideoQuality=qual[int(maxVideoQuality)]

def index():
        addDir(translation(30001),"http://www.giga.de/tv/alle-videos/",'listVideos',"")
        addDir("Top Videos","http://www.giga.de/tv/",'listVideosTop',"")
        addDir("Giga Live","http://www.giga.de/giga-tv/videos/giga-live/",'listVideos',"")
        addDir("Gameplay","http://www.giga.de/giga-tv/videos/giga-gameplay/",'listVideos',"")
        addDir("Specials","http://www.giga.de/giga-tv/videos/specials/",'listVideos',"")
        addDir("Monatsvorschau","http://www.giga.de/giga-tv/giga-monatsvorschau/",'listVideos',"")
        addDir("Nostalgiga","http://www.giga.de/giga-tv/videos/nostalgiga/",'listVideos',"")
        addDir("Radio Giga","http://www.giga.de/giga-tv/videos/radio-giga/",'listVideos',"")
        addDir("Top100 Movies","http://www.giga.de/giga-tv/videos/top-100-filme/",'listVideos',"")
        addDir("Top100 Games","http://www.giga.de/giga-tv/videos/top-100-games/",'listVideos',"")
        addDir("Tobis tolle Taktikanalyse","http://www.giga.de/giga-tv/videos/tobis-tolle-taktikanalyse/",'listVideos',"")
        addDir("Jonas liest","http://www.giga.de/giga-tv/videos/jonas-liest/",'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideosTop(url):
        content = getUrl(url)
        spl=content.split('<div class="row video-player">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<a href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('<span class="tooltip">(.+?)</span>', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            addLink(title,url,'playVideo',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        mainUrl=url
        content = getUrl(url)
        spl=content.split('<div class="meta-posttype">')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('"VIDEO_ID":"(.+?)"', re.DOTALL).findall(entry)
          match2=re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
          if len(match)>0:
            url=match[0]
          else:
            url=match2[0][0]
          title=match2[0][1]
          thumb=""
          match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
          if len(match)>0:
            thumb=match[0]
          title=cleanTitle(title)
          addLink(title,url,'playVideo',thumb)
        if mainUrl.find("/page/")>=0:
          match=re.compile('/page/(.+?)/', re.DOTALL).findall(mainUrl)
          nr=str(int(match[0])+1)
          newUrl=mainUrl[:-2]+nr+"/"
        else:
          nr="2"
          newUrl=mainUrl+"page/2/"
        fh = open("d:\\html.txt", 'w')
        fh.write(newUrl)
        fh.close()
        if content.find("/page/"+nr+"/")>=0:
            addDir(translation(30002)+" ("+nr+")",newUrl,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        if url.find("http://")>=0:
          content = getUrl(url)
          match=re.compile('<a name="video-(.+?)"></a>', re.DOTALL).findall(content)
          if len(match)>0:
            url=match[0]
          else:
            url=""
            xbmc.executebuiltin('XBMC.Notification(Achtung:,Video nicht verfügbar!, 5000)')
        if url!="":
          content = getUrl("http://video.giga.de/xml/"+url+".xml")
          match1=re.compile('<high width="1280" height="720">(.+?)<filename>(.+?)</filename>', re.DOTALL).findall(content)
          match2=re.compile('<medium width="640" height="360">(.+?)<filename>(.+?)</filename>', re.DOTALL).findall(content)
          url=""
          if len(match1)==1 and maxVideoQuality=="720p":
            url=match1[0][1]
          elif len(match2)==1:
            url=match2[0][1]
          listitem = xbmcgui.ListItem(path="http://video.giga.de/data/"+url)
          return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        return title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#038;","&").replace("&#039;","\\").replace("&#8211;","-").replace("&#8220;","-").replace("&#8221;","-").replace("&#8217;","'").replace("&quot;","\"").strip()

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

if mode == 'listVideosTop':
    listVideosTop(url)
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
