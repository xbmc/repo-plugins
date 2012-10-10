#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(id='plugin.video.redux_com')
translation = addon.getLocalizedString

forceViewMode=addon.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(addon.getSetting("viewMode"))

def index():
        content = getUrl("http://redux.com/hg.shellinit")
        content = content[content.find('name=\\"mine\\"')+1:]
        spl=content.split("name=")
        for i in range(1,len(spl),1):
            entry=spl[i]
            id = entry[entry.find('\\"')+2:]
            id = id[:id.find('\\"')]
            title = entry[entry.find('>\\n')+3:]
            title = title[:title.find('\\n')]
            title=cleanTitle(title)
            addDir(title,id,"listChannels","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listChannels(type):
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        content = getUrl("http://redux.com/hg.shellinit")
        content = content[content.find('"'+type+'":'):]
        content = content[:content.find('</div>\\n</div>\\n\\n",')]
        spl=content.split("<div class='chan'")
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile("<div class='title'>(.+?)</div>", re.DOTALL).findall(entry)
            match2=re.compile("<div class=&#39;title&#39;>(.+?)</div>", re.DOTALL).findall(entry)
            if len(match)>0:
              title=match[0]
            elif len(match2)>0:
              title=match2[0]
            title=cleanTitle(title)
            id = entry[entry.find('chid=\\"')+7:]
            id = id[:id.find('\\"')]
            match=re.compile("preload='(.+?)'", re.DOTALL).findall(entry)
            thumb=match[0]
            addDir(title,id,'listVideos',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(id):
        urlMain=url
        content = getUrl("http://redux.com/hg.channelinfo/"+id)
        spl=content.split('"pid":')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('"title":"(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('"type":"(.+?)"', re.DOTALL).findall(entry)
            type=match[0]
            match=re.compile('"id":"(.+?)"', re.DOTALL).findall(entry)
            id=match[0]
            match=re.compile('</span>(.+?)<span class=', re.DOTALL).findall(entry)
            desc=""
            if len(match)>0:
              desc=match[0]
            match=re.compile('"duration":(.+?),', re.DOTALL).findall(entry)
            try:
              min=int(int(match[0])/60)
              sec=int(int(match[0])%60)
              duration=str(min)+":"+str(sec)
            except:
              duration=""
            match=re.compile('"imagebase":"(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]+"strip203x150"
            if type=="youtube":
              addLink(title,id,'playYoutube',thumb,desc,duration)
            elif type=="vimeo":
              addLink(title,id,'playVimeo',thumb,desc,duration)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playYoutube(id):
        if xbox==True:
          url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
        else:
          url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def playVimeo(id):
        if xbox==True:
          url = "plugin://video/Vimeo/?path=/root/video&action=play_video&videoid=" + id
        else:
          url = "plugin://plugin.video.vimeo/?path=/root/video&action=play_video&videoid=" + id
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0')
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
elif mode == 'listChannels':
    listChannels(url)
elif mode == 'playYoutube':
    playYoutube(url)
elif mode == 'playVimeo':
    playVimeo(url)
else:
    index()
