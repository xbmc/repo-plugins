#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.dtm_tv')
translation = settings.getLocalizedString

language=""
language=settings.getSetting("language")
if language=="":
  settings.openSettings()
  language=settings.getSetting("language")

if language=="0":
  language="DE"
elif language=="1":
  language="EN"

def cleanTitle(title):
        return title.replace("\\u00c4","Ä").replace("\\u00e4","ä").replace("\\u00d6","Ö").replace("\\u00f6","ö").replace("\\u00dc","Ü").replace("\\u00fc","ü").replace("\\u00df","ß").strip()

def index():
        addDir(translation(30001),"LATEST","listVideos","")
        addDir(translation(30002),"MOST_VIEWED","listVideos","")
        addDir(translation(30003),"BEST_RATED","listVideos","")
        addDir(translation(30004),"SEARCH","listVideos","")
        xbmcplugin.endOfDirectory(pluginhandle)

def listVideos(url):
        values = {}
        if url=="LATEST":
          values = {'string':'*',
                    'lang':language,
                    'page':'1',
                    'order':'date'}
        elif url=="MOST_VIEWED":
          values = {'string':'*',
                    'lang':language,
                    'page':'1',
                    'order':'views'}
        elif url=="BEST_RATED":
          values = {'string':'*',
                    'lang':language,
                    'page':'1',
                    'order':'ranking'}
        elif url=="SEARCH":
          keyboard = xbmc.Keyboard('', translation(30004))
          keyboard.doModal()
          if keyboard.isConfirmed() and keyboard.getText():
            search_string = keyboard.getText()
            values = {'string':search_string,
                      'lang':language,
                      'page':'1',
                      'order':'date'}
        if len(values)>0:
          data = urllib.urlencode(values)
          listVideosMain(data)

def listVideosMain(url):
        content = getUrl("http://www.dtm.tv/Daten/getSearchData",data=url)
        
        spl=content.split('{"id":')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('"bild":"(.+?)"', re.DOTALL).findall(entry)
            thumb="http://www.dtm.tv/media/images/"+match[0]
            match=re.compile('"publishdate":"(.+?)"', re.DOTALL).findall(entry)
            date=match[0]
            match=re.compile('"title":"(.+?)"', re.DOTALL).findall(entry)
            title=date+" - "+cleanTitle(match[0])
            
            urls=[]
            match=re.compile('"url1":"(.+?)"', re.DOTALL).findall(entry)
            if len(match)==1:
              urls.append(match[0].replace("\\",""))
            match=re.compile('"url2":"(.+?)"', re.DOTALL).findall(entry)
            if len(match)==1:
              urls.append(match[0].replace("\\",""))
            match=re.compile('"url3":"(.+?)"', re.DOTALL).findall(entry)
            if len(match)==1:
              urls.append(match[0].replace("\\",""))
            
            urlNew=""
            for urlTemp in urls:
              if urlTemp.find("_HD.mp4")>=0:
                urlNew=urlTemp
              elif urlTemp.find("_SD.mp4")>=0:
                if urlNew=="":
                  urlNew=urlTemp
              elif urlTemp.find(".flv")>=0:
                if urlNew=="":
                  urlNew=urlTemp
            
            addLink(title,urlNew,'playVideo',thumb)
        
        match=re.compile('"nextPage":(.+?),', re.DOTALL).findall(content)
        if len(match)==1:
          dataNext=url[:url.find("page=")+5]+match[0]
          temp=url[url.find("page=")+5:]
          if temp.find("&")>=0:
            dataNext=dataNext+url[:url.find("&")+1]
          
          addDir("Next Page ("+str(match[0])+")",dataNext,"listVideosMain","")
        xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
        listitem = xbmcgui.ListItem(path=url)
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
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'listVideosMain':
    listVideosMain(url)
else:
    index()
