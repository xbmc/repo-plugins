#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])

settings = xbmcaddon.Addon(id='plugin.video.mtv_de')
translation = settings.getLocalizedString

def index():
        addDir(translation(30007),"http://www.mtv.de/musikvideos",'listVideosLatest',"")
        addDir(translation(30001),"http://www.mtv.de/charts/5-hitlist-germany-top-100",'listVideos',"")
        addDir(translation(30002),"http://www.mtv.de/charts/7-deutsche-black-charts",'listVideos',"")
        addDir(translation(30003),"http://www.mtv.de/charts/6-dance-charts",'listVideos',"")
        addDir(translation(30004),"http://www.mtv.de/musikvideos/11-mtv-de-videocharts/playlist",'listVideos',"")
        addDir(translation(30005),"SEARCH_ARTIST",'search',"")
        addDir(translation(30006),"SEARCH_SPECIAL",'search',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(50)')

def listVideos(url):
        content = getUrl(url)
        content = content[content.find("<div class='current_season'>"):]
        content = content[:content.find("</ul>")]
        spl=content.split('<li')
        for i in range(1,len(spl),1):
            entry=spl[i]
            if entry.find("class='no_video'")==-1 and entry.find("class='active no_video'")==-1:
              match=re.compile("data-uma-token='(.+?)'", re.DOTALL).findall(entry)
              url=match[0]
              match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
              thumb=match[0]
              match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
              title=match[0]
              match=re.compile("<span class='chart_position'>(.+?)</span>", re.DOTALL).findall(entry)
              if len(match)==1:
                title=match[0]+". "+title
              addLink(title,url,'playVideo',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(500)')

def listVideosLatest(url):
        content = getUrl(url)
        match=re.compile('<li class=\'teaser_music_video\'>\n<a href="(.+?)" rel="general" title="(.+?)"><img alt="(.+?)" height="80" src="(.+?)"', re.DOTALL).findall(content)
        for url,title1,title2,thumb in match:
          addLink(title1,"http://www.mtv.de"+url,'playVideo',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(500)')

def playVideo(url):
        if url.find("http://")==0:
          content = getUrl(url)
          match=re.compile('music_video-(.+?)-DE', re.DOTALL).findall(content)
          url=match[0]
        content = getUrl("http://api.mtvnn.com/v2/mrss.xml?uri=mgid:sensei:video:mtvnn.com:music_video-"+url+"-DE")
        match=re.compile("<media:content duration='0' isDefault='true' type='text/xml' url='(.+?)'></media:content>", re.DOTALL).findall(content)
        content = getUrl(match[0])
        
        if content.find("<src>/www/custom/intl/errorslates/video_error.flv</src>")>=0:
          xbmc.executebuiltin('XBMC.Notification(Error!,Video is not available...,5000)')
        else:
          match1=re.compile('type="video/mp4" bitrate="1700">\n<src>(.+?)</src>', re.DOTALL).findall(content)
          match2=re.compile('type="video/mp4" bitrate="1200">\n<src>(.+?)</src>', re.DOTALL).findall(content)
          match3=re.compile('type="video/x-flv" bitrate="800">\n<src>(.+?)</src>', re.DOTALL).findall(content)
          match4=re.compile('type="video/mp4" bitrate="750">\n<src>(.+?)</src>', re.DOTALL).findall(content)
          match5=re.compile('type="video/x-flv" bitrate="600">\n<src>(.+?)</src>', re.DOTALL).findall(content)
          match6=re.compile('type="video/mp4" bitrate="400">\n<src>(.+?)</src>', re.DOTALL).findall(content)
          match7=re.compile('type="video/x-flv" bitrate="250">\n<src>(.+?)</src>', re.DOTALL).findall(content)
          url=""
          if len(match1)==1:
            url=match1[0]
          elif len(match2)==1:
            url=match2[0]
          elif len(match3)==1:
            url=match3[0]
          elif len(match4)==1:
            url=match4[0]
          elif len(match5)==1:
            url=match5[0]
          elif len(match6)==1:
            url=match6[0]
          elif len(match7)==1:
            url=match7[0]
          listitem = xbmcgui.ListItem(path=url+" swfVfy=1 swfUrl=http://media.mtvnservices.com/player/prime/mediaplayerprime.1.9.1.swf")
          return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def search(SEARCHTYPE):
        keyboard = xbmc.Keyboard('', 'Video Suche')
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          url="http://www.mtv.de/search?query="+search_string+"&ajax=1"
          content = getUrlSearch(url)
          if SEARCHTYPE=="SEARCH_ARTIST":
            if content.find("<h2>Artists</h2>")>=0:
              content=content[content.find("<h2>Artists</h2>"):]
              content=content[:content.find("</ul>")]
              spl=content.split('<li>')
              for i in range(1,len(spl),1):
                  entry=spl[i]
                  match=re.compile('<a href="(.+?)"', re.DOTALL).findall(entry)
                  url=match[0]
                  match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
                  thumb=match[0]
                  match=re.compile('<h3>(.+?)</h3>', re.DOTALL).findall(entry)
                  title=match[0].replace("&amp;","&")
                  addDir(title,"http://www.mtv.de"+url,'listVideos',thumb)
              xbmcplugin.endOfDirectory(pluginhandle)
              if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(500)')
          elif SEARCHTYPE=="SEARCH_SPECIAL":
            if content.find("<h2>Videos</h2>")>=0:
              content=content[content.find("<h2>Videos</h2>"):]
              content=content[:content.find("</ul>")]
              spl=content.split('<li>')
              for i in range(1,len(spl),1):
                  entry=spl[i]
                  match=re.compile('<a href="(.+?)"', re.DOTALL).findall(entry)
                  url=match[0]
                  match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
                  thumb=match[0]
                  match=re.compile('<h3>(.+?)</h3>', re.DOTALL).findall(entry)
                  title1=match[0].replace("&amp;","&")
                  match=re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
                  title=match[0]+" - "+title1
                  addLink(title,"http://www.mtv.de"+url,'playVideo',thumb)
              xbmcplugin.endOfDirectory(pluginhandle)
              if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(500)')

def getUrlSearch(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
        req.add_header('X-Requested-With', 'XMLHttpRequest')
        req.add_header('Referer', 'http://www.mtv.de/charts')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link

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
elif mode == 'listVideosLatest':
    listVideosLatest(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search(url)
else:
    index()
