#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.video.atv_at')
translation = addon.getLocalizedString
forceViewMode=addon.getSetting("forceViewMode")
viewMode=str(addon.getSetting("viewMode"))

def index():
        content = getUrl("http://atv.at/mediathek")
        spl=content.split('<li data-time=')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
          title=match[0]
          title=cleanTitle(title)
          match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
          url="http://atv.at"+match[0]
          match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
          thumb=match[0]
          addDir(title,url,'listVideos',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        if url.find("http://atv.at/contentset/")==0:
          content = getUrl(url)
          match=re.compile('contentset_id%22%3A(.+?)%', re.DOTALL).findall(content)
          id1=match[0]
          match=re.compile('active_playlist_id%22%3A(.+?)%', re.DOTALL).findall(content)
          id2=match[0]
          url="http://atv.at/player_playlist_page_json/"+id1+"/"+id2+"/1"
        content = getUrl(url)
        match=re.compile('"(.+?)":', re.DOTALL).findall(content)
        currentPage=int(match[0])
        match=re.compile('"total_page_count":(.+?)}', re.DOTALL).findall(content)
        maxPage=int(match[0])
        spl=content.split('"title"')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('"(.+?)","subtitle":"(.+?)"', re.DOTALL).findall(entry)
          if match[0][1].find('",')==0:
            title=match[0][0]
          else:
            title=match[0][0]+" - "+match[0][1]
          title=cleanTitle(title)
          match=re.compile('"image_url":"(.+?)"', re.DOTALL).findall(entry)
          thumb=match[0].replace("\\","")
          addLink(title,entry,'playVideo',thumb)
        if currentPage<maxPage:
          addDir(translation(30001)+" ("+str(currentPage+1)+")",url[:len(url)-1]+str(currentPage+1),'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(entry):
        if '"geoblocked":true' not in entry:
          entry = entry[entry.find("contentset_id"):]
          matchUrls=re.compile('"url":"(.+?)"', re.DOTALL).findall(entry)
          if len(matchUrls)>1:
            urlFull="stack://"
            for url in matchUrls:
              urlFull+=url.replace("\\","")+" , "
            urlFull=urlFull[:-3]
            listitem = xbmcgui.ListItem(path=urlFull)
            return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
          elif len(matchUrls)==1:
            urlFull=matchUrls[0].replace("\\","")
            listitem = xbmcgui.ListItem(path=urlFull)
            return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        else:
          xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30002))+',5000)')

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.replace("\\u00c4","Ä").replace("\\u00e4","ä").replace("\\u00d6","Ö").replace("\\u00f6","ö").replace("\\u00dc","Ü").replace("\\u00fc","ü").replace("\\u00df","ß")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:18.0) Gecko/20100101 Firefox/18.0')
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
else:
    index()
