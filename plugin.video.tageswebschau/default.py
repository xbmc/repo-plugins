#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmc,xbmcgui,xbmcaddon,xbmcplugin

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.tageswebschau')
translation = settings.getLocalizedString

def index():
        content = getUrl("http://www.radiobremen.de/extranet/tws/json/tws_toc.json?_=1338860844174")
        spl=content.split('{\n  	"titel" : ')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('"(.+?)"', re.DOTALL).findall(entry)
          title=match[0]
          title=cleanTitle(title)
          match=re.compile('"img" : "(.+?)"', re.DOTALL).findall(entry)
          thumb=match[0]
          title=cleanTitle(title)
          match=re.compile('"jsonurl" : "(.+?)"', re.DOTALL).findall(entry)
          url="http://www.radiobremen.de"+match[0]
          addLink(title,url,'playVideo',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
        content = getUrl(url)
        match=re.compile('"url" : "http://(.+?)_L.mp4"', re.DOTALL).findall(content)
        url="http://"+match[0]+"_L.mp4"
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        return title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").strip()

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
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

def addLink(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'playVideo':
    playVideo(url)
else:
    index()
