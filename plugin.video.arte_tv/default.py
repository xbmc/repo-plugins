#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.arte_tv')
translation = settings.getLocalizedString

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
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#39;","\\").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

def index():
        addDir(translation(30001),"ARTE_7","showSortList","")
        addDir(translation(30002),"ALL_VIDS","listShows","")
        addDir(translation(30003),"SHOWS_AZ","listShows","")
        addDir(translation(30004),"EVENTS","listShows","")
        addDir(translation(30005),"SEARCH","search","")
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
        addDir(translation(30006),urlTitle,"listVideos","")
        addDir(translation(30007),urlDate,"listVideos","")
        addDir(translation(30008),urlRated,"listVideos","")
        addDir(translation(30009),urlViewed,"listVideos","")
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

def listVideos(url):
        urlMain=url
        content = getUrl(url)
        spl=content.split('<div class="video">')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
          date=match[0]
          match=re.compile('<h2><a href="(.+?)">(.+?)</a></h2>', re.DOTALL).findall(entry)
          url="http://videos.arte.tv"+match[0][0]
          title=date+" - "+cleanTitle(match[0][1])
          entry=entry[entry.find('class="thumbnail"'):]
          match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
          thumb="http://videos.arte.tv"+match[0]
          addLink(title,url,'playVideo',thumb)
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
        listitem = xbmcgui.ListItem(path=urlNew+" swfVfy=1 swfUrl=http://videos.arte.tv/blob/web/i18n/view/player_23-3188338-data-4993762.swf")
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def getUrl(url,data=None,cookie=None):
        if data!=None:
          req = urllib2.Request(url,data)
          req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        else:
          req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
        if cookie!=None:
          req.add_header('Cookie',cookie)
        try:
          response = urllib2.urlopen(req,timeout=30)
          link=response.read()
          response.close()
          return link
        except:
          return ""

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
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'showSortList':
    showSortList(url)
elif mode == 'listShows':
    listShows(url)
elif mode == 'search':
    search()
else:
    index()
