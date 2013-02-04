#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcaddon,xbmcplugin,xbmcgui,sys,urllib,urllib2,re,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(id='plugin.video.bestofyoutube_com')
translation = addon.getLocalizedString

forceViewMode=addon.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(addon.getSetting("viewMode"))

def index():
        addDir(translation(30001),"http://www.bestofyoutube.com","listVideos","")
        addDir(translation(30008),"","bestOf","")
        addDir(translation(30006),"http://www.bestofyoutube.com/index.php?show=random","listVideos","")
        addDir(translation(30007),"","search","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def bestOf():
        addDir(translation(30002),"http://www.bestofyoutube.com/index.php?show=week","listVideos","")
        addDir(translation(30003),"http://www.bestofyoutube.com/index.php?show=month","listVideos","")
        addDir(translation(30004),"http://www.bestofyoutube.com/index.php?show=year","listVideos","")
        addDir(translation(30005),"http://www.bestofyoutube.com/index.php?show=alltime","listVideos","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', translation(30007))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listVideos("http://www.bestofyoutube.com/search.php?q="+search_string)

def playVideo(id):
        if xbox==True:
          url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
        else:
          url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def listLatest():
        content = getUrl("http://feeds.feedburner.com/bestofyoutubedotcom")
        match=re.compile('<item><title>(.+?)</title><description>(.+?)a href="(.+?)"(.+?)img src="(.+?)"', re.DOTALL).findall(content)
        for title,desc,url,temp,thumb in match:
                addLink(title,url,2,thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        spl=content.split("<div class='main'>")
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('value="http://www.youtube.com/v/(.+?)&amp;', re.DOTALL).findall(entry)
            id=match[0]
            match=re.compile("name='up'>(.+?)<", re.DOTALL).findall(entry)
            up=float(match[0])
            match=re.compile("name='down'>(.+?)<", re.DOTALL).findall(entry)
            down=float(match[0])
            thumb="http://img.youtube.com/vi/"+id+"/0.jpg"
            match=re.compile("<div class='title'><a href='/(.+?)'>(.+?)</a>", re.DOTALL).findall(entry)
            title=match[0][1]
            title=cleanTitle(title)
            if (up+down)>0:
              percentage=int((up/(up+down))*100)
            else:
              percentage=100
            title=title+" ("+str(percentage)+"%)"
            addLink(title,id,"playVideo",thumb)
        content=content[content.find('<div class="pagination">'):]
        content=content[:content.find('</div>')]
        spl=content.split("<a href=\"")
        for i in range(1,len(spl),1):
          entry=spl[i][:spl[i].find('</a>')]
          url="http://www.bestofyoutube.com/"+entry[:entry.find('"')]
          if entry.find('next &#187;')>=0:
            addDir(translation(30009),url,"listVideos",'')
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

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

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listLatest':
    listLatest()
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'bestOf':
    bestOf()
elif mode == 'search':
    search()
else:
    index()
