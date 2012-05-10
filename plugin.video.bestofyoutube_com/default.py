#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcaddon
import xbmcplugin
import xbmcgui
import sys
import urllib, urllib2
import re

thisPlugin = int(sys.argv[1])

settings = xbmcaddon.Addon(id='plugin.video.bestofyoutube_com')
translation = settings.getLocalizedString

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def index():
        addDir(translation(30001),"NEW",1,"")
        addDir(translation(30002),"http://www.bestofyoutube.com/index.php?show=week",3,"")
        addDir(translation(30003),"http://www.bestofyoutube.com/index.php?show=month",3,"")
        addDir(translation(30004),"http://www.bestofyoutube.com/index.php?show=year",3,"")
        addDir(translation(30005),"http://www.bestofyoutube.com/index.php?show=alltime",3,"")
        addDir(translation(30006),"http://www.bestofyoutube.com/index.php?show=random",3,"")
        addDir(translation(30007),"SEARCH",4,"")
        xbmcplugin.endOfDirectory(thisPlugin)

def showContentLatest():
        content = getUrl("http://feeds.feedburner.com/bestofyoutubedotcom")
        match=re.compile('<item><title>(.+?)</title><description>(.+?)a href="(.+?)"(.+?)img src="(.+?)"', re.DOTALL).findall(content)
        for title,desc,url,temp,thumb in match:
                title=cleanTitle(title)
                addLink(title,url,2,thumb)
        xbmcplugin.endOfDirectory(thisPlugin)

def search():
        keyboard = xbmc.Keyboard('', str(translation(30007)))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          showContent("http://www.bestofyoutube.com/search.php?q="+search_string)

def playVideo(url):
        if url.find("http://")==0:
          content = getUrl(url)
          match=re.compile('<param name="movie" value="http://www.youtube.com/v/(.+?)&amp;', re.DOTALL).findall(content)
          youtubeID=match[0]
        else:
          youtubeID=url
        fullData = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + youtubeID
        listitem = xbmcgui.ListItem(path=fullData)
        return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)

def showContent(url):
        content = getUrl(url)
        spl=content.split("<div class='videoarea'>")
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('value="http://www.youtube.com/v/(.+?)&amp;', re.DOTALL).findall(entry)
            url=match[0]
            thumb="http://img.youtube.com/vi/"+url+"/0.jpg"
            match=re.compile("<div class='title'><a href='/(.+?)'>(.+?)</a>", re.DOTALL).findall(entry)
            title=match[0][1]
            title=cleanTitle(title)
            addLink(title,url,2,thumb)
        content=content[content.find('<div class="pagination">'):]
        content=content[:content.find('</div>')]
        spl=content.split("<a href=\"")
        for i in range(1,len(spl),1):
          entry=spl[i][:spl[i].find('</a>')]
          url="http://www.bestofyoutube.com/"+entry[:entry.find('"')]
          if entry.find('next &#187;')>=0:
            addDir("Next Page",url,3,'')
        xbmcplugin.endOfDirectory(thisPlugin)

def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
    response = urllib2.urlopen(req,timeout=30)
    link=response.read()
    response.close()
    return link

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

params = parameters_string_to_dict(sys.argv[2])
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
        showContentLatest()
elif mode==2:
        playVideo(url)
elif mode==3:
        showContent(url)
elif mode==4:
        search()
