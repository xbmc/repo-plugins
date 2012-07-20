#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,httplib,socket,time
from pyamf import remoting

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
settings = xbmcaddon.Addon(id='plugin.video.wired_com')
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
        addDir("Latest","http://www.wired.com/video/",'listVideos',"")
        content = getUrl("http://www.wired.com/video/")
        content = content[content.find("<li class='bc_topics bc_otherChannels'>"):]
        content = content[:content.find("</div>")]
        match=re.compile('<li><a href="(.+?)">(.+?)</a></li>', re.DOTALL).findall(content)
        for url,title in match:
          if title!="Nebula":
            addDir(title,url,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        ids=[]
        urlMain = url
        content = getUrl(url)
        spl=content.split('<div class="lineupThumb">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile("_popDesc_1' class='bc_popDesc'>(.+?)</div>", re.DOTALL).findall(entry)
            desc=""
            if len(match)>0:
              desc=match[0]
              desc=cleanTitle(desc)
            match=re.compile("alt='(.+?)'", re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile("<div id='bc_(.+?)_", re.DOTALL).findall(entry)
            id=match[0]
            match=re.compile("_thumbUrl_1' class='bc_popDesc'>(.+?)</div>", re.DOTALL).findall(entry)
            thumb=""
            if len(match)>0:
              thumb=match[0]
            if not id in ids:
              ids.append(id)
              addLink(title,id,'playBrightCoveStream',thumb,desc)
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

def playBrightCoveStream(bc_videoID):
        bc_playerID = 1716442119
        bc_publisherID = 1564549380
        bc_const = "70e339d95edc21381e28c3d5f182e9b653c2a35e"
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
        if streamUrl=="":
          streamUrl=response['FLVFullLengthURL']
        if streamUrl!="":
          url = streamUrl[0:streamUrl.find("&")]
          playpath = streamUrl[streamUrl.find("&")+1:]
          listItem = xbmcgui.ListItem(path=url+' playpath='+playpath)
          xbmcplugin.setResolvedUrl(pluginhandle,True,listItem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
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

def addLink(name,url,mode,iconimage,desc):
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
elif mode == 'playBrightCoveStream':
    playBrightCoveStream(url)
elif mode == 'search':
    search()
else:
    index()
