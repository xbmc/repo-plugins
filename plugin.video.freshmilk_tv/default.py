#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,httplib,socket
from pyamf import remoting

pluginhandle = int(sys.argv[1])
addonID='plugin.video.freshmilk_tv'
xbox = xbmc.getCondVisibility("System.Platform.xbox")
settings = xbmcaddon.Addon(addonID)
fmLogo=xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
bimLogo=xbmc.translatePath('special://home/addons/'+addonID+'/bim.png')
fdLogo=xbmc.translatePath('special://home/addons/'+addonID+'/fd.png')
translation = settings.getLocalizedString

maxBitRate=settings.getSetting("maxBitRate")
forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))

qual=[512000,1024000,2048000,3072000,4096000,5120000]
maxBitRate=qual[int(maxBitRate)]

def index():
        addDir("FreshMilk.tv","http://www.freshmilk.tv/",'listChannels',fmLogo)
        addDir("BerlinIsMusic.tv","http://www.berlinismusic.tv/",'listChannelsBIM',bimLogo)
        addDir("FashionDaily.tv","http://www.fashiondaily.tv/",'listChannels',fdLogo)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listChannels(url):
        urlMain=url
        content = getUrl(url)
        spl=content.split('<option value=')
        addDir(translation(30002),urlMain+"player/ajax/videos/20/1/?navtype=allnav",'listVideos',"")
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('"(.+?)"', re.DOTALL).findall(entry)
            if len(match)>0:
              id=match[0]
              url=urlMain+"player/ajax/videos/"+id+"/20/1/?navtype=allnav"
              match=re.compile('>(.+?)<', re.DOTALL).findall(entry)
              title=match[0]
              title=cleanTitle(title)
              thumb=""
              if title=="Summer of Festivals":
                thumb="http://www.freshmilk.tv/media/logobranding/summer-festivals-logo.png"
              elif title=="Unplugged":
                thumb="http://www.freshmilk.tv/media/logobranding/unplugged-logo.png"
              elif title=="Playlist":
                thumb="http://www.freshmilk.tv/media/logobranding/playlist-logo.png"
              elif title=="Interview":
                thumb="http://www.freshmilk.tv/media/logobranding/people-and-portrait-logo.png"
              elif title=="Schneller Teller":
                thumb="http://www.freshmilk.tv/media/logobranding/schneller-teller-logo.png"
              elif title=="Elevator Talk":
                thumb="http://www.freshmilk.tv/media/logobranding/elevator-talk-logo.png"
              elif title=="Plugged":
                thumb="http://www.freshmilk.tv/media/logobranding/plugged-logo.png"
              elif title=="Art Leisure":
                thumb="http://www.freshmilk.tv/media/logobranding/art-and-leisure-logo.png"
              elif title=="Bombs":
                thumb="http://www.freshmilk.tv/media/logobranding/bombs-logo.png"
              elif title=="Art Tramp":
                thumb="http://www.freshmilk.tv/media/logobranding/fmtv-art-tramp-logo.png"
              elif title=="Sports and Streets":
                thumb="http://www.freshmilk.tv/media/logobranding/sports-and-streets-logo.png"
              elif title=="Achtung Berlin":
                thumb="http://www.freshmilk.tv/media/logobranding/achtung-berlin-logo.png"
              elif title=="Music & Festival":
                thumb="http://www.freshmilk.tv/media/logobranding/musik-and-festival-logo.png"
              elif title=="Berlin Fashion Week SS 2013":
                thumb="http://www.fashiondaily.tv/media/logobranding/berlin-fashion-week-ss-2013-logo.png"
              elif title=="Paris Fashion Week":
                thumb="http://www.fashiondaily.tv/media/logobranding/paris-fashion-week-logo.png"
              elif title=="Reportage":
                thumb="http://www.fashiondaily.tv/media/logobranding/reportage-logo.png"
              elif title=="Accessoire Special":
                thumb="http://www.fashiondaily.tv/media/logobranding/accessoire-special-logo.png"
              elif title=="Coverstar":
                thumb="http://www.fashiondaily.tv/media/logobranding/coverstar-logo.png"
              elif title=="Fashion Film":
                thumb="http://www.fashiondaily.tv/media/logobranding/fashion-film-logo.png"
              elif title=="Festival de Cannes":
                thumb="http://www.fashiondaily.tv/media/logobranding/festival-de-cannes-logo.png"
              elif title=="Look at Me":
                thumb="http://www.fashiondaily.tv/media/logobranding/look-me-logo.png"
              elif title=="Modemacher im Gespräch":
                thumb="http://www.fashiondaily.tv/media/logobranding/interview-logo.png"
              elif title=="Shop of the Week":
                thumb="http://www.fashiondaily.tv/media/logobranding/shop-week-logo.png"
              elif title=="Streetstyles":
                thumb="http://www.fashiondaily.tv/media/logobranding/streetstyles-logo.png"
              elif title=="Judgement Day":
                thumb="http://www.fashiondaily.tv/media/logobranding/judgementday-logo.png"
              elif title=="Fashion Shows":
                thumb="http://www.fashiondaily.tv/media/logobranding/fashionshows-logo.png"
              elif title=="Fashion Events":
                thumb="http://www.fashiondaily.tv/media/logobranding/fashion-events-logo.png"
              addDir(title,url,'listVideos',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listChannelsBIM(url):
        urlMain=url
        content = getUrl(url)
        spl=content.split('<option value=')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('"(.+?)"', re.DOTALL).findall(entry)
            if len(match)>0:
              url="http://www.berlinismusic.tv"+match[0]
              match=re.compile('>(.+?)<', re.DOTALL).findall(entry)
              title=match[0]
              title=cleanTitle(title)
              thumb=""
              if title=="Locations":
                thumb="http://www.berlinismusic.tv/media/uploads/locations.jpg"
              elif title=="Music Videos":
                thumb="http://www.berlinismusic.tv/media/uploads/musicvideos.jpg"
              elif title=="People&Interviews":
                thumb="http://www.berlinismusic.tv/media/uploads/people.jpg"
              elif title=="Plugged:::":
                thumb="http://www.berlinismusic.tv/media/uploads/plugged.jpg"
              elif title=="un:plugged":
                thumb="http://www.berlinismusic.tv/media/uploads/nav_unplugged.png"
              elif title=="unterwegs mit":
                thumb="http://www.berlinismusic.tv/media/uploads/unterwegs.jpg"
              if title!="Startseite":
                addDir(title,url,'listVideosBIM',thumb)
        addDir("news:show","http://www.berlinismusic.tv/channel/newsshow/",'listVideos',"http://www.berlinismusic.tv/media/uploads/news.jpg")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        urlMain=url[:url.find("/player/")]
        content = getUrl(url)
        match=re.compile('/20/(.+?)/', re.DOTALL).findall(url)
        currentPage=int(match[0])
        if url.find(urlMain+"/player/ajax/videos/20/")==0:
          nextUrl=urlMain+"/player/ajax/videos/20/"+str(currentPage+1)+"/?navtype=allnav"
        else:
          match=re.compile(urlMain+'/player/ajax/videos/(.+?)/20/', re.DOTALL).findall(url)
          id=match[0]
          nextUrl=urlMain+"/player/ajax/videos/"+id+"/20/"+str(currentPage+1)+"/?navtype=allnav"
        match=re.compile('allnav.num_pages = (.+?);', re.DOTALL).findall(content)
        maxPage=int(match[0])
        spl=content.split('<li>')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('id="vl(.+?)"', re.DOTALL).findall(entry)
            id=match[0]
            match=re.compile('<span class="length">(.+?)</span>', re.DOTALL).findall(entry)
            length=match[0]
            match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            title=title+" ("+length+" min)"
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,id,'playBrightCoveStream',thumb)
        if currentPage<maxPage:
          addDir(translation(30001),nextUrl,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideosBIM(url):
        urlMain = url
        content = getUrl(url)
        spl=content.split('<div class="video "')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url="http://www.berlinismusic.tv"+match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,url,'playBIMVideo',thumb)
        match=re.compile('<a class="next" href="(.+?)">', re.DOTALL).findall(content)
        if len(match)>0:
          addDir(translation(30001),match[0],'listVideosBIM',"")
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

def playBIMVideo(url):
        content = getUrl(url)
        match=re.compile('<a id="player" href="(.+?)"', re.DOTALL).findall(content)
        listItem = xbmcgui.ListItem(path=match[0])
        xbmcplugin.setResolvedUrl(pluginhandle,True,listItem)

def playBrightCoveStream(bc_videoID):
        bc_playerID = 1277164692001
        bc_publisherID = 1113255272001
        bc_const = "f079ea2204e0e0bd5fe43221b533e35790610514"
        conn = httplib.HTTPConnection("c.brightcove.com")
        envelope = remoting.Envelope(amfVersion=3)
        envelope.bodies.append(("/1", remoting.Request(target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById", body=[bc_const, bc_playerID, bc_videoID, bc_publisherID], envelope=envelope)))
        conn.request("POST", "/services/messagebroker/amf?playerId=" + str(bc_playerID), str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
        response = conn.getresponse().read()
        response = remoting.decode(response).bodies[0][1].body
        streamUrl = ""
        for item in sorted(response['renditions'], key=lambda item:item['encodingRate'], reverse=False):
          encRate = item['encodingRate']
          if encRate < maxBitRate:
            streamUrl = item['defaultURL']
        if streamUrl.find("http://")==0:
          listItem = xbmcgui.ListItem(path=streamUrl)
        else:
          url = streamUrl[0:streamUrl.find("&")]
          playpath = streamUrl[streamUrl.find("&")+1:]
          listItem = xbmcgui.ListItem(path=url+' playpath='+playpath)
        xbmcplugin.setResolvedUrl(pluginhandle,True,listItem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#39;","\\").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
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

def addLink(name,url,mode,iconimage,desc=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name , "Plot": desc } )
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
elif mode == 'listShows':
    listShows(url)
elif mode == 'listChannels':
    listChannels(url)
elif mode == 'listChannelsBIM':
    listChannelsBIM(url)
elif mode == 'listVideosBIM':
    listVideosBIM(url)
elif mode == 'playBIMVideo':
    playBIMVideo(url)
elif mode == 'search':
    search()
elif mode == 'playBrightCoveStream':
    playBrightCoveStream(url)
else:
    index()
