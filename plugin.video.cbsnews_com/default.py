#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,httplib,socket,time

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.video.cbsnews_com')
translation = addon.getLocalizedString

forceViewMode=addon.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(addon.getSetting("viewMode"))

maxBitRate=addon.getSetting("maxBitRate")
qual=[500,1000,1500,2000,3000]
maxBitRate=qual[int(maxBitRate)]

def index():
        content = getUrl("http://www.cbsnews.com/video/")
        spl=content.split('<li><h2><a href=')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('"(.+?)"', re.DOTALL).findall(entry)
            nextUrl=match[0]
            match=re.compile('nodeid="(.+?)"', re.DOTALL).findall(entry)
            match2=re.compile('nodeId="(.+?)"', re.DOTALL).findall(entry)
            if len(match)>0:
              noteId=match[0]
            elif len(match2)>0:
              noteId=match2[0]
            match=re.compile('slug="(.+?)">(.+?)<', re.DOTALL).findall(entry)
            title=match[0][1]
            title=cleanTitle(title)
            match=re.compile('pagetype="(.+?)"', re.DOTALL).findall(entry)
            if len(match)>0:
              pageType=match[0]
            else:
              pageType="1611"
            url="http://www.cbsnews.com/"+pageType+"-"+noteId+"_162-1.html?nomesh"
            if title=="Evening News":
              addDir(title,"",'listEveningMain',"")
            elif title=="60 Minutes":
              addDir(title,"",'list60MinutesMain',"")
            elif title=="48 Hours":
              addDir(title,nextUrl,'listVideos',"")
            else:
              addDir(title,url+"#"+nextUrl,'listLatest',"")
        addDir("Up To The Minute","http://www.cbsnews.com/2076-3455_162-0.html",'listVideos',"")
        addDir(translation(30002),"",'search',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listEveningMain():
        addLink(translation(30004),"",'playEveningLatest',"")
        addDir(translation(30005),"http://www.cbsnews.com/2003-503445_162-0.html",'listVideos',"")
        addDir(translation(30006),"http://www.cbsnews.com/video/eveningnews/",'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def list60MinutesMain():
        content = getUrl("http://www.cbsnews.com/60-minutes/")
        match=re.compile('<strong class="sideScrollerTitle"><span>(.+?)</span></strong>', re.DOTALL).findall(content)
        for title in match:
          addDir(title,title,'list60Minutes',"")
        addDir(translation(30007),"http://www.cbsnews.com/video/60minutes/",'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def list60Minutes(title):
        content = getUrl("http://www.cbsnews.com/60-minutes/")
        content = content[content.find('<strong class="sideScrollerTitle"><span>'+title+'</span></strong>'):]
        content = content[:content.find('</ul>'):]
        match=re.compile('<li class="promoBox"> <a href="(.+?)"(.+?)loadsrc="(.+?)"(.+?)class="assetTitle">(.+?)</a> <p class="storySub">(.+?)</p> </li>', re.DOTALL).findall(content)
        for url, temp, thumb, temp2, title, date in match:
          fullDate=date
          date=date.strip().replace(",","")
          dateTemp = time.strptime(date, '%B %d %Y')
          dateShort = time.strftime("%m/%d", dateTemp)
          title=dateShort+" - "+title
          addLink(title,url,'playVideo',thumb,fullDate)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playEveningLatest():
        content = getUrl("http://www.cbsnews.com/2003-503445_162-0.html")
        match=re.compile('<li> <a href="(.+?)"(.+?)alt="(.+?)"', re.DOTALL).findall(content)
        playVideo(match[0][0], match[0][2])

def listLatest(url):
        spl=url.split("#")
        url=spl[0]
        nextUrl=spl[1]
        content = getUrl(url)
        spl=content.split('<li class="promoBox">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            if url.find("/video/watch/")==0:
              url="http://www.cbsnews.com"+url
            match=re.compile('<p class="assetDek">(.+?)</p>', re.DOTALL).findall(entry)
            desc=""
            if len(match)>0:
              desc=match[0]
              desc=cleanTitle(desc)
            match=re.compile('class="assetTitle">(.+?)</a>', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('<span class="duration">(.+?)</span>(.+?)</p>', re.DOTALL).findall(entry)
            length=""
            date=""
            if len(match)>0:
              length=match[0][0]
              length=str(int(length[:length.find(":")])+1)
              date=match[0][1]
              date=date[:date.find("|")].strip().replace(",","")
              dateTemp = time.strptime(date, '%B %d %Y')
              dateShort = time.strftime("%m/%d", dateTemp)
              title=dateShort+" - "+title
              desc=date+"\n"+desc
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,url,'playVideo',thumb,desc,length)
        if nextUrl.find("/video/")>=0:
          addDir(translation(30003),nextUrl,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        if "http://" not in url:
          url="http://www.cbsnews.com"+url
        urlMain=url
        content = getUrl(url)
        tempTitle=""
        match=re.compile('http://www.cbsnews.com/video/(.+?)/', re.DOTALL).findall(url)
        if len(match)>0:
          tempTitle=match[0]
        if content.find('<div style="background-image')>=0 and "http://www.cbsnews.com/2003-503445_162-0" not in urlMain:
          spl=content.split('<div style="background-image')
          for i in range(1,len(spl),1):
              entry=spl[i]
              match=re.compile('<h2 class="storyTitle"><a href="(.+?)">(.+?)</a></h2>', re.DOTALL).findall(entry)
              url=match[0][0]
              title=match[0][1]
              title=cleanTitle(title)
              match=re.compile('<p class="datestamp">(.+?)</p>', re.DOTALL).findall(entry)
              date=""
              if len(match)>0:
                date=match[0].replace('<span class="separatorGrey">','')
                date=date[:date.find("|")].strip().replace(",","")
                dateTemp = time.strptime(date, '%B %d %Y')
                dateShort = time.strftime("%m/%d", dateTemp)
                title=dateShort+" - "+title
              match=re.compile('<p class="storyDek">(.+?)</p>', re.DOTALL).findall(entry)
              desc=""
              if len(match)>0:
                desc=match[0]
                desc=cleanTitle(desc)
              if date!="":
                desc=date+"\n"+desc
              match=re.compile("url\\('(.+?)'\\)", re.DOTALL).findall(entry)
              thumb=match[0]
              addLink(title,url,'playVideo',thumb,desc)
        elif content.find('<li> <a href="http://www.cbsnews.com/video/watch/')>=0 or content.find('<li> <a href="/video/watch/')>=0:
          if content.find('<li> <a href="http://www.cbsnews.com/video/watch/')>=0:
            spl=content.split('<li> <a href="http://www.cbsnews.com/video/watch/')
          elif content.find('<li> <a href="/video/watch/')>=0:
            spl=content.split('<li> <a href="/video/watch/')
          for i in range(1,len(spl),1):
              entry=spl[i]
              match=re.compile('alt=(.+?)/>', re.DOTALL).findall(entry)
              title=match[0]
              title=cleanTitle(title).replace('"','')
              url="http://www.cbsnews.com/video/watch/"+entry[:entry.find('"')]
              match=re.compile('<p class="datestamp">(.+?)</p>', re.DOTALL).findall(entry)
              date=""
              if len(match)>0:
                date=match[0].replace('<span class="separatorGrey">','')
                date=date[:date.find("|")].strip().replace(",","")
                dateTemp = time.strptime(date, '%B %d %Y')
                dateShort = time.strftime("%m/%d", dateTemp)
                if "http://www.cbsnews.com/2003-503445_162-0" not in urlMain:
                  title=dateShort+" - "+title
              match=re.compile('<p class="storyDek">(.+?)</p>', re.DOTALL).findall(entry)
              desc=""
              if len(match)>0:
                desc=match[0]
                desc=cleanTitle(desc)
              match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
              thumb=match[0]
              addLink(title,url,'playVideo',thumb,date+"\n"+desc)
        matchPage=re.compile('<li class="next"> <a href="(.+?)">', re.DOTALL).findall(content)
        matchPage2=re.compile('<li class="next" section="next"><a href="(.+?)" rel="next">', re.DOTALL).findall(content)
        urlNext=""
        if len(matchPage)>0:
          urlNext=matchPage[0]
        if len(matchPage2)>0:
          urlNext=matchPage2[0]
        if urlNext!="":
          if urlNext.find("/video//")>=0:
            urlNext=urlNext.replace("/video//","/video/"+tempTitle+"/")
          addDir(translation(30001),urlNext,'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def search():
        keyboard = xbmc.Keyboard('', translation(30002))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listSearchResults('http://www.cbsnews.com/1770-5_162-0.html?query='+search_string+'&searchtype=cbsSearch&pageType=14&rpp=30')

def listSearchResults(url):
        content = getUrl(url)
        spl=content.split('<li section=')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<span class="date">(.+?)<', re.DOTALL).findall(entry)
            date=match[0]
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('class="title">(.+?)<', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=""
            if len(match)>0:
              thumb=match[0]
            addLink(title,url,'playVideo',thumb,date)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url,title=""):
        content = getUrl(url)
        match=re.compile('setVideoId\\("(.+?)"\\)', re.DOTALL).findall(content)
        match2=re.compile('setVideoId\\((.+?)\\)', re.DOTALL).findall(content)
        if len(match)>0:
          id=match[0]
        elif len(match2)>0:
          id=match2[0]
        content = getUrl("http://api.cnet.com/rest/v1.0/video?videoId="+id+"&iod=videoMedia&players=Download,Streaming")
        spl=content.split('<VideoMedia id=')
        maxBitrateTemp=0
        finalUrl=""
        for i in range(1,len(spl),1):
            entry=spl[i]
            if entry.find("<DeliveryUrl>")>=0:
              match=re.compile('<BitRate>(.+?)</BitRate>', re.DOTALL).findall(entry)
              bitrate=int(match[0])
              if bitrate>maxBitrateTemp and bitrate<=maxBitRate:
                maxBitrateTemp=bitrate
                match=re.compile('<DeliveryUrl><!\\[CDATA\\[(.+?)\\]\\]></DeliveryUrl>', re.DOTALL).findall(entry)
                finalUrl=match[0]
        if finalUrl!="":
          listitem = xbmcgui.ListItem(path=finalUrl)
          if title!="":
            listitem.setInfo( type="Video", infoLabels={ "Title": title } )
          xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:16.0) Gecko/20100101 Firefox/16.0')
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

def addLink(name,url,mode,iconimage,desc="",duration=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc, "Duration": duration } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage,desc=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok
         
params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listLatest':
    listLatest(url)
elif mode == 'listEveningMain':
    listEveningMain()
elif mode == 'list60MinutesMain':
    list60MinutesMain()
elif mode == 'list60Minutes':
    list60Minutes(url)
elif mode == 'listSearchResults':
    listSearchResults(url)
elif mode == 'playEveningLatest':
    playEveningLatest()
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
else:
    index()
