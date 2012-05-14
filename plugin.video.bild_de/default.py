#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.bild_de')
translation = settings.getLocalizedString

def index():
        addDir("News","http://www.bild.de/video/clip/news/news-15477962.bild.html",'showVideos',"")
        addDir(translation(30001),"http://www.bild.de/video/clip/politik/politik-15714862.bild.html",'showVideos',"")
        addDir(translation(30002),"http://www.bild.de/video/clip/leute/leute-15715942.bild.html",'showVideos',"")
        addDir("TV","http://www.bild.de/video/clip/tv/tv-15715994.bild.html",'showVideos',"")
        addDir(translation(30003),"http://www.bild.de/video/clip/kino/kino-15715908.bild.html",'showVideos',"")
        addDir(translation(30004),"http://www.bild.de/video/clip/sport/sport-15717150.bild.html",'showVideos',"")
        addDir(translation(30005),"http://www.bild.de/video/clip/auto/auto-15711140.bild.html",'showVideos',"")
        addDir("Lifestyle","http://www.bild.de/video/clip/lifestyle/lifestyle-15716870.bild.html",'showVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def showVideos(url):
        if url.find("http://www.bild.de/video/clip/teaserreihe")==-1:
          content = getUrl(url)
          url=content[content.find("return paginator('")+18:]
          url=url[:url.find("'")]
          url="http://www.bild.de"+url
        content = getUrl(url)
        spl=content.split('<div class="hentry vt7')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<span class="value">(.+?)</span>', re.DOTALL).findall(entry)
            date=match[0].strip()
            date=date[:6]
            match=re.compile('<span class="kicker">(.+?)</span>', re.DOTALL).findall(entry)
            title=date+" "+match[0]
            title=cleanTitle(title)
            match=re.compile('<span class="headline">(.+?)</span>', re.DOTALL).findall(entry)
            if len(match)==1:
              title2=match[0].replace("<br />"," ").replace('<span class="st">',"")
              title2=cleanTitle(title2)
              title=title+" - "+title2
            title=title.replace("„","").replace("“","")
            match=re.compile('/video/(.+?)"', re.DOTALL).findall(entry)
            url="http://www.bild.de/video/"+match[0]
            url=url.replace(".bild.html",",view=xml.bild.xml")
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,url,'playVideo',thumb)
        if content.find('<div class="next">')>=0:
          content=content[content.find('<div class="next">'):]
          match=re.compile("return paginator\\('(.+?)',this\\)\" >weiter</a>", re.DOTALL).findall(content)
          url=match[0]
          match=re.compile("page=(.+?),", re.DOTALL).findall(url)
          addDir("Next Page ("+match[0]+")","http://www.bild.de"+url,'showVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
        content = getUrl(url)
        match=re.compile('<video src="(.+?)"', re.DOTALL).findall(content)
        listitem = xbmcgui.ListItem(path=match[0])
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

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

if mode == 'showVideos':
    showVideos(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
