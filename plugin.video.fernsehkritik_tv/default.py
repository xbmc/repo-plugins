#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcplugin
import xbmcgui
import sys
import urllib, urllib2
import re
import random

thisPlugin = int(sys.argv[1])

def index():
        addDir("TV-Magazin","http://fernsehkritik.tv/tv-magazin/komplett/",1,"")
        addDir("Pantoffelkino-TV","http://fernsehkritik.tv/pktv/",1,"")
        addDir("Extras: Alle Extras","http://fernsehkritik.tv/extras/",1,"")
        addDir("Extras: Aktuell im Gespräch","http://fernsehkritik.tv/extras/aktuell/",1,"")
        addDir("Extras: Schlechte Filme TV","http://fernsehkritik.tv/extras/sftv/",1,"")
        addDir("Extras: Pantoffelkino-TV Pannen","http://fernsehkritik.tv/extras/pktv/",1,"")
        xbmcplugin.endOfDirectory(thisPlugin)
        if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(50)')

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<div class="lclmo" id=')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
            url=match[0][0]
            title=match[0][1].replace("&quot;","")
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            thumb=thumb.replace("../","/")
            newUrl=""
            if url.find("/pktv/")==0:
              newUrl="http://fernsehkritik.tv"+url
            elif url.find("#extra-")==0:
              newUrl=url[7:]
            else:
              newUrl="http://fernsehkritik.tv"+url+"Start/"
            addLink(title,newUrl,2,"http://fernsehkritik.tv"+thumb)
        xbmcplugin.endOfDirectory(thisPlugin)
        if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(500)')

def playVideo(url):
        if url.find("http://")==0:
          content = getUrl(url)
          match=re.compile("var flattr_tle = '(.+?)'", re.DOTALL).findall(content)
          title=match[0]
          if content.find('playlist = [')>=0:
            content=content[content.find('playlist = ['):]
            content=content[:content.find('];')]
            match=re.compile("\\{ url:(.+?)'(.+?)' \\}", re.DOTALL).findall(content)
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            i=1
            for temp,filename in match:
              url="http://dl"+str(random.randint(1,3))+".fernsehkritik.tv/fernsehkritik"+filename
              listitem = xbmcgui.ListItem(title+" ("+str(i)+"/"+str(len(match))+")")
              i=i+1
              playlist.add(url,listitem)
            xbmc.executebuiltin('XBMC.Playlist.PlayOffset(-1)')
          else:
            match=re.compile("file=='(.+?)'", re.DOTALL).findall(content)
            filename=match[0]
            listitem = xbmcgui.ListItem(path="http://dl"+str(random.randint(1,3))+".fernsehkritik.tv/antik/"+filename)
            return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)
        else:
          content = getUrl("http://fernsehkritik.tv/swf/extras_cfg.php?id="+url)
          match=re.compile('"file":"(.+?)"', re.DOTALL).findall(content)
          file=match[0]
          listitem = xbmcgui.ListItem(path=file)
          return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)

def getUrl(url):
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
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
        listVideos(url)
elif mode==2:
        playVideo(url)
