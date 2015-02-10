#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
settings = xbmcaddon.Addon(id='plugin.audio.einslive_de')
translation = settings.getLocalizedString

forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))

def index():
        addDir("O-Ton-Charts","http://www.einslive.de/comedy/o_ton_charts/",'oTonCharts',"")
        addDir("O-Ton-Charts Top100","http://www.einslive.de/comedy/o_ton_charts/top_100/120409_otc_top100_1_bis_10.jsp",'oTonChartsTop100',"")
        addDir("Comedy","http://podcast.wdr.de/radio/comedy.xml",'listRSS',"")
        addDir("Plan B Reportage","http://podcast.wdr.de/radio/planbreportage.xml",'listRSS',"")
        addDir("Mitwisser","http://podcast.wdr.de/radio/allerbeste.xml",'listRSS',"")
        addDir("Plan B Talk","http://podcast.wdr.de/radio/planbtalk.xml",'listRSS',"")
        addDir(translation(30004),"http://podcast.wdr.de/radio/diegaeste.xml",'listRSS',"")
        addDir("Klubbing","http://podcast.wdr.de/radio/1liveklubbing.xml",'listRSS',"")
        addDir(str(translation(30002))+" Olli Briesch "+str(translation(30003))+" Imhof","http://podcast.wdr.de/radio/briesch_imhof.xml",'listRSS',"")
        addDir(str(translation(30002))+" Terhoeven "+str(translation(30003))+" Dietz","http://podcast.wdr.de/radio/terhoeven_dietz.xml",'listRSS',"")
        addDir(str(translation(30002))+" Tobi Schäfer "+str(translation(30003))+" Bursche","http://podcast.wdr.de/radio/schaefer_bursche.xml",'listRSS',"")
        addLink("diggi - "+str(translation(30001)),"http://www.wdr.de/wdrlive/media/einslivedigi.m3u",'playAudio',"")
        addLink("Fliehe - "+str(translation(30001)),"http://www.wdr.de/wdrlive/media/1live_fiehe.m3u",'playAudio',"")
        addLink("Plan B - "+str(translation(30001)),"http://www.wdr.de/wdrlive/media/1live_planb.m3u",'playAudio',"")
        addLink("Plan B mit Curse - "+str(translation(30001)),"http://www.wdr.de/wdrlive/media/1live_planbmit.m3u",'playAudio',"")
        addLink("Kasettendeck - "+str(translation(30001)),"http://www.wdr.de/wdrlive/media/1live_kassettendeck.m3u",'playAudio',"")
        addLink("Klubbing - "+str(translation(30001)),"http://www.wdr.de/wdrlive/media/1live_klubbing.m3u",'playAudio',"")
        addLink("Rocker - "+str(translation(30001)),"http://www.wdr.de/wdrlive/media/1live_rocker.m3u",'playAudio',"")
        addLink("1LIVE - Livestream","http://www.wdr.de/wdrlive/media/einslive.m3u",'playAudio',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def oTonCharts(url):
        content = getUrl(url)
        spl=content.split('<p class="wsBlContEL">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<label for="(.+?)">(.+?)</label>', re.DOTALL).findall(entry)
            title=match[0][1]
            title=cleanTitle(title)
            match=re.compile('dslSrc=(.+?)&', re.DOTALL).findall(entry)
            url=match[0]
            addLink(title,url,'playAudio',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def oTonChartsTop100(url):
        urlMain=url
        content = getUrl(url)
        spl=content.split('audioLink">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('</span>(.+?)\\]', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)+"]"
            match=re.compile('dslSrc=(.+?)&', re.DOTALL).findall(entry)
            url="rtmp://gffstream.fcod.llnwd.net/a792/e2/mediendb/1live"+match[0]
            addLink(title,url,'playAudio',"")
        if urlMain.find('1_bis_10.jsp')>=0:
          addDir(translation(30005)+" 11 "+str(translation(30006))+" 40","http://www.einslive.de/comedy/o_ton_charts/top_100/120409_otc_top100_11_bis_40.jsp",'oTonChartsTop100',"")
        elif urlMain.find('11_bis_40.jsp')>=0:
          addDir(translation(30005)+" 41 "+str(translation(30006))+" 70","http://www.einslive.de/comedy/o_ton_charts/top_100/120409_otc_top100_41_bis_70.jsp",'oTonChartsTop100',"")
        elif urlMain.find('41_bis_70.jsp')>=0:
          addDir(translation(30005)+" 71 "+str(translation(30006))+" 100","http://www.einslive.de/comedy/o_ton_charts/top_100/120409_otc_top100_71_bis_100.jsp",'oTonChartsTop100',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listRSS(url):
        content = getUrl(url)
        spl=content.split('<item>')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<title>(.+?)</title>', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('<link>(.+?)</link>', re.DOTALL).findall(entry)
            url=match[0]
            addLink(title,url,'playAudio',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playAudio(url):
        if url.find(".m3u")>=0:
          url=getUrl(url)
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.replace("1LIVE - Comedy: ","").replace("1LIVE - Plan B Reportage: ","").replace("1LIVE - Plan B Talk: ","").replace("1LIVE - Die Gäste: ","").replace("1LIVE - Klubbing: ","").replace("1LIVE mit Olli Briesch und dem Imhof: ","").replace("1LIVE mit Terhoeven und dem Dietz: ","").replace("1LIVE mit Tobi Schäfer und dem Bursche: ","")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
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

if mode == 'oTonCharts':
    oTonCharts(url)
elif mode == 'oTonChartsTop100':
    oTonChartsTop100(url)
elif mode == 'listRSS':
    listRSS(url)
elif mode == 'playAudio':
    playAudio(url)
else:
    index()
