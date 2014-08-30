#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(id='plugin.video.break_com')
translation = addon.getLocalizedString
forceViewMode=addon.getSetting("forceViewMode")
viewMode=str(addon.getSetting("viewMode"))

def index():
        addDir(translation(30001),"http://www.break.com/content/GetContentTimeStreamByChannelIdAndFilterBy?channelId=1&filterBy=videos&pageNum=1",'listChannelVideos',"")
        addDir(translation(30002),"http://www.break.com/content/GetContentByPageModuleAndPageTypeAndFilterBy?pageModuleTypeId=5&pageTypeId=4&filterBy=Daily&channelId=0&categoryId=0&numberOfContent=12",'listVideos',"")
        content = getUrl("http://www.break.com/channels/")
        content = content[content.find('class="channel-menu"'):]
        content = content[:content.find('</ul>'):]
        spl=content.split('<li class')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('src="(.+?)">(.+?)<', re.DOTALL).findall(entry)
            #thumb=match[0][0]
            title=match[0][1].strip()
            title=cleanTitle(title)
            if url!="http://www.break.com/action-unleashed/":
              addDir(title,url,'listChannel',"")
        addDir(translation(30004),"",'search',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listChannel(url):
        content = getUrl(url)
        match=re.compile("channelId           : (.+?),", re.DOTALL).findall(content)
        id=match[0]
        listChannelVideos("http://www.break.com/content/GetContentTimeStreamByChannelIdAndFilterBy?channelId="+id+"&filterBy=videos&pageNum=1")

def listChannelVideos(url):
        urlMain=url
        content = getUrl(url)
        match=re.compile('"MaxRecords":(.+?),', re.DOTALL).findall(content)
        max=int(match[0])
        spl=content.split('<article class=')
        for i in range(1,len(spl),1):
            entry=spl[i].replace("\\","")
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            id = url[url.rfind("-")+1:]
            if "/" in id:
                id = id[:id.find("/")]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            match=re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
            desc=match[0]
            desc=cleanTitle(desc)
            addLink(title,id,'playVideo',thumb,desc)
        page=int(urlMain[urlMain.find("&pageNum=")+9:])
        baseUrl=urlMain[:urlMain.find("&pageNum=")+9]
        if (page*10)<max:
          addDir(translation(30003)+" ("+str(page+1)+")",baseUrl+str(page+1),'listChannelVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<article class=')
        for i in range(1,len(spl),1):
            entry=spl[i].replace("\\","")
            if entry.find('] Video"')>0:
              match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
              url=match[0]
              id = url[url.rfind("-")+1:]
              if "/" in id:
                  id = id[:id.find("/")]
              match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
              thumb=match[0]
              match=re.compile('alt="\\[(.+?)\\]', re.DOTALL).findall(entry)
              title=match[0]
              title=cleanTitle(title)
              addLink(title,id,'playVideo',thumb,"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listSearchVideos(url):
        content = getUrl(url)
        contentNext = content[content.find('<div class="btm_cmore"'):]
        contentNext = contentNext[:contentNext.find('<script>')]
        matchPage=re.compile('<a href="(.+?)" title="(.+?)">(.+?)</a>', re.DOTALL).findall(contentNext)
        content = content[:content.find('<div class="btm_cmore"')]
        spl=content.split('<article class=')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('href="(.+?)">(.+?)<', re.DOTALL).findall(entry)
            url=match[0][0]
            title=cleanTitle(match[0][1])
            id = url[url.rfind("-")+1:]
            if "/" in id:
                id = id[:id.find("/")]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=""
            if len(match)>0:
              thumb=match[0]
            match=re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
            addLink(title,id,'playVideo',thumb,"")
        urlNext=""
        for url, title1, title2 in matchPage:
          if title2=="Next":
            urlNext=url
        if urlNext!="":
          addDir(translation(30003),urlNext,'listSearchVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(id):
          content = getUrl("http://www.break.com/embed/"+id)
          matchAuth=re.compile('"AuthToken": "(.+?)"', re.DOTALL).findall(content)
          matchURL=re.compile('"uri": "(.+?)".+?"height": (.+?),', re.DOTALL).findall(content)
          matchYT=re.compile('"youtubeId": "(.*?)"', re.DOTALL).findall(content)
          finalUrl=""
          if matchYT and matchYT[0]:
            if xbox==True:
              finalUrl = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + matchYT[0]
            else:
              finalUrl = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + matchYT[0]
          else:
              max=0
              for url, vidHeight in matchURL:
                  vidHeight=int(vidHeight)
                  if vidHeight>max:
                    finalUrl=url.replace(".wmv",".flv")+"?"+matchAuth[0]
                    max=vidHeight
          listitem = xbmcgui.ListItem(path=finalUrl)
          xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def search():
        keyboard = xbmc.Keyboard('', translation(30004))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","-")
          listSearchVideos('http://www.break.com/search/?q='+search_string)

def cleanTitle(title):
        return title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#038;","&").replace("&#39;","'").replace("&#039;","'").replace("&#8211;","-").replace("&#8220;","-").replace("&#8221;","-").replace("&#8217;","'").replace("&quot;","\"").strip()

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:23.0) Gecko/20100101 Firefox/23.0')
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

def addLink(name,url,mode,iconimage,desc):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
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

if mode == 'listChannelVideos':
    listChannelVideos(url)
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'listSearchVideos':
    listSearchVideos(url)
elif mode == 'listChannel':
    listChannel(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
else:
    index()
