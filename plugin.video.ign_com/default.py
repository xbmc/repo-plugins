#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.video.ign_com')
translation = addon.getLocalizedString

maxVideoQuality=addon.getSetting("maxVideoQualityRes")
forceViewMode=addon.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(addon.getSetting("viewMode"))

maxVideoHeight = [360,540,720,1080][int(maxVideoQuality)]
maxVideoBitrate=[1000000,1500000,2500000,5000000][int(maxVideoQuality)]
maxVideoQuality=[640,960,1280,1920][int(maxVideoQuality)]

def index():
        addDir(translation(30002),"http://www.ign.com/videos/all/filtergalleryajax?filter=all",'listVideos',"")
        addDir("IGN Daily Fix","http://www.ign.com/videos/series/ign-daily-fix",'listVideos',"")
        addDir("IGN Live","http://www.ign.com/videos/series/ign-live",'listVideos',"")
        addDir("IGN First","http://www.ign.com/videos/series/playstation-app-ign-first",'listVideos',"")
        addDir(translation(30003),"http://www.ign.com/videos/all/filtergalleryajax?filter=games-review",'listVideos',"")
        addDir(translation(30004),"http://www.ign.com/videos/all/filtergalleryajax?filter=games-trailer",'listVideos',"")
        addDir(translation(30005),"http://www.ign.com/videos/all/filtergalleryajax?filter=movies-trailer",'listVideos',"")
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
              l = length.split(':')
              length = int(l[0])*60 + int(l[1])
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
              thumb = ""
              if match:
                  thumb=match[0].replace("_small.jpg", ".jpg")
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
              thumb=match[0].replace("_small.jpg", ".jpg")
            addDir(title,url,'listVideos',thumb,date)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', translation(30008))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listSearchResults('http://www.ign.com/search?q='+search_string+'&page=0&count=10&type=video')

def listSearchResults(url):
        urlMain = url
        content = getUrl(url)
        spl=content.split('<div class="search-item"')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=""
            if match:
                thumb=cleanUrl(match[0]).replace("_small.jpg", ".jpg")
            entry=entry[entry.find('<div class="search-item-title">'):]
            match=re.compile('<span class="duration">(.+?)<span>', re.DOTALL).findall(entry)
            length=""
            if len(match)>0:
              length=cleanTitle(match[0])
            match=re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
            url=match[0][0]
            title=match[0][1]
            title=cleanTitle(title)
            addLink(title,url,'playVideo',thumb,"",length)
        match=re.compile('data-page="(.+?)"', re.DOTALL).findall(content)
        page=int(match[0])
        match=re.compile('data-total="(.+?)"', re.DOTALL).findall(content)
        maxPage=int(int(match[0])/10)
        urlNext=urlMain.replace("page="+str(page),"page="+str(page+1))
        if page<maxPage:
          addDir(translation(30001),urlNext,'listSearchResults',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        content = getUrl(url)
        match4 = re.compile("data-video='(.+?)'", re.DOTALL).findall(content)
        if match4:
            listOfUrls = re.compile('"url":"(.+?)","height":(.+?),"', re.DOTALL).findall(match4[0])
            videoUrl = ""
            for x in range(0, len(listOfUrls)):
                if maxVideoHeight >= int(listOfUrls[x][1]):
                    videoUrl = listOfUrls[x][0]
            finalUrl = videoUrl.replace("\\", "")
        else:
            match1 = re.compile('"video_id":"(.+?)"', re.DOTALL).findall(content)
            match2 = re.compile('data-id="(.+?)"', re.DOTALL).findall(content)
            match3 = re.compile('data-video-id="(.+?)"', re.DOTALL).findall(content)
            videoID = ""
            if match1:
                videoID=match1[0]
            elif match2:
                videoID=match2[0]
            elif match3:
                videoID=match3[0]
            content = getUrl("http://www.ign.com/videos/configs/id/"+videoID+".config").replace("\\", "")
            match = re.compile('"url":"(.+?)/zencoder/(.+?)/(.+?)/(.+?)/(.+?)/(.+?)-(.+?)-(.+?)"', re.DOTALL).findall(content)
            startUrl = match[0][0]
            date = match[0][1]+"/"+match[0][2]+"/"+match[0][3]
            resolution = int(match[0][4])
            vidID = match[0][5]
            bitrate = match[0][6]
            ext = match[0][7]
            if maxVideoQuality < resolution:
                resolution = maxVideoQuality
                bitrate = maxVideoBitrate
            finalUrl = startUrl+"/zencoder/"+date+"/"+str(resolution)+"/"+vidID+"-"+str(bitrate)+"-"+ext
        listitem = xbmcgui.ListItem(path=finalUrl)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
          

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.replace("<em>","").replace("</em>","").strip()
        return title

def cleanUrl(title):
        title=title.replace("&#x3A;",":").replace("&#x2F;","/")
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11')
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