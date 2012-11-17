#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,socket,time

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.arte_tv')
translation = settings.getLocalizedString

forceViewMode=settings.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(settings.getSetting("viewMode"))
timeout=int(settings.getSetting("timeout"))
socket.setdefaulttimeout(timeout)

language=""
language=settings.getSetting("language")
if language=="":
  settings.openSettings()
  language=settings.getSetting("language")

if language=="0":
  language="de"
elif language=="1":
  language="fr"

numbers=["10","25","50","100",]
videosPerPage=numbers[int(settings.getSetting("itemsPerPage"))]

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#39;","'").replace("&#039;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def index():
        addDir(translation(30011),"http://videos.arte.tv/"+language+"/videos","vidsDay","")
        addDir(translation(30001),"ARTE_7","showSortList","")
        addDir(translation(30002),"ALL_VIDS","listShows","")
        addDir(translation(30003),"SHOWS_AZ","listShows","")
        addDir(translation(30004),"EVENTS","listShows","")
        addDir(translation(30005),"SEARCH","search","")
        addDir(translation(30012),"","listWebLiveMain","")
        xbmcplugin.endOfDirectory(pluginhandle)

def showSortList(url):
        if url=="ARTE_7":
          urlDate="http://videos.arte.tv/"+language+"/do_delegate/videos/index-3188698,view,asThumbnail.html?hash=tv/thumb/date//1/"+videosPerPage+"/"
          urlTitle="http://videos.arte.tv/"+language+"/do_delegate/videos/index-3188698,view,asThumbnail.html?hash=tv/thumb/title//1/"+videosPerPage+"/"
          urlRated="http://videos.arte.tv/"+language+"/do_delegate/videos/index-3188698,view,asThumbnail.html?hash=tv/thumb/popular/bestrated/1/"+videosPerPage+"/"
          urlViewed="http://videos.arte.tv/"+language+"/do_delegate/videos/index-3188698,view,asThumbnail.html?hash=tv/thumb/popular/mostviewed/1/"+videosPerPage+"/"
        else:
          content = getUrl(url)
          match=re.compile('thumbnailViewUrl: "(.+?)"', re.DOTALL).findall(content)
          url="http://videos.arte.tv"+match[0]
          urlTitle=url+"?hash=tv/thumb/title//1/"+videosPerPage+"/"
          urlDate=url+"?hash=tv/thumb/date//1/"+videosPerPage+"/"
          urlRated=url+"?hash=tv/thumb/popular/bestrated/1/"+videosPerPage+"/"
          urlViewed=url+"?hash=tv/thumb/popular/mostviewed/1/"+videosPerPage+"/"
        addDir(translation(30007),urlDate,"listVideos","")
        addDir(translation(30009),urlViewed,"listVideos","")
        addDir(translation(30008),urlRated,"listVideos","")
        addDir(translation(30006),urlTitle,"listVideos","")
        xbmcplugin.endOfDirectory(pluginhandle)

def listShows(url):
        if url=="ALL_VIDS":
          if language=="de":
            url="http://videos.arte.tv/de/videos/alleVideos"
          elif language=="fr":
            url="http://videos.arte.tv/fr/videos/toutesLesVideos"
        elif url=="SHOWS_AZ":
          if language=="de":
            url="http://videos.arte.tv/de/videos/sendungen"
          elif language=="fr":
            url="http://videos.arte.tv/fr/videos/programmes"
        elif url=="EVENTS":
          url="http://videos.arte.tv/"+language+"/videos/events/index-3188672.html"
        content = getUrl(url)
        content = content[content.find('<div class="navTop"></div>'):]
        content = content[:content.find('</ul>')]
        spl=content.split('<a href')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('>(.+?)<', re.DOTALL).findall(entry)
          title=cleanTitle(match[0])
          match=re.compile('="(.+?)"', re.DOTALL).findall(entry)
          url="http://videos.arte.tv"+match[0]
          addDir(title,url,'showSortList',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def vidsDay(url):
        content = getUrl(url)
        content=content[content.find('<ul class="slider" id="car-one">'):]
        content=content[:content.find('</ul>')]
        spl=content.split('<li')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('<h3>(.+?)</h3>', re.DOTALL).findall(entry)
          title=cleanTitle(match[0])
          match=re.compile('<p><a href="(.+?)">(.+?)</a></p>', re.DOTALL).findall(entry)
          url="http://videos.arte.tv"+match[0][0]
          desc=cleanTitle(match[0][1])
          match=re.compile('class="thumbnail" width="(.+?)" height="(.+?)" src="(.+?)"', re.DOTALL).findall(entry)
          thumb="http://videos.arte.tv"+match[0][2]
          addLink(title,url,'playVideo',thumb,desc)
        xbmcplugin.endOfDirectory(pluginhandle)

def listWebLive(url):
        urlMain=url
        hasNextPage=False
        content = getUrl(url,cookie="liveweb-language="+language.upper())
        if content.find('class="next off"')==-1:
          hasNextPage=True
        content=content[content.find('<div id="wall-mosaique"'):]
        content=content[:content.find('<div class="pagination-new">')]
        spl=content.split('<div class="block')
        for i in range(1,len(spl),1):
          entry=spl[i]
          if entry.find("/video/")>0 or entry.find("/festival/")>0:
            match=re.compile('<strong>(.+?)</strong>', re.DOTALL).findall(entry)
            if len(match)>0:
              title=cleanTitle(match[0])
            else:
              match1=re.compile('/video/(.+?)/', re.DOTALL).findall(entry)
              match2=re.compile('/festival/(.+?)/', re.DOTALL).findall(entry)
              if len(match1)>0:
                title=cleanTitle(match1[0]).replace("_"," ")
              elif len(match2)>0:
                title=cleanTitle(match2[0]).replace("_"," ")
            match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb=match[0]
            addLink(title,url,'playLiveEvent',thumb,"")
        match=re.compile('moveValue=(.+?)&', re.DOTALL).findall(urlMain)
        page=int(match[0])
        if hasNextPage:
          addDir("Next",urlMain.replace("moveValue="+str(page)+"&","moveValue="+str(page+1)+"&"),"listWebLive","")
        xbmcplugin.endOfDirectory(pluginhandle)

def listWebLiveMain():
        addDir(translation(30002),"http://liveweb.arte.tv/searchEvent.do?method=displayElements&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&categoryId=&displayMode=0&eventTagName=","listWebLive","")
        addDir(translation(30013),"http://liveweb.arte.tv/searchEvent.do?method=displayElements&categoryId=8&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&displayMode=0&eventTagName=","listWebLive","")
        addDir(translation(30014),"http://liveweb.arte.tv/searchEvent.do?method=displayElements&categoryId=1&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&displayMode=0&eventTagName=","listWebLive","")
        addDir(translation(30015),"http://liveweb.arte.tv/searchEvent.do?method=displayElements&categoryId=11&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&displayMode=0&eventTagName=","listWebLive","")
        addDir(translation(30016),"http://liveweb.arte.tv/searchEvent.do?method=displayElements&categoryId=7&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&displayMode=0&eventTagName=","listWebLive","")
        addDir(translation(30017),"http://liveweb.arte.tv/searchEvent.do?method=displayElements&categoryId=3&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=&classification=0&displayMode=0&eventTagName=","listWebLive","")
        addDir(translation(30005),"","searchWebLive","")
        xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
        urlMain=url
        content = getUrl(url)
        spl=content.split('<div class="video">')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
          date=match[0]
          match=re.compile('<p class="teaserText">(.+?)</p>', re.DOTALL).findall(entry)
          desc=cleanTitle(match[0])
          desc=date+"\n"+desc
          match=re.compile('<h2><a href="(.+?)">(.+?)</a></h2>', re.DOTALL).findall(entry)
          url="http://videos.arte.tv"+match[0][0]
          title=cleanTitle(match[0][1])
          entry=entry[entry.find('class="thumbnail"'):]
          match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
          thumb="http://videos.arte.tv"+match[0]
          addLink(title,url,'playVideo',thumb,desc,"")
        content=content[content.find('<div class="pagination inside">'):]
        content=content[:content.find('</ul>')]
        spl=content.split('<a href=')
        for i in range(1,len(spl),1):
          entry=spl[i]
          if entry.find('"#"')>=0:
            next=""
            if language=="de":
              next="Weiter"
            elif language=="fr":
              next="Suivant"
            if entry.find(next)>=0:
              match=re.compile('class="{page:\'(.+?)\'}">'+next+'</a>', re.DOTALL).findall(entry)
              nextPage=match[0]
              currentPage=int(nextPage)-1
              url=urlMain.replace("/"+str(currentPage)+"/"+videosPerPage+"/","/"+nextPage+"/"+videosPerPage+"/")
              addDir(translation(30010)+" ("+nextPage+")",url,"listVideos","")
          else:
            if language=="de":
              next="Weiter"
            elif language=="fr":
              next="Suivant"
            if entry.find(next)>=0:
              match=re.compile('"(.+?)"', re.DOTALL).findall(entry)
              url="http://videos.arte.tv"+match[0].replace("&amp;","&")
              match=re.compile('pageNr=(.+?)&', re.DOTALL).findall(url)
              nextPage=match[0]
              addDir(translation(30010)+" ("+nextPage+")",url,"listVideos","")
        xbmcplugin.endOfDirectory(pluginhandle)

def search():
        keyboard = xbmc.Keyboard('', translation(30005))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          if language=="de":
            url="http://videos.arte.tv/de/do_search/videos/suche?q="+search_string
          elif language=="fr":
            url="http://videos.arte.tv/fr/do_search/videos/recherche?q="+search_string
          listVideos(url)

def searchWebLive():
        keyboard = xbmc.Keyboard('', translation(30005))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          url="http://liveweb.arte.tv/searchEvent.do?method=displayElements&globalNames="+search_string+"&eventDateMode=0&moveValue=1&eventDateMode=0&chronology=&globalNames=norah%20jones&classification=0&categoryId=&displayMode=0&eventTagName="
          listWebLive(url)

def playVideo(url):
        url=url.replace("/videos/","/do_delegate/videos/").replace(".html",",view,asPlayerXml.xml")
        content = getUrl(url)
        match=re.compile('<video lang="'+language+'" ref="(.+?)"', re.DOTALL).findall(content)
        url=match[0]
        content = getUrl(url)
        match1=re.compile('<url quality="hd">(.+?)</url>', re.DOTALL).findall(content)
        match2=re.compile('<url quality="sd">(.+?)</url>', re.DOTALL).findall(content)
        urlNew=""
        if len(match1)==1:
          urlNew=match1[0]
        elif len(match2)==1:
          urlNew=match2[0]
        listitem = xbmcgui.ListItem(path=urlNew.replace("/MP4:","/mp4:")+" swfVfy=1 swfUrl=http://videos.arte.tv/blob/web/i18n/view/player_23-3188338-data-5044926.swf")
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def playLiveEvent(url):
        content = getUrl(url)
        match=re.compile("eventId=(.+?)&", re.DOTALL).findall(content)
        id=match[0]
        content = getUrl("http://download.liveweb.arte.tv/o21/liveweb/events/event-"+id+".xml")
        match1=re.compile('<urlHd>(.+?)</urlHd>', re.DOTALL).findall(content)
        match2=re.compile('<urlSd>(.+?)</urlHd>', re.DOTALL).findall(content)
        urlNew=""
        if len(match1)==1:
          urlNew=match1[0]
        elif len(match2)==1:
          urlNew=match2[0]
        if urlNew=="":
          xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30018)+'!,5000)')
        else:
          match=re.compile('e=(.+?)&', re.DOTALL).findall(urlNew)
          expire=int(match[0])
          if expire<time.time():
            xbmc.executebuiltin('XBMC.Notification(Info:,'+translation(30019)+'!,5000)')
          else:
            urlNew=urlNew[:urlNew.find("?")].replace("/MP4:","/mp4:")
            listitem = xbmcgui.ListItem(path=urlNew)
            return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def getUrl(url,cookie=None):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:16.0) Gecko/20100101 Firefox/16.0')
        if cookie!=None:
          req.add_header('Cookie',cookie)
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
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'playLiveEvent':
    playLiveEvent(url)
elif mode == 'vidsDay':
    vidsDay(url)
elif mode == 'listWebLive':
    listWebLive(url)
elif mode == 'listWebLiveMain':
    listWebLiveMain()
elif mode == 'showSortList':
    showSortList(url)
elif mode == 'listShows':
    listShows(url)
elif mode == 'search':
    search()
elif mode == 'searchWebLive':
    searchWebLive()
else:
    index()
