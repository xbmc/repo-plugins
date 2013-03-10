#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.video.sevenload_de')
translation = addon.getLocalizedString
forceViewMode=addon.getSetting("forceViewMode")
viewMode=str(addon.getSetting("viewMode"))
mainUrl="http://www.sevenload.com/paginate?api_key=c2435678afb6fda6e5f5a67c8a9b88e7&limit=20&offset=0&sevenload_video_category="

def index():
        addDir(translation(30003),mainUrl+"Autos",'listVideos',"")
        addDir(translation(30004),mainUrl+"Entertainment",'listVideos',"")
        addDir(translation(30005),mainUrl+"Fashion",'listVideos',"")
        addDir(translation(30006),mainUrl+"Fun",'listVideos',"")
        addDir(translation(30007),mainUrl+"Lifestyle",'listVideos',"")
        addDir(translation(30008),mainUrl+"Musik",'listVideos',"")
        addDir(translation(30009),mainUrl+"News",'listVideos',"")
        addDir(translation(30010),mainUrl+"Sport",'listVideos',"")
        addDir(translation(30011),mainUrl+"Technik",'listVideos',"")
        addDir(translation(30012),mainUrl+"Wissen",'listVideos',"")
        addDir(translation(30002),"",'search',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        match=re.compile('offset=(.+?)&', re.DOTALL).findall(url)
        offset=match[0]
        nextOffset=str(int(offset)+20)
        nextUrl=url.replace("offset="+offset, "offset="+nextOffset)
        spl=content.split('<li>')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url="http://www.sevenload.com"+match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('<span class="duration">(.+?)</span>', re.DOTALL).findall(entry)
            duration=match[0].strip()
            if duration.startswith("00:"):
              duration=1
            match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            addLink(title,url,'playVideo',thumb,duration)
        addDir(translation(30001),nextUrl,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', translation(30002))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listVideos('http://www.sevenload.com/search?limit=20&offset=0&q='+search_string)

def playVideo(url):
          content = getUrl(url)
          match=re.compile("src&quot;:&quot;(.+?)&quot;", re.DOTALL).findall(content)
          listitem = xbmcgui.ListItem(path=match[0])
          return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        return title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#038;","&").replace("&#39;","'").replace("&#039;","'").replace("&#8211;","-").replace("&#8220;","-").replace("&#8221;","-").replace("&#8217;","'").replace("&quot;","\"").strip()

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:19.0) Gecko/20100101 Firefox/19.0')
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

def addLink(name,url,mode,iconimage,duration):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Duration": duration } )
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
