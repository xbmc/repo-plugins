#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.howstuffworks_com')
translation = settings.getLocalizedString

forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))
autoPlay=int(settings.getSetting("autoPlay"))

def index():
        addDir(translation(30003), "", "search", "")
        listCategories("http://videos.howstuffworks.com/")

def listCategories(url):
        content = getUrl(url)
        spl=content.split('<td class="exploreCats"')
        if len(spl)>2:
          addDir(translation(30004),url,'listPlaylists',"")
          addDir(translation(30005),url,'listLatestVideos',"")
          if url!="http://videos.howstuffworks.com/":
            addDir(translation(30006)+" ("+translation(30007)+" 500)",url,'listVideos',"")
          for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('Category Explorer : (.+?)">(.+?)</a> (.+?)</td>', re.DOTALL).findall(entry)
            title=match[0][0]+" "+match[0][2]
            title=cleanTitle(title)
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            addDir(title,url,'listCategories',"")
        else:
          listVideos(url)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        content = getUrl("http://videos.howstuffworks.com/syndicate.php?f=rss&c=content&u="+urllib.quote_plus(url))
        spl=content.split('<item>')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<title>(.+?)</title>', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('<description>(.+?)</description>', re.DOTALL).findall(entry)
            desc=""
            if len(match)>0:
              desc=match[0]
              desc=cleanTitle(desc)
            match=re.compile('<link>http://videos.howstuffworks.com/(.+?)/(.+?)-(.+?)</link>', re.DOTALL).findall(entry)
            id=match[0][1]
            match=re.compile('url="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,id,'playVideo',thumb,desc)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listLatestVideos(url):
        content = getUrl(url)
        content = content[content.find('<div class="content recent">'):]
        content = content[:content.find('<div class="item-list browse-videos module">')]
        spl=content.split('<div class="item center">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('&nbsp;\\((.+?)\\)', re.DOTALL).findall(entry)
            length=match[0]
            match=re.compile('href="/(.+?)/(.+?)-(.+?)"', re.DOTALL).findall(entry)
            id=match[0][1]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,id,'playVideo',thumb,"",length)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listPlaylists(url):
        if url.find("/ajax/")==-1:
          content = getUrl(url)
          match=re.compile('contentId:"(.+?)"', re.DOTALL).findall(content)
          content = getUrl("http://videos.howstuffworks.com/ajax/top-playlists-videos?page=1&camcid="+match[0]+"&pageType=VideoCategory")
        else:
          content = getUrl(url)
        spl=content.split('<div class="item center">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('<br />\\((.+?)\\)</a>', re.DOTALL).findall(entry)
            vids=match[0]
            title=title+" ("+vids+")"
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addDir(title,url,'listPlaylist',thumb)
        if content.find('id="btnNextVideos"')>=0:
          content=content[content.find('<div class="rightVideoArrow">'):]
          match=re.compile("getTopPlaylists\\('(.+?)','(.+?)','(.+?)'\\)", re.DOTALL).findall(entry)
          page=match[0][0]
          id=match[0][1]
          type=match[0][2]
          url="http://videos.howstuffworks.com/ajax/top-playlists-videos?page="+page+"&camcid="+id+"&pageType="+type
          addDir(translation(30001)+" ("+page+")",url,'listPlaylists',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listPlaylist(url):
        content = getUrl(url)
        spl=content.split('<div class="line itemContainer"')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('class="bold">(.+?) \\((.+?)\\)</a>', re.DOTALL).findall(entry)
            title=match[0][0]
            length=match[0][1]
            title=cleanTitle(title)
            match=re.compile('short_description="(.+?)"', re.DOTALL).findall(entry)
            desc=match[0]
            desc=cleanTitle(desc)
            match=re.compile('video_id="(.+?)"', re.DOTALL).findall(entry)
            id=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,id,'playVideo',thumb,desc,length)
        match=re.compile('<div id="next-page-video" title="(.+?)" url="(.+?)"', re.DOTALL).findall(entry)
        if len(match)>0:
          addDir(translation(30001),match[0][1],'listPlaylist',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', translation(30003))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listSearch('http://videos.howstuffworks.com/search.php?media=video&terms='+search_string)

def listSearch(url):
        results=[]
        content = getUrl(url)
        spl=content.split('<div class="item video">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('<h4>Time: (.+?)</h4>', re.DOTALL).findall(entry)
            length=match[0]
            match=re.compile('<td colspan="2">(.+?)</td>', re.DOTALL).findall(entry)
            desc=match[0]
            match=re.compile('href="http://videos.howstuffworks.com/(.+?)/(.+?)-(.+?)"', re.DOTALL).findall(entry)
            id=match[0][1]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            if id not in results:
              results.append(id)
              addLink(title,id,'playVideo',thumb,desc,length)
        if content.find('<div class="more-results">')>0:
          content=content[content.find('<div class="more-results">'):]
          content=content[:content.find('</div>')]
          spl=content.split("<a href=")
          for i in range(1,len(spl),1):
            entry=spl[i]
            if entry.find('<span class="uppercase">next</span>')>0:
              match=re.compile('"(.+?)"', re.DOTALL).findall(entry)
              addDir(translation(30002),match[0].replace("&amp;","&"),'listSearch',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(id):
        content = getUrl("http://static.discoverymedia.com/videos/components/hsw/"+id+"-title/smil-service.smil")
        match=re.compile('<meta name="httpBase" content="(.+?)"', re.DOTALL).findall(content)
        base=match[0]
        maxBitrate=0
        match=re.compile('<video src="(.+?)" system-bitrate="(.+?)"/>', re.DOTALL).findall(content)
        for urlTemp, bitrateTemp in match:
          bitrate=int(bitrateTemp)
          if bitrate>maxBitrate:
            maxBitrate=bitrate
            url=urlTemp
        url=base+"/"+url+"?v=2.6.8&fp=&r=&g="
        listitem = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        if autoPlay>0:
          xbmc.sleep(autoPlay*1000)
          if xbmc.Player().isPlaying()==True and int(xbmc.Player().getTime())==0:
            xbmc.Player().pause()

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/13.0')
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

def addLink(name,url,mode,iconimage,desc,length=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc, "Duration": length } )
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
elif mode == 'listCategories':
    listCategories(url)
elif mode == 'listPlaylists':
    listPlaylists(url)
elif mode == 'listPlaylist':
    listPlaylist(url)
elif mode == 'listLatestVideos':
    listLatestVideos(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
elif mode == 'listSearch':
    listSearch(url)
else:
    index()
