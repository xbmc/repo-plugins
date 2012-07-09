#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,httplib,socket
from pyamf import remoting

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
settings = xbmcaddon.Addon(id='plugin.video.redbull_tv')
translation = settings.getLocalizedString

maxVideoQuality=settings.getSetting("maxVideoQuality")
forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))

qual=[1080,720,540,360]
maxVideoQuality=qual[int(maxVideoQuality)]

def index():
        addDir(translation(30002),"http://www.redbull.tv/Redbulltv",'latestVideos',"")
        addDir(translation(30003),"http://www.redbull.tv/cs/Satellite?_=1341624385783&pagename=RBWebTV%2FRBTV_P%2FRBWTVShowContainer&orderby=latest&p=%3C%25%3Dics.GetVar(%22p%22)%25%3E&start=1",'listShows',"")
        addDir(translation(30004),"",'search',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def latestVideos(url):
        content = getUrl(url)
        content = content[content.find('<h3>LATEST EPISODES</h3>'):]
        content = content[:content.find('</ul>')]
        spl=content.split('<li')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<span class="date">(.+?)</span>', re.DOTALL).findall(entry)
            date=match[0]
            match=re.compile('<span class="season">(.+?)</span>', re.DOTALL).findall(entry)
            subTitle=match[0]
            match=re.compile('<span class="title">(.+?)</span>', re.DOTALL).findall(entry)
            title=date+" - "+match[0]+" - "+subTitle
            title=cleanTitle(title)
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url="http://www.redbull.tv"+match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb="http://www.redbull.tv"+match[0].replace(" ","%20")
            addLink(title,url,'playVideo',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listShows(url):
        urlMain = url
        content = getUrl(url)
        matchPage=re.compile('<a class="next_page" rel="next" href="(.+?)">', re.DOTALL).findall(content)
        content = content[content.find('<div class="carousel-container"'):]
        spl=content.split('<div data-id=')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<span class="episode-count">(.+?)</span>', re.DOTALL).findall(entry)
            subTitle=match[0]
            match=re.compile('<span class="title">(.+?)</span>', re.DOTALL).findall(entry)
            title=match[0].strip()+" ("+subTitle.strip().replace("[","").replace("]","").replace(" episodes","")+")"
            title=cleanTitle(title)
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url="http://www.redbull.tv"+match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb="http://www.redbull.tv"+match[0].replace(" ","%20")
            addDir(title,url,'listVideos',thumb)
        if urlMain=="http://www.redbull.tv/cs/Satellite?_=1341624385783&pagename=RBWebTV%2FRBTV_P%2FRBWTVShowContainer&orderby=latest&p=%3C%25%3Dics.GetVar(%22p%22)%25%3E&start=1":
          addDir(translation(30001),"http://www.redbull.tv/cs/Satellite?_=1341624260257&pagename=RBWebTV%2FRBTV_P%2FRBWTVShowContainer&orderby=latest&p=%3C%25%3Dics.GetVar(%22p%22)%25%3E&start=17",'listShows',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        content = getUrl(url)
        spl=content.split('<div id="season-')
        for i in range(1,len(spl),1):
          entry=spl[i]
          season=entry[:entry.find('"')]
          if len(season)==1:
            season="0"+season
          entry=entry[entry.find('<tbody>'):]
          entry=entry[:entry.find('</tbody>')]
          spl2=entry.split('<tr')
          for i in range(1,len(spl2),1):
            entry2=spl2[i]
            match=re.compile('<td><a href="(.+?)">(.+?)</a></td>', re.DOTALL).findall(entry2)
            url="http://www.redbull.tv"+match[0][0]
            episode=match[0][1]
            if len(episode)==1:
              episode="0"+episode
            title=match[1][1]
            length=match[2][1]
            if length.find("</a>")==-1:
              length = " ("+length+")"
            else:
              length = ""
            addLink("S"+season+"E"+episode+" - "+title+length,url,'playVideo',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', translation(30004))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          content = getUrl('http://www.redbull.tv/cs/Satellite?_=1341632208902&pagename=RBWebTV%2FRBWTVSearchResult&q='+search_string)
          if content.find("<!-- Episodes -->")>=0:
            content = content[content.find('<!-- Episodes -->'):]
            spl=content.split('<div class="results-item">')
            for i in range(1,len(spl),1):
                entry=spl[i]
                match=re.compile('<span style="font-weight: bold;">(.+?)</span><br/>', re.DOTALL).findall(entry)
                title=match[0]
                title=cleanTitle(title)
                match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
                url="http://www.redbull.tv"+match[0]
                addLink(title,url,'playVideo',"")
          xbmcplugin.endOfDirectory(pluginhandle)
          if forceViewMode==True:
            xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        content = getUrl(url)
        match=re.compile("episode_video_id = '(.+?)'", re.DOTALL).findall(content)
        playBrightCoveStream(match[0])

def playBrightCoveStream(bc_videoID):
        bc_playerID = 761157706001
        bc_publisherID = 710858724001
        bc_const = "cf760beae3fbdde270b76f2109537e13144e6fbd"
        conn = httplib.HTTPConnection("c.brightcove.com")
        envelope = remoting.Envelope(amfVersion=3)
        envelope.bodies.append(("/1", remoting.Request(target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById", body=[bc_const, bc_playerID, bc_videoID, bc_publisherID], envelope=envelope)))
        conn.request("POST", "/services/messagebroker/amf?playerId=" + str(bc_playerID), str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
        response = conn.getresponse().read()
        response = remoting.decode(response).bodies[0][1].body
        streamUrl = ""
        maxEncodingRate = 0
        for item in sorted(response['renditions'], key=lambda item:item['frameHeight'], reverse=False):
          streamHeight = item['frameHeight']
          encRate = item['encodingRate']
          if streamHeight <= maxVideoQuality:
            if encRate > maxEncodingRate:
              maxEncodingRate = encRate
              streamUrl = item['defaultURL']
        rtmp = streamUrl[0:streamUrl.find("&")]
        playpath = streamUrl[streamUrl.find("&")+1:]
        listItem = xbmcgui.ListItem(path=rtmp+' playpath='+playpath)
        xbmcplugin.setResolvedUrl(pluginhandle,True,listItem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/13.0')
        if xbox==True:
          socket.setdefaulttimeout(30)
          response = urllib2.urlopen(req)
        else:
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

if mode == 'listVideos':
    listVideos(url)
elif mode == 'latestVideos':
    latestVideos(url)
elif mode == 'listShows':
    listShows(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
else:
    index()
