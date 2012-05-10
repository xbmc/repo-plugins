#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,string,xbmcaddon

pluginhandle = int(sys.argv[1])

settings = xbmcaddon.Addon(id='plugin.video.chip_de')
translation = settings.getLocalizedString

def index():
        addDir(string.upper(translation(30001)),"http://www.chip.de/Video_17367032.html?tid1=30593&tid2=0&of=0",1,"")
        content=getUrl("http://www.chip.de/Video_17367032.html")
        content=content[content.find('<table width="468" border="0" cellspacing="0" cellpadding="0">'):]
        content=content[:content.find('</table><br><br>')]
        spl=content.split("<td><a href")
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('name="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            addDir(string.upper(title),url+"&of=0",1,thumb)
        xbmcplugin.endOfDirectory(pluginhandle)

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<div class="mi-beitragsliste-videos chipTeaser')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,url,2,"http://www.chip.de"+thumb)
        match=re.compile('</a>\n        \n    \n\n    \n\n\n\n    <a href="(.+?)"><span> &gt; </span></a>', re.DOTALL).findall(entry)
        if len(match)>0:
            url=match[0]
            addDir("Next Page",url,1,"")
        xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
        content = getUrl(url)
        match=re.compile('<a id="player" href="(.+?)"></a>', re.DOTALL).findall(content)
        url=match[0]
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

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
