#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.video.zdf_de_lite')
translation = addon.getLocalizedString

forceViewMode=addon.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(addon.getSetting("viewMode"))

def index():
        addDir("ZDF","zdf",'listChannel',"http://www.zdf.de/ZDFmediathek/contentblob/1209114/tImg/4009328")
        addDir("ZDFneo","zdfneo",'listChannel',"http://www.zdf.de/ZDFmediathek/contentblob/1209122/tImg/5939058")
        addDir("ZDFkultur","zdfkultur",'listChannel',"http://www.zdf.de/ZDFmediathek/contentblob/1317640/tImg/5960283")
        addDir("ZDFinfo","zdfinfo",'listChannel',"http://www.zdf.de/ZDFmediathek/contentblob/1209120/tImg/5880352")
        addDir("3sat","dreisat",'listChannel',"http://www.zdf.de/ZDFmediathek/contentblob/1209116/tImg/5784929")
        addDir("LIVE","http://www.zdf.de/ZDFmediathek/hauptnavigation/live/day0",'listVideos',"")
        addDir(str(translation(30001))+": A-Z","",'listAZ',"")
        addDir(str(translation(30001))+": Thema","http://www.zdf.de/ZDFmediathek/hauptnavigation/themen",'listThemen',"")
        addDir(str(translation(30001))+": "+str(translation(30002)),"",'search',"")
        addDir(translation(30003),"http://www.zdf.de/ZDFmediathek/hauptnavigation/nachrichten/ganze-sendungen",'listShows',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listChannel(url):
        if url=="zdf":
          addDir("Das Aktuellste","http://www.zdf.de/ZDFmediathek/senderstartseite/sst1/1209114",'listVideos',"")
          addDir("Meist gesehen","http://www.zdf.de/ZDFmediathek/senderstartseite/sst2/1209114",'listVideos',"")
        elif url=="zdfneo":
          addDir("Das Aktuellste","http://www.zdf.de/ZDFmediathek/kanaluebersicht/aktuellste/857392",'listVideos',"")
          addDir("Tipps","http://www.zdf.de/ZDFmediathek/senderstartseite/sst0/1209122",'listVideos',"")
          addDir("Themen","http://www.zdf.de/ZDFmediathek/senderstartseite/sst1/1209122",'listShows',"")
          addDir("Sendungen","http://www.zdf.de/ZDFmediathek/senderstartseite/sst2/1209122",'listShows',"")
        elif url=="zdfkultur":
          addDir("Das Aktuellste","http://www.zdf.de/ZDFmediathek/kanaluebersicht/aktuellste/1321386",'listVideos',"")
          addDir("Tipps","http://www.zdf.de/ZDFmediathek/senderstartseite/sst0/1317640",'listVideos',"")
          addDir("Sendungen","http://www.zdf.de/ZDFmediathek/senderstartseite/sst1/1317640",'listShows',"")
          addDir("Meist gesehen","http://www.zdf.de/ZDFmediathek/senderstartseite/sst2/1317640",'listVideos',"")
        elif url=="zdfinfo":
          addDir("Das Aktuellste","http://www.zdf.de/ZDFmediathek/kanaluebersicht/aktuellste/398",'listVideos',"")
          addDir("Tipps","http://www.zdf.de/ZDFmediathek/senderstartseite/sst0/1209120",'listVideos',"")
          addDir("Sendungen","http://www.zdf.de/ZDFmediathek/senderstartseite/sst1/1209120",'listShows',"")
          addDir("Meist gesehen","http://www.zdf.de/ZDFmediathek/senderstartseite/sst2/1209120",'listVideos',"")
        elif url=="dreisat":
          addDir("Das Aktuellste","http://www.zdf.de/ZDFmediathek/senderstartseite/sst1/1209116",'listVideos',"")
          addDir("Sendungen","http://www.zdf.de/ZDFmediathek/senderstartseite/sst2/1209116",'listShows',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listShows(url,bigThumb):
        content = getUrl(url)
        spl=content.split('<div class="image">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<a href="(.+?)">', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            if bigThumb==True:
              thumb=thumb.replace("/timg94x65blob","/timg485x273blob")
            match=re.compile('<p><b><a href="(.+?)">(.+?)<br />', re.DOTALL).findall(entry)
            title=match[0][1]
            title=cleanTitle(title)
            if url.find("?bc=nrt;nrg&amp;gs=446")==-1 and url.find("?bc=nrt;nrg&amp;gs=1456548")==-1 and url.find("?bc=nrt;nrg&amp;gs=1384544")==-1 and url.find("?bc=nrt;nrg&amp;gs=1650526")==-1 and url.find("?bc=nrt;nrg&amp;gs=1650818")==-1:
              addDir(title,"http://www.zdf.de"+url,'listVideos',"http://www.zdf.de"+thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        urlMain=url
        if url.find("/nachrichten/ganze-sendungen")==-1:
          if url.find("?bc=")>=0:
            url=url[:url.find("?bc=")]
          if url.find("?sucheText=")==-1:
            url=url+"?teaserListIndex=500"
        else:
          url=url.replace("&amp;","&")+"&teaserListIndex=75"
        content = getUrl(url)
        spl=content.split('<div class="image">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            if entry.find("BILDER</a></p>")==-1 and entry.find(">INTERAKTIV</a></p>")==-1 and entry.find("BEITR&Auml;GE")==-1:
              match1=re.compile('/video/(.+?)/', re.DOTALL).findall(entry)
              match2=re.compile('/live/(.+?)/', re.DOTALL).findall(entry)
              if len(match1)>=1:
                url=match1[0]
              elif len(match2)>=1:
                url=match2[0]
              match=re.compile('<p class="grey"><a href="(.+?)">(.+?)</a></p>', re.DOTALL).findall(entry)
              date=""
              if len(match)>0:
                date=match[0][1]
              date=date.replace('<span class="orange">','').replace('</span>','')
              match=re.compile('>VIDEO, (.+?)<', re.DOTALL).findall(entry)
              length=""
              if len(match)>0:
                length=match[0]
              match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
              thumb=match[0]
              thumb=thumb.replace("/timg94x65blob","/timg485x273blob")
              if thumb.find("http://www.zdf.de/")==-1:
                thumb="http://www.zdf.de"+thumb
              match=re.compile('<p><b><a href="(.+?)">(.+?)<br />', re.DOTALL).findall(entry)
              title=match[0][1]
              title=cleanTitle(title)
              date=cleanTitle(date)
              if date.find(".20")>=0:
                date=date[:date.find(".20")]
              title=date+" - "+title
              if urlMain.find("/live/day0")>0 and entry.find(">LIVE</a></p>")>=0:
                addLink(title,url,'playVideo',thumb,length)
              elif urlMain.find("/live/day0")==-1 and entry.find(">LIVE</a></p>")==-1:
                addLink(title,url,'playVideo',thumb,length)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        content = getUrl("http://www.zdf.de/ZDFmediathek/xmlservice/web/beitragsDetails?id="+url+"&ak=web")
        match1=re.compile('<formitaet basetype="h264_aac_mp4_rtmp_zdfmeta_http" isDownload="false">\n                <quality>veryhigh</quality>\n                <url>(.+?)</url>', re.DOTALL).findall(content)
        match2=re.compile('<formitaet basetype="h264_aac_mp4_rtmp_zdfmeta_http" isDownload="false">\n                <quality>high</quality>\n                <url>(.+?)</url>', re.DOTALL).findall(content)
        match3=re.compile('<formitaet basetype="h264_aac_na_rtsp_mov_http" isDownload="false">\n                <quality>veryhigh</quality>\n                <url>(.+?)</url>', re.DOTALL).findall(content)
        url=""
        finalUrl=""
        if content.find("<type>livevideo</type>")>=0:
          if len(match3)>=1:
            url=match3[0]
            content = getUrl(url)
            match=re.compile('RTSPtext\n(.+?)\n', re.DOTALL).findall(content)
            finalUrl=match[0]
        elif content.find("<type>video</type>")>=0:
          if len(match1)>=1:
            url=match1[0]
            content = getUrl(url)
            match=re.compile('<default-stream-url>(.+?)</default-stream-url>', re.DOTALL).findall(content)
            finalUrl=match[0]
          elif len(match2)>=1:
            url=match2[1]
            content = getUrl(url)
            match=re.compile('<default-stream-url>(.+?)</default-stream-url>', re.DOTALL).findall(content)
            finalUrl=match[0]
        if finalUrl!="":
          listitem = xbmcgui.ListItem(path=finalUrl)
          return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def search():
        keyboard = xbmc.Keyboard('', 'Video Suche')
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listVideos("http://www.zdf.de/ZDFmediathek/suche?sucheText="+search_string)

def listAZ():
        addDir("ABC","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz0",'listShows',"")
        addDir("DEF","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz1",'listShows',"")
        addDir("GHI","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz2",'listShows',"")
        addDir("JKL","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz3",'listShows',"")
        addDir("MNO","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz4",'listShows',"")
        addDir("PQRS","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz5",'listShows',"")
        addDir("TUV","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz6",'listShows',"")
        addDir("WXYZ","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz7",'listShows',"")
        addDir("0-9","http://www.zdf.de/ZDFmediathek/hauptnavigation/sendung-a-bis-z/saz8",'listShows',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö").replace("&eacute;","é").replace("&egrave;","è")
        title=title.strip()
        return title

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

def addLink(name,url,mode,iconimage,duration=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Duration": duration } )
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

if mode == 'listChannel':
    listChannel(url)
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'listShows':
    listShows(url,True)
elif mode == 'listThemen':
    listShows(url,False)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
elif mode == 'listAZ':
    listAZ()
else:
    index()
