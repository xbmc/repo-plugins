#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys

pluginhandle = int(sys.argv[1])

def index():
        addDir('Trailer: Aktuell im Kino','http://www.filmstarts.de/trailer/aktuell_im_kino.html?version=1',1,'')
        addDir('Trailer: Demnächst im Kino','http://www.filmstarts.de/trailer/bald_im_kino.html?version=1',1,'')
        addDir('Trailer: Archiv','http://www.filmstarts.de/trailer/archiv.html?version=1',1,'')
        addDir('Filmstarts: Fünf Sterne','http://www.filmstarts.de/videos/shows/funf-sterne',3,'')
        addDir('Filmstarts: Fehlerteufel','http://www.filmstarts.de/videos/shows/filmstarts-fehlerteufel',3,'')
        addDir('Meine Lieblings-Filmszene','http://www.filmstarts.de/videos/shows/meine-lieblings-filmszene',3,'')
        addDir('Video-Interviews','http://www.filmstarts.de/trailer/interviews/',4,'')
        addDir('Serien-Trailer','http://www.filmstarts.de/trailer/serien/',5,'')
        xbmcplugin.endOfDirectory(pluginhandle)
        if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(50)')

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
        if mode==1:
          match=re.compile('<img src=\'(.+?)\' alt="(.+?)" title="(.+?)" />\n</span>\n</div>\n<div class="contenzone">\n<div class="titlebar">\n<a class="link" href="(.+?)">\n<span class=\'bold\'>(.+?)</span>', re.DOTALL).findall(content)
          for thumb,temp1,temp2,url,title in match:
                addLink(title,'http://www.filmstarts.de' + url,2,thumb)
        elif mode==3:
          if currentPage==1:
            match=re.compile('<a href="(.+?)">\n<img src="(.+?)" alt="" />\n</a>\n</div>\n<div style="(.+?)">\n<h2 class="(.+?)" style="(.+?)"><b>(.+?)</b> (.+?)</h2><br />\n<span style="(.+?)" class="purehtml fs11">\n(.+?)<a class="btn" href="(.+?)"', re.DOTALL).findall(content)
            for temp0,thumb,temp1,temp2,temp3,temp4,title,temp5,temp6,url in match:
                  addLink(title,'http://www.filmstarts.de' + url,2,thumb)
          match=re.compile('<img src=\'(.+?)\' alt="(.+?)" title="(.+?)" />\n</span>\n</div>\n<div class="contenzone">\n<div class="titlebar">\n<a href=\'(.+?)\' class="link">\n<span class=\'bold\'><b>(.+?)</b> (.+?)</span>', re.DOTALL).findall(content)
          for thumb,temp1,temp2,url,temp3,title in match:
                addLink(title,'http://www.filmstarts.de' + url,2,thumb)
        elif mode==4:
          match=re.compile('<img src=\'(.+?)\'(.+?)</span>\n</div>\n<div class="contenzone">\n<div class="titlebar">\n<a(.+?)href=\'(.+?)\'>\n<span class=\'bold\'>\n(.+?)\n</span>(.+?)\n</a>', re.DOTALL).findall(content)
          for thumb,temp1,temp2,url,title1,title2 in match:
                addLink(title1+title2,'http://www.filmstarts.de' + url,2,thumb)
        elif mode==5:
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
            addLink(title,'http://www.filmstarts.de' + url,2,thumb)
        if currentPage<maxPage:
          urlNew=""
          if urlFull.find('?page=')>=0 and mode==1:
            match=re.compile('http://www.filmstarts.de/(.+?)?page=(.+?)&version=1', re.DOTALL).findall(urlFull)
            urlNew='http://www.filmstarts.de/'+match[0][0]+'page='+str(currentPage+1)+'&version=1'
          elif urlFull.find('?page=')>=-1 and mode==1:
            urlNew=urlFull.replace("?version=1","?page="+str(currentPage+1))+"&version=1"
          elif urlFull.find('?page=')>=0 and (mode==3 or mode==4 or mode==5):
            match=re.compile('http://www.filmstarts.de/(.+?)?page=(.+?)', re.DOTALL).findall(urlFull)
            urlNew='http://www.filmstarts.de/'+match[0][0]+'page='+str(currentPage+1)
          elif urlFull.find('?page=')>=-1 and (mode==3 or mode==4 or mode==5):
            urlNew=urlFull + "?page="+str(currentPage+1)
          addDir('Next Page',urlNew,mode,'')
        xbmcplugin.endOfDirectory(pluginhandle)
        if (xbmc.getSkinDir() == "skin.confluence" or xbmc.getSkinDir() == "skin.touched"): xbmc.executebuiltin('Container.SetViewMode(500)')

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
url=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass


if mode==None or url==None or len(url)<1:
        index()
       
elif mode==2:
        playVideo(url)
else:
        listVideos(url)
