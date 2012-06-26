#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.filmstarts_de')
translation = settings.getLocalizedString

def index():
        addDir('Trailer: '+translation(30001),'http://www.filmstarts.de/trailer/aktuell_im_kino.html?version=1',"showSortDirection",'')
        addDir('Trailer: '+translation(30002),'http://www.filmstarts.de/trailer/bald_im_kino.html?version=1',"showSortDirection",'')
        addDir('Trailer: Archiv','http://www.filmstarts.de/trailer/archiv.html?version=1',"showSortDirection",'')
        addDir('Filmstarts: Fünf Sterne','http://www.filmstarts.de/videos/shows/funf-sterne',"listVideosMagazin",'')
        addDir('Filmstarts: Fehlerteufel','http://www.filmstarts.de/videos/shows/filmstarts-fehlerteufel',"listVideosMagazin",'')
        addDir('Meine Lieblings-Filmszene','http://www.filmstarts.de/videos/shows/meine-lieblings-filmszene',"listVideosMagazin",'')
        addDir('Video-Interviews','http://www.filmstarts.de/trailer/interviews/',"listVideosInterview",'')
        addDir('Serien-Trailer','http://www.filmstarts.de/trailer/serien/',"listVideosTV",'')
        xbmcplugin.endOfDirectory(pluginhandle)

def showSortDirection(url):
        addDir(translation(30003),url.replace("?version=1","?sort_order=0&version=1"),"listVideosTrailer",'')
        addDir(translation(30004),url.replace("?version=1","?sort_order=1&version=1"),"listVideosTrailer",'')
        addDir(translation(30005),url.replace("?version=1","?sort_order=3&version=1"),"listVideosTrailer",'')
        addDir(translation(30006),url.replace("?version=1","?sort_order=2&version=1"),"listVideosTrailer",'')
        xbmcplugin.endOfDirectory(pluginhandle)

def listVideos(urlFull):
        content = getUrl(urlFull)
        currentPage=-1
        maxPage=-1
        try:
          match=re.compile('<span class="navcurrpage">(.+?)</span> / (.+?)</li><li class="navnextbtn">', re.DOTALL).findall(content)
          currentPage=int(match[0][0])
          maxPage=int(match[0][1])
        except:
          try:
            match=re.compile('<em class="current">(.+?)</em></li><li class="navcenterdata"><span class="(.+?)">(.+?)</span>', re.DOTALL).findall(content)
            currentPage=int(match[0][0])
            maxPage=int(match[0][2])
          except:
            pass
        if mode=="listVideosTrailer":
          match=re.compile('<img src=\'(.+?)\' alt="(.+?)" title="(.+?)" />\n</span>\n</div>\n<div class="contenzone">\n<div class="titlebar">\n<a class="link" href="(.+?)">\n<span class=\'bold\'>(.+?)</span>', re.DOTALL).findall(content)
          for thumb,temp1,temp2,url,title in match:
                addLink(title,'http://www.filmstarts.de' + url,"playVideo",thumb)
        elif mode=="listVideosMagazin":
          if currentPage==1:
            match=re.compile('<a href="(.+?)">\n<img src="(.+?)" alt="" />\n</a>\n</div>\n<div style="(.+?)">\n<h2 class="(.+?)" style="(.+?)"><b>(.+?)</b> (.+?)</h2><br />\n<span style="(.+?)" class="purehtml fs11">\n(.+?)<a class="btn" href="(.+?)"', re.DOTALL).findall(content)
            for temp0,thumb,temp1,temp2,temp3,temp4,title,temp5,temp6,url in match:
                  addLink(title,'http://www.filmstarts.de' + url,"playVideo",thumb)
          match=re.compile('<img src=\'(.+?)\' alt="(.+?)" title="(.+?)" />\n</span>\n</div>\n<div class="contenzone">\n<div class="titlebar">\n<a href=\'(.+?)\' class="link">\n<span class=\'bold\'><b>(.+?)</b> (.+?)</span>', re.DOTALL).findall(content)
          for thumb,temp1,temp2,url,temp3,title in match:
                addLink(title,'http://www.filmstarts.de' + url,"playVideo",thumb)
        elif mode=="listVideosInterview":
          match=re.compile('<img src=\'(.+?)\'(.+?)</span>\n</div>\n<div class="contenzone">\n<div class="titlebar">\n<a(.+?)href=\'(.+?)\'>\n<span class=\'bold\'>\n(.+?)\n</span>(.+?)\n</a>', re.DOTALL).findall(content)
          for thumb,temp1,temp2,url,title1,title2 in match:
                addLink(title1+title2,'http://www.filmstarts.de' + url,"playVideo",thumb)
        elif mode=="listVideosTV":
          spl=content.split('<div class="datablock vpadding10b">')
          for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile("<a href='(.+?)'>", re.DOTALL).findall(entry)
            url=match[0]
            match=re.compile("<img src='(.+?)'", re.DOTALL).findall(entry)
            thumb=match[0]
            if entry.find("<span class='bold'>")>=0:
              match=re.compile("<span class='bold'>(.+?)</span>(.+?)<br />", re.DOTALL).findall(entry)
              title=match[0][0]+' '+match[0][1]
            else:
              match=re.compile("<a href='(.+?)'>\n(.+?)<br />", re.DOTALL).findall(entry)
              title=match[0][1]
            addLink(title,'http://www.filmstarts.de' + url,"playVideo",thumb)
        if currentPage<maxPage:
          urlNew=""
          if mode=="listVideosTrailer":
            sortNr=urlFull[urlFull.find('sort_order=')+11:]
            sortNr=sortNr[:sortNr.find('&')]
            urlNew=urlFull[:urlFull.find('?')]+"?page="+str(currentPage+1)+"&sort_order="+sortNr+"&version=1"
          elif urlFull.find('?page=')>=0 and (mode=="listVideosMagazin" or mode=="listVideosInterview" or mode=="listVideosTV"):
            match=re.compile('http://www.filmstarts.de/(.+?)?page=(.+?)', re.DOTALL).findall(urlFull)
            urlNew='http://www.filmstarts.de/'+match[0][0]+'page='+str(currentPage+1)
          elif urlFull.find('?page=')==-1 and (mode=="listVideosMagazin" or mode=="listVideosInterview" or mode=="listVideosTV"):
            urlNew=urlFull + "?page="+str(currentPage+1)
          addDir(translation(30007)+" ("+str(currentPage+1)+")",urlNew,mode,'')
        xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
        content = getUrl(url)
        if url.find("?cmedia=")>=0:
          match=re.compile("cmedia: '(.+?)',\nref: '(.+?)',\ntypeRef: '(.+?)'", re.DOTALL).findall(content)
          media=match[0][0]
          ref=match[0][1]
          typeRef=match[0][2]
        elif url.find("/trailer/")>=0:
          match=re.compile('"cmedia" : (.+?),"ref" : (.+?),"siteKey" : "(.+?)","typeRef" : "(.+?)"', re.DOTALL).findall(content)
          media=match[0][0]
          ref=match[0][1]
          typeRef=match[0][3]
        content = getUrl('http://www.filmstarts.de/ws/AcVisiondata.ashx?media='+media+'&ref='+ref+'&typeref='+typeRef)
        match=re.compile('hd_path="(.+?)"', re.DOTALL).findall(content)
        url=match[0]
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

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

if mode=="playVideo":
    playVideo(url)
elif mode=="showSortDirection":
    showSortDirection(url)
elif mode=="listVideosMagazin" or mode=="listVideosInterview" or mode=="listVideosTV" or mode=="listVideosTrailer":
    listVideos(url)
else:
    index()