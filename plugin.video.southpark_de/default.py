#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(id='plugin.video.southpark_de')
translation = addon.getLocalizedString

language=addon.getSetting("language")
forceViewMode=addon.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(addon.getSetting("viewMode"))
playIntro=addon.getSetting("playIntro")

if language=="0":
  language=""
elif language=="1":
  language="en"

def index():
        addLink(translation(30003),"",'playRandom',"","")
        content = getUrl("http://www.southpark.de/alle-episoden")
        content = content[content.find('content_epfinder'):]
        content = content[:content.find('content_carouselwrap')]
        match=re.compile('data-promoId="(.+?)"', re.DOTALL).findall(content)
        promoId=match[0]
        match=re.compile('href="(.+?)">(.+?)</a>', re.DOTALL).findall(content)
        for url, staffel in match:
          if url.find("/random")==-1:
            addDir(str(translation(30001))+" "+staffel,"http://www.southpark.de/feeds/full-episode/carousel/"+staffel+"/"+promoId,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playRandom():
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        i=1
        for i in range(1,100,1):
          if xbox==True:
            url="plugin://video/SouthPark.de/?url=http://www.southpark.de/alle-episoden/random&mode=playVideo"
          else:
            url="plugin://plugin.video.southpark_de/?url=http://www.southpark.de/alle-episoden/random&mode=playVideo"
          listitem = xbmcgui.ListItem("South Park: "+translation(30003)+" "+str(i))
          i=i+1
          playlist.add(url,listitem)

def listVideos(url):
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        content = getUrl(url)
        spl=content.split('title:')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile("'(.+?)',", re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile("episodenumber:'(.+?)'", re.DOTALL).findall(entry)
            episode=match[0]
            nr="S"+episode[0:2]+"E"+episode[2:4]
            match=re.compile("description:'(.+?)'", re.DOTALL).findall(entry)
            desc=match[0]
            match=re.compile("url:'(.+?)'", re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile("thumbnail:'(.+?)'", re.DOTALL).findall(entry)
            thumb=match[0]
            thumb=thumb[:thumb.find("?")]
            addLink(nr+" - "+title,url,'playVideo',thumb,desc)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        content = getUrl(url)
        matchTitle=re.compile('<h1 itemprop="name">(.+?)</h1>', re.DOTALL).findall(content)
        matchDesc=re.compile('<h2 itemprop="description">(.+?)</h2>', re.DOTALL).findall(content)
        matchSE=re.compile('/s(.+?)e(.+?)-', re.DOTALL).findall(content)
        match=re.compile('http://media.mtvnservices.com/mgid:arc:episode:southpark.de:(.+?)"', re.DOTALL).findall(content)
        if len(match)>0:
          content = getUrl("http://www.southpark.de/feeds/video-player/mrss/mgid%3Aarc%3Aepisode%3Asouthpark.de%3A"+match[0]+"?lang="+language)
          spl=content.split('<item>')
          urlFull="stack://"
          start=2
          if playIntro=="true":
            start=1
          for i in range(start,len(spl),1):
              entry=spl[i]
              match=re.compile('<media:content type="text/xml" medium="video" duration="(.+?)" isDefault="true" url="(.+?)"', re.DOTALL).findall(entry)
              url=match[0][1].replace("&amp;","&")
              content = getUrl(url)
              if 'currently undergoing maintenance' in content:
                continue
              matchMp4=re.compile('width="(.+?)" height="(.+?)" type="video/mp4" bitrate="(.+?)">(.+?)<src>(.+?)</src>', re.DOTALL).findall(content)
              matchFlv=re.compile('width="(.+?)" height="(.+?)" type="video/x-flv" bitrate="(.+?)">(.+?)<src>(.+?)</src>', re.DOTALL).findall(content)
              urlNew=""
              bitrate=0
              if len(matchMp4)>0:
                match=matchMp4
              elif len(matchFlv)>0:
                match=matchFlv
              for temp1,temp2,br,temp3,url in match:
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
          title="S"+matchSE[0][0]+"E"+matchSE[0][1]+" - "+matchTitle[0]
          desc=matchDesc[0]
          listitem.setInfo( type="Video", infoLabels={ "Title": title , "Plot": desc } )
          return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        else:
          xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30004))+'!,5000)')

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.replace("\\'","'").strip()
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
