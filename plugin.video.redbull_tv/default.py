#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,httplib,socket,time
from pyamf import remoting

pluginhandle = int(sys.argv[1])
xbox = xbmc.getCondVisibility("System.Platform.xbox")
settings = xbmcaddon.Addon(id='plugin.video.redbull_tv')
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
        addDir(translation(30005),"live",'listEvents',"")
        addDir(translation(30006),"latest",'listEvents',"")
        addDir(translation(30002),"http://www.redbull.tv/Redbulltv",'latestVideos',"")
        addDir(translation(30003),"http://www.redbull.tv/cs/Satellite?_=1341624385783&pagename=RBWebTV%2FRBTV_P%2FRBWTVShowContainer&orderby=latest&p=%3C%25%3Dics.GetVar(%22p%22)%25%3E&start=1",'listShows',"")
        addDir(translation(30004),"",'search',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listEvents(url):
        matchPage=""
        if url.find("http://")==0:
          content = getUrl(url)
          matchPage=re.compile('<a href="/includes/fragments/schedule_list.php\\?pg=(.+?)" class="(.+?)">', re.DOTALL).findall(content)
          spl=content.split('<td class="status"><span class="prev">Past</span></td>')
        else:
          content = getUrl("http://live.redbull.tv/includes/fragments/schedule_list.php?pg=1")
          if url=="live":
            if content.find('<span class="live">Live</span>')>0:
              match=re.compile('<td class="description">(.+?)</td>', re.DOTALL).findall(content)
              desc=match[0]
              match=re.compile('<a href="(.+?)">(.+?)<span>(.+?)</span>', re.DOTALL).findall(content)
              url="http://live.redbull.tv"+match[0][0]
              title=match[0][1]
              subTitle=match[0][2]
              title="NOW LIVE: "+title
              title=cleanTitle(title)
              addLink(title,url,'playEvent',"",subTitle+"\n"+desc)
            spl=content.split('<td class="status"><span>Upcoming</span></td>')
          elif url=="latest":
            matchPage=re.compile('<a href="/includes/fragments/schedule_list.php\\?pg=(.+?)" class="(.+?)">', re.DOTALL).findall(content)
            spl=content.split('<td class="status"><span class="prev">Past</span></td>')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<span class="localtime-date-only-med">(.+?)</span>', re.DOTALL).findall(entry)
            date=match[0]
            spl2=date.split("-")
            day=spl2[2]
            month=spl2[1]
            if len(day)==1:
              day="0"+day
            if len(month)==1:
              month="0"+month
            date=day+"."+month
            match=re.compile('<span class="localtime-time-only">(.+?)</span>', re.DOTALL).findall(entry)
            timeFrom=match[0]
            spl2=timeFrom.split("-")
            timeFrom=spl2[3]+":"+spl2[4]
            if len(timeFrom)==4:
              timeFrom="0"+timeFrom
            match=re.compile('<span class="localtime-time-only tz-abbr">(.+?)</span>', re.DOTALL).findall(entry)
            timeTo=match[0]
            spl2=timeTo.split("-")
            timeTo=spl2[3]+":"+spl2[4]
            if len(timeTo)==4:
              timeTo="0"+timeTo
            match=re.compile('<td class="description">(.+?)</td>', re.DOTALL).findall(entry)
            desc=match[0]
            match=re.compile('<a href="(.+?)">(.+?)<span>(.+?)</span>', re.DOTALL).findall(entry)
            url="http://live.redbull.tv"+match[0][0]
            title=match[0][1]
            subTitle=match[0][2]
            title=date+" "+timeFrom+" (GMT) - "+title
            title=cleanTitle(title)
            addLink(title,url,'playEvent',"",date+" "+timeFrom+"-"+timeTo+" (GMT): "+subTitle+"\n"+desc)
        if len(matchPage)>0:
          for pageNr, title in matchPage:
            if title=="next":
              addDir(translation(30001),"http://live.redbull.tv/includes/fragments/schedule_list.php?pg="+pageNr,'listEvents',"")
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
              length = " ("+length+" min)"
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

def playEvent(url):
        content = getUrl(url)
        match=re.compile('<span class="player-id"><span class="(.+?)"></span></span>', re.DOTALL).findall(content)
        if len(match)>0:
          playBrightCoveStream(match[0])
        else:
          match=re.compile('<span class="ts-utc">(.+?)</span>', re.DOTALL).findall(content)
          if len(match)>0:
            xbmc.executebuiltin('XBMC.Notification('+str(translation(30105))+':,'+time.strftime("%d.%m.%y %H:%M",time.localtime(int(match[0]))) +' ('+str(translation(30106))+'),5000)')
          else:
            xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30104))+'!,5000)')
        
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
        for item in sorted(response['renditions'], key=lambda item:item['encodingRate'], reverse=False):
          encRate = item['encodingRate']
          if encRate < maxBitRate:
            streamUrl = item['defaultURL']
        if streamUrl.find("http://")==0:
          listItem = xbmcgui.ListItem(path=streamUrl+"?videoId="+bc_videoID+"&lineUpId=&pubId="+str(bc_publisherID)+"&playerId="+str(bc_playerID)+"&affiliateId=&v=&fp=&r=&g=")
        else:
          url = streamUrl[0:streamUrl.find("&")]
          playpath = streamUrl[streamUrl.find("&")+1:]
          listItem = xbmcgui.ListItem(path=url+' playpath='+playpath)
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
elif mode == 'latestVideos':
    latestVideos(url)
elif mode == 'listShows':
    listShows(url)
elif mode == 'listEvents':
    listEvents(url)
elif mode == 'playEvent':
    playEvent(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
else:
    index()
