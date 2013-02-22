#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(id='plugin.video.break_com')
translation = addon.getLocalizedString
forceViewMode=addon.getSetting("forceViewMode")
viewMode=str(addon.getSetting("viewMode"))

def index():
        addDir(translation(30001),"http://www.break.com/content/GetContentTimeStreamByChannelIdAndFilterBy?channelId=1&filterBy=videos&pageNum=1",'listChannelVideos',"")
        addDir(translation(30002),"http://www.break.com/content/GetContentByPageModuleAndPageTypeAndFilterBy?pageModuleTypeId=5&pageTypeId=4&filterBy=Daily&channelId=0&categoryId=0&numberOfContent=12",'listVideos',"")
        content = getUrl("http://www.break.com")
        spl=content.split('<a class="tip"')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile("<h1><span>(.+?)</span></h1>", re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            if url!="http://www.break.com/action-unleashed/":
              addDir(title,url,'listChannel',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listChannel(url):
        content = getUrl(url)
        match=re.compile("channelId           : (.+?),", re.DOTALL).findall(content)
        id=match[0]
        listChannelVideos("http://www.break.com/content/GetContentTimeStreamByChannelIdAndFilterBy?channelId="+id+"&filterBy=videos&pageNum=1")

def listChannelVideos(url):
        urlMain=url
        content = getUrl(url)
        match=re.compile('"MaxRecords":(.+?),', re.DOTALL).findall(content)
        max=int(match[0])
        spl=content.split('<article class=')
        for i in range(1,len(spl),1):
            entry=spl[i].replace("\\","")
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('alt="\\[(.+?)\\]', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
            desc=match[0]
            desc=cleanTitle(desc)
            addLink(title,url,'playVideo',thumb,desc)
        page=int(urlMain[urlMain.find("&pageNum=")+9:])
        baseUrl=urlMain[:urlMain.find("&pageNum=")+9]
        if (page*10)<max:
          addDir(translation(30003)+" ("+str(page+1)+")",baseUrl+str(page+1),'listChannelVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<article class=')
        for i in range(1,len(spl),1):
            entry=spl[i].replace("\\","")
            if entry.find('] Video"')>0:
              match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
              url=match[0]
              match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
              thumb=match[0]
              match=re.compile('alt="\\[(.+?)\\]', re.DOTALL).findall(entry)
              title=match[0]
              title=cleanTitle(title)
              addLink(title,url,'playVideo',thumb,"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
          content = getUrl(url)
          match1=re.compile("videoPath: '(.+?)'", re.DOTALL).findall(content)
          match2=re.compile("icon: '(.+?)'", re.DOTALL).findall(content)
          match3=re.compile("youtubeid=(.+?)&", re.DOTALL).findall(content)
          match4=re.compile("callForInfo: '(.+?)',", re.DOTALL).findall(content)
          match5=re.compile('src="http://www.theonion.com/video_embed/\\?id=(.+?)"', re.DOTALL).findall(content)
          url=""
          if len(match1)>0:
            url=match1[0]+"?"+match2[0]
            if match4[0]=="true":
              req = urllib2.Request(url.replace("_1.flv","_3.mp4"))
              try:
                urllib2.urlopen(req)
                url=url.replace("_1.flv","_3.mp4")
              except:
                req = urllib2.Request(url.replace("_1.flv","_2.mp4"))
                try:
                  urllib2.urlopen(req)
                  url=url.replace("_1.flv","_2.mp4")
                except:
                  pass
          elif len(match3)>0:
            if xbox==True:
              url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + match3[0]
            else:
              url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + match3[0]
          elif len(match5)>0:
            content = getUrl("http://www.theonion.com/video_embed/?id="+match5[0])
            match=re.compile('<source src="(.+?)" type="(.+?)">', re.DOTALL).findall(content)
            for urlTemp, type in match:
              if type=="video/mp4":
                url=urlTemp
          listitem = xbmcgui.ListItem(path=url)
          return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        return title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#038;","&").replace("&#39;","'").replace("&#039;","'").replace("&#8211;","-").replace("&#8220;","-").replace("&#8221;","-").replace("&#8217;","'").replace("&quot;","\"").strip()

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

if mode == 'listChannelVideos':
    listChannelVideos(url)
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'listChannel':
    listChannel(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
