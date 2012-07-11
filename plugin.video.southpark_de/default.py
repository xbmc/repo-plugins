#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
settings = xbmcaddon.Addon(id='plugin.video.southpark_de')
translation = settings.getLocalizedString

language=settings.getSetting("language")
forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))

if language=="0":
  language=""
elif language=="1":
  language="en"

def index():
        addLink(translation(30003),"",'playRandom',"","")
        content = getUrl("http://www.southpark.de/alleEpisoden/")
        content = content[content.find('<div id="content_epfinder"'):]
        content = content[:content.find('<div class="content_carouselwrap">')]
        match=re.compile('href="(.+?)">(.+?)</a>', re.DOTALL).findall(content)
        for url, staffel in match:
          addDir(str(translation(30001))+" "+staffel,"http://www.southpark.de"+url,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playRandom():
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        i=1
        for i in range(1,100,1):
          if xbox==True:
            url="plugin://video/SouthPark.de/?url=http://www.southpark.de/alleEpisoden/random/&mode=playVideo"
          else:
            url="plugin://plugin.video.southpark_de/?url=http://www.southpark.de/alleEpisoden/random/&mode=playVideo"
          listitem = xbmcgui.ListItem("South Park: "+translation(30003)+" "+str(i))
          i=i+1
          playlist.add(url,listitem)

def listVideos(url):
        content = getUrl(url)
        match=re.compile('<li><span>(.+?)</span></li>', re.DOTALL).findall(content)
        season=match[0]
        spl=content.split('<li class="grid_item">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<span class="title eptitle">(.+?)</span>', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('<span class="epnumber">(.+?)</span>', re.DOTALL).findall(entry)
            episode=match[0]
            match=re.compile('<span class="epdesc">(.+?)</span>', re.DOTALL).findall(entry)
            desc=match[0]
            match=re.compile('href="/alleEpisoden/(.+?)/"', re.DOTALL).findall(entry)
            url="http://www.southpark.de/alleEpisoden/"+match[0]+"/"
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(episode+" - "+title,url,'playVideo',thumb,desc)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        content = getUrl(url)
        matchTitle=re.compile('<meta name="title" content="(.+?)"', re.DOTALL).findall(content)
        matchDesc=re.compile('<meta name="description" content="(.+?)"', re.DOTALL).findall(content)
        match=re.compile(':southparkstudios.de:(.+?)"', re.DOTALL).findall(content)
        if len(match)>0:
          content = getUrl("http://www.southpark.de/feeds/video-player/mrss/mgid%3Ahcx%3Acontent%3Asouthparkstudios.de%3A"+match[0]+"?lang="+language)
          spl=content.split('<item>')
          urlFull="stack://"
          for i in range(1,len(spl),1):
              entry=spl[i]
              match=re.compile('<media:content url="(.+?)"', re.DOTALL).findall(entry)
              url=match[0]
              content = getUrl(url)
              matchMp4=re.compile('bitrate="(.+?)" width="(.+?)" height="(.+?)" type="video/mp4">\n<src>(.+?)</src>', re.DOTALL).findall(content)
              matchFlv=re.compile('bitrate="(.+?)" width="(.+?)" height="(.+?)" type="video/x-flv">\n<src>(.+?)</src>', re.DOTALL).findall(content)
              urlNew=""
              bitrate=0
              if len(matchMp4)>0:
                match=matchMp4
              elif len(matchFlv)>0:
                match=matchFlv
              for br,temp1,temp2,url in match:
                if int(br)>bitrate:
                  bitrate=int(br)
                  urlNew=url
                  if urlNew.find("/mtvnorigin/")>=0:
                    urlNew="http://mtvni.rd.llnwd.net/44620"+urlNew[urlNew.find("/mtvnorigin/"):]
                  elif urlNew.find("/mtviestor/")>=0:
                    urlNew="http://mtvni.rd.llnwd.net/44620/cdnorigin"+urlNew[urlNew.find("/mtviestor/"):]
              urlFull+=urlNew+" , "
          urlFull=urlFull[:-3]
          listitem = xbmcgui.ListItem(path=urlFull)
          title=matchTitle[0]
          if title.find("South Park: ")==-1:
            title="South Park: "+title
          desc=matchDesc[0]
          listitem.setInfo( type="Video", infoLabels={ "Title": title , "Plot": desc } )
          return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        else:
          xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30004))+'!,5000)')

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/13.0')
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

def addLink(name,url,mode,iconimage,desc):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name , "Plot": desc } )
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
elif mode == 'sortDirection':
    sortDirection(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
elif mode == 'playRandom':
    playRandom()
else:
    index()
