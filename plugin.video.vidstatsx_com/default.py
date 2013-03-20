#!/usr/bin/python
# -*- coding: utf-8 -*-
import xbmcaddon,xbmcplugin,xbmcgui,sys,urllib,urllib2,re,socket,os

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID = 'plugin.video.vidstatsx_com'
xbox = xbmc.getCondVisibility("System.Platform.xbox")
addon = xbmcaddon.Addon(addonID)
channelFavsFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".favorites")
translation = addon.getLocalizedString

videoChartsSortType=addon.getSetting("videoChartsSortType")
types=[translation(30105),translation(30010),translation(30013),translation(30011),translation(30015),translation(30016)]
videoChartsSortType=types[int(videoChartsSortType)]
videoChartsSortTime=addon.getSetting("videoChartsSortTime")
times=[translation(30105),translation(30017),translation(30018),translation(30019)]
videoChartsSortTime=times[int(videoChartsSortTime)]
forceViewMode=addon.getSetting("forceViewMode")
viewMode=str(addon.getSetting("viewMode"))

def index():
        addDir(translation(30001),"","mostSubscribedMain","")
        addDir(translation(30002),"","mostViewedMain","")
        addDir(translation(30003),"","videoChartsMain","")
        xbmcplugin.endOfDirectory(pluginhandle)

def mostSubscribedMain():
        url="http://vidstatsx.com/youtube-top-100-most-subscribed-channels"
        addDir(translation(30004),url,"listChannels","")
        addDir(translation(30005),url,"showCategories","")
        addDir(translation(30006),url,"showLanguages","")
        addDir("VEVO","http://vidstatsx.com/vevo-most-subscribed","listChannels","")
        xbmcplugin.endOfDirectory(pluginhandle)

def mostViewedMain():
        url="http://vidstatsx.com/youtube-top-100-most-viewed"
        addDir(translation(30004),url,"listChannels","")
        addDir(translation(30005),url,"showCategories","")
        addDir(translation(30006),url,"showLanguages","")
        xbmcplugin.endOfDirectory(pluginhandle)

def videoChartsMain():
        addDir(translation(30004),"http://vidstatsx.com/most-popular-videos-today","videoChartsOrderBy","")
        showCategories("http://vidstatsx.com/most-popular-videos-today")

def topGainersMain():
        addDir(translation(30021),"http://vidstatsx.com/top-100-1h-sub-gains","listChannels","")
        addDir(translation(30023),"http://vidstatsx.com/top-100-24h-sub-gains","listChannels","")
        addDir(translation(30024),"http://vidstatsx.com/top-100-7d-sub-gains","listChannels","")
        xbmcplugin.endOfDirectory(pluginhandle)

def listChannels(url):
        content = getUrlVSX(url)
        match=re.compile('<title>(.+?)</title>', re.DOTALL).findall(content)
        siteTitle=match[0]
        spl=content.split('<td id=')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match1=re.compile('<td class="rank center">(.+?)</td><td class="padl">(.+?)</td>', re.DOTALL).findall(entry)
          match2=re.compile('<td class="rank center">(.+?)</td><td>(.+?)</td>', re.DOTALL).findall(entry)
          if siteTitle.find("Top 100 Most Viewed")>=0:
            count=match1[0][1]
            count+=" Views"
          else:
            count=match2[0][1]
            count+=" Subscribers"
          count=count.replace('<span class="gray">K</span>','K')
          match=re.compile('href="//www.youtube.com/user/(.+?)"', re.DOTALL).findall(entry)
          user=match[0]
          title="[B]"+user+"[/B]  -  "+count
          addChannelDir(title,user+"#1",'showYoutubeOrderBy',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def showCategories(url):
        if url=="http://vidstatsx.com/most-popular-videos-today":
          type="videoChartsOrderBy"
        else:
          type="listChannels"
        cats=[[translation(30030), "autos-vehicles"],[translation(30031), "comedy"],[translation(30032), "education"],[translation(30033), "entertainment"],[translation(30034), "film-animation"],[translation(30035), "games-gaming"],[translation(30036), "how-to-style"],[translation(30037), "news-politics"],[translation(30038), "nonprofit-activism"],[translation(30039), "people-vlogs"],[translation(30040), "pets-animals"],[translation(30041), "science-tech"],[translation(30042), "shows"],[translation(30043), "sports"],[translation(30044), "travel-events"]]
        for cat in cats:
          addDir(cat[0],url.replace("-most-subscribed-channels","-most-subscribed-"+cat[1]+"-channels").replace("-most-viewed","-most-viewed-"+cat[1]).replace("most-popular-videos-","most-popular-"+cat[1]+"-videos-"),type,"")
        xbmcplugin.endOfDirectory(pluginhandle)

def showLanguages(url):
        cats=[[translation(30050), "argentina-ar"],[translation(30051), "australia-au"],[translation(30052), "brazil-br"],[translation(30053), "canada-ca"],[translation(30054), "czech-republic-cz"],[translation(30055), "france-fr"],[translation(30056), "germany-de"],[translation(30057), "great-britain-gb"],[translation(30058), "hong-kong-hk"],[translation(30059), "india-in"],[translation(30060), "ireland-ie"],[translation(30061), "israel-il"],[translation(30062), "italy-it"],[translation(30063), "japan-jp"],[translation(30064), "mexico-mx"],[translation(30065), "netherlands-nl"],[translation(30066), "new-zealand-nz"],[translation(30067), "poland-pl"],[translation(30068), "russia-ru"],[translation(30069), "south-africa-za"],[translation(30070), "south-korea-kr"],[translation(30071), "spain-es"],[translation(30072), "sweden-se"],[translation(30073), "taiwan-tw"],[translation(30074), "united-states-us"]]
        for cat in cats:
          addDir(cat[0],url.replace("-most-subscribed-channels","-most-subscribed-"+cat[1]+"-channels").replace("-most-viewed","-most-viewed-"+cat[1]),"listChannels","")
        xbmcplugin.endOfDirectory(pluginhandle)

def showYoutubeOrderBy(url):
        addDir(translation(30009),url+"#published","listVideos","")
        addDir(translation(30010),url+"#viewCount","listVideos","")
        addDir(translation(30011),url+"#rating","listVideos","")
        xbmcplugin.endOfDirectory(pluginhandle)

def videoChartsOrderBy(url):
        if url=="http://vidstatsx.com/recently-featured-videos":
          listVideoCharts(url)
        else:
          if videoChartsSortType==str(translation(30105)):
            addDir(translation(30010),url,"listVideoCharts","")
            addDir(translation(30013),url.replace("/most-popular-","/top-favorited-"),"videoChartsOrderBy2","")
            addDir(translation(30011),url.replace("/most-popular-","/top-rated-"),"videoChartsOrderBy2","")
            addDir(translation(30015),url.replace("/most-popular-","/most-commented-"),"videoChartsOrderBy2","")
            addDir(translation(30016),url.replace("/most-popular-","/most-responded-"),"videoChartsOrderBy2","")
            xbmcplugin.endOfDirectory(pluginhandle)
          elif videoChartsSortType==translation(30010):
            videoChartsOrderBy2(url)
          elif videoChartsSortType==translation(30013):
            videoChartsOrderBy2(url.replace("/most-popular-","/top-favorited-"))
          elif videoChartsSortType==translation(30011):
            videoChartsOrderBy2(url.replace("/most-popular-","/top-rated-"))
          elif videoChartsSortType==translation(30015):
            videoChartsOrderBy2(url.replace("/most-popular-","/most-commented-"))
          elif videoChartsSortType==translation(30016):
            videoChartsOrderBy2(url.replace("/most-popular-","/most-responded-"))

def videoChartsOrderBy2(url):
        if videoChartsSortTime==str(translation(30105)):
          addDir(translation(30017),url,"listVideoCharts","")
          addDir(translation(30018),url.replace("-today","-this-week"),"listVideoCharts","")
          addDir(translation(30019),url.replace("-today","-this-month"),"listVideoCharts","")
          xbmcplugin.endOfDirectory(pluginhandle)
        elif videoChartsSortTime==translation(30017):
            listVideoCharts(url)
        elif videoChartsSortTime==translation(30018):
            listVideoCharts(url.replace("-today","-this-week"))
        elif videoChartsSortTime==translation(30019):
            listVideoCharts(url.replace("-today","-this-month"))

def listVideos(params):
        spl=params.split("#")
        user=spl[0]
        index=spl[1]
        orderby=spl[2]
        content = getUrl("http://gdata.youtube.com/feeds/api/videos?author="+user+"&racy=include&max-results=50&start-index="+index+"&orderby="+orderby+"&v=2")
        match=re.compile("<openSearch:totalResults>(.+?)</openSearch:totalResults><openSearch:startIndex>(.+?)</openSearch:startIndex>", re.DOTALL).findall(content)
        maxIndex=int(match[0][0])
        startIndex=int(match[0][1])
        spl=content.split('<entry')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('<yt:videoid>(.+?)</yt:videoid>', re.DOTALL).findall(entry)
          id=match[0]
          match=re.compile("viewCount='(.+?)'", re.DOTALL).findall(entry)
          viewCount="0"
          if len(match)>0:
            viewCount=match[0]
          match=re.compile("duration='(.+?)'", re.DOTALL).findall(entry)
          durationTemp=int(match[0])
          min=(durationTemp/60)+1
          sec=durationTemp%60
          duration=str(min)+":"+str(sec)
          match=re.compile("<author><name>(.+?)</name>", re.DOTALL).findall(entry)
          author=match[0]
          match=re.compile("<media:title type='plain'>(.+?)</media:title>", re.DOTALL).findall(entry)
          title=match[0]
          title=cleanTitle(title)
          match=re.compile("<media:description type='plain'>(.+?)</media:title>", re.DOTALL).findall(entry)
          desc=""
          if len(match)>0:
            desc=match[0]
            desc=cleanTitle(desc)
          match=re.compile("<published>(.+?)T", re.DOTALL).findall(entry)
          date=match[0]
          thumb="http://img.youtube.com/vi/"+id+"/0.jpg"
          addLink(title,id,'playVideo',thumb,"Date: "+date+"; Views: "+viewCount+"\n"+desc,duration,author)
        if startIndex+50<=maxIndex:
          addDir(translation(30007),user+"#"+str(int(index)+50)+"#"+orderby,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideoCharts(url):
        content = getUrlVSX(url)
        spl=content.split('<div class="contain-v">')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('/watch\\?v=(.+?)&', re.DOTALL).findall(entry)
          id=match[0]
          match=re.compile('<span class="overlay-report views">(.+?)</span>', re.DOTALL).findall(entry)
          count=match[0]
          match=re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
          title=match[0]
          match=re.compile('title="(.+?)"', re.DOTALL).findall(entry)
          desc=match[0]
          thumb="http://img.youtube.com/vi/"+id+"/0.jpg"
          title=cleanTitle(title)
          desc=cleanTitle(desc)
          addLink(title,id,'playVideo',thumb,desc)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(youtubeID):
        url = getYoutubeUrl(youtubeID)
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def getYoutubeUrl(youtubeID):
        if xbox==True:
          url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + youtubeID
        else:
          url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + youtubeID
        return url

def playChannel(id):
        content = getUrl("http://gdata.youtube.com/feeds/api/videos?author="+id+"&racy=include&max_results=25&start-index=1&orderby=published")
        spl=content.split('<entry>')
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        for i in range(1,len(spl),1):
          try:
            entry=spl[i]
            match=re.compile('<id>http://gdata.youtube.com/feeds/api/videos/(.+?)</id>', re.DOTALL).findall(entry)
            id=match[0]
            url = getYoutubeUrl(id)
            match=re.compile("<title type='text'>(.+?)</title>", re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            listitem = xbmcgui.ListItem(title)
            playlist.add(url,listitem)
          except:
            pass
        xbmc.Player().play(playlist)

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:18.0) Gecko/20100101 Firefox/18.0')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link

def getUrlVSX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'XBMC VidStatsX Addon')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return link

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&#038;","&").replace("&#8230;","...").replace("&#8211;","-").replace("&#8220;","-").replace("&#8221;","-").replace("&#8217;","'")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def addLink(name,url,mode,iconimage,desc="",duration="",author=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc, "Duration": duration, "Director": author } )
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

def addChannelDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        if iconimage=="": iconimage="DefaultFolder.png"
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        user=name[:name.find("  -")].replace("[B]","").replace("[/B]","")
        playListInfos="ADD#"+user+"#"+user+"#"+iconimage+"#"
        liz.addContextMenuItems([(translation(30079), 'XBMC.RunPlugin(plugin://'+addonID+'/?mode=playChannel&url='+user+')',),(translation(30076), 'RunPlugin(plugin://plugin.video.youtube.channels/?mode=addChannel&url='+urllib.quote_plus(name+"#"+name+"#"+iconimage+"#")+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

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

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listChannels':
    listChannels(url)
elif mode == 'favoriteChannels':
    favoriteChannels()
elif mode == 'mostSubscribedMain':
    mostSubscribedMain()
elif mode == 'mostViewedMain':
    mostViewedMain()
elif mode == 'videoChartsMain':
    videoChartsMain()
elif mode == 'topGainersMain':
    topGainersMain()
elif mode == 'showCategories':
    showCategories(url)
elif mode == 'showLanguages':
    showLanguages(url)
elif mode == 'showYoutubeOrderBy':
    showYoutubeOrderBy(url)
elif mode == 'videoChartsOrderBy':
    videoChartsOrderBy(url)
elif mode == 'videoChartsOrderBy2':
    videoChartsOrderBy2(url)
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'listVideoCharts':
    listVideoCharts(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'playChannel':
    playChannel(url)
else:
    index()
