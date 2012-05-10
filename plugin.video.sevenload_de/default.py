#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.sevenload_de')
translation = settings.getLocalizedString

def index():
        content = getUrl("http://de.sevenload.com/")
        match=re.compile('<a href="/kanaele/(.+?)" class="clearfix"><em>(.+?)</em><span>(.+?)</span>', re.DOTALL).findall(content)
        addDir(translation(30001),"http://de.sevenload.com/sendungen/all",9,'')
        for url,temp,title in match:
          addDir("  "+title,"http://de.sevenload.com/kanaele/"+url,1,'')
        addDir(translation(30002),"___NEW___1",8,"")
        addDir(translation(30003),"___NEW___2",8,"")
        xbmcplugin.endOfDirectory(pluginhandle)

def search(url):
        content = getUrl(url)
        content = content[content.find('<div class="overlayWhileAdding"'):]
        match=re.compile('<div class="mediaItem"><div><a href="(.+?)"><img src="(.+?)" width="(.+?)" height="(.+?)" alt="" title="(.+?)"', re.DOTALL).findall(content)
        for url,thumb,temp1,temp2,title in match:
                addLink(title,url,5,thumb)
        match=re.compile('<a title="Zur n(.+?)chsten Seite" href="(.+?)"', re.DOTALL).findall(content)
        if len(match)>0:
          url="http://de.sevenload.com"+match[0][1]
          addDir("Next Page",url,8,'')
        xbmcplugin.endOfDirectory(pluginhandle)

def searchHelper(url):
        if url.find("___NEW___")==0:
          if url=="___NEW___1":
            type="kanaele"
          elif url=="___NEW___2":
            type="videos"
          keyboard = xbmc.Keyboard('', 'Video Suche')
          keyboard.doModal()
          if keyboard.isConfirmed() and keyboard.getText():
            search_string = keyboard.getText()
            search("http://de.sevenload.com/suche/"+search_string+"/"+type+"/kacheln/relevanteste/1")
        else:
          search(url)

def mainChannel(url):
        content = getUrl(url)
        match=re.compile('<title>Kanal - (.+?) - sevenload</title>', re.DOTALL).findall(content)
        cat=match[0]
        content = content[content.find("</a><ul><li >"):]
        match=re.compile('<a href="/kanaele/(.+?)" class="clearfix"><span>(.+?)</span>', re.DOTALL).findall(content)
        addDir("Alle Sendungen ("+cat+")",url,2,'')
        for url,title in match:
                addDir("  "+title,"http://de.sevenload.com/kanaele/"+url,2,'')
        xbmcplugin.endOfDirectory(pluginhandle)

def channel(url):
        if url.find("filter=name")==-1:
          content = getUrl(url+"?filter=name")
        else:
          content = getUrl(url)
        newContent=content[content.find('<ul class="teaserList uoBoxToggleContent">'):content.find('</div> </div> </li> </ul>')]
        spl=newContent.split("<li")
        for i in range(1,len(spl),1):
            entry=spl[i]
            entry2=entry[entry.find("<h2>"):]
            match=re.compile('<a href="(.+?)">(.+?) <span>', re.DOTALL).findall(entry2)
            url=match[0][0]
            title=match[0][1]
            if title.find("<abbr title=")>=0:
              match=re.compile('<abbr title="(.+?)">', re.DOTALL).findall(title)
              title=match[0]
            match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
            thumb=""
            if len(match)>0:
              thumb=match[0]
            addDir(title,url,3,thumb)
        match=re.compile('<a title="Zur n(.+?)chsten Seite" href="(.+?)" onclick=', re.DOTALL).findall(content)
        if len(match)>0:
          url="http://de.sevenload.com"+match[0][1]
          url=url.replace("&amp;","&")
          addDir("Next Page",url,2,'')
        xbmcplugin.endOfDirectory(pluginhandle)

def allShows(url):
        content = getUrl(url)
        match=re.compile('<a href="http://de.sevenload.com/sendungen/(.+?)">(.+?)</a>', re.DOTALL).findall(content)
        for url,title in match:
                addDir(title.replace('<span class="new">Neues Video</span>','').strip(),"http://de.sevenload.com/sendungen/"+url,3,'')
        xbmcplugin.endOfDirectory(pluginhandle)

def show(url):
        content = getUrl(url+"/folgen")
        content = content[content.find('<div id="showContentWrapper">'):]
        match=re.compile('<h2>(.+?)</h2> <div class="albumContent">(.+?)<div id="album_(.+?)">', re.DOTALL).findall(content)
        spl=url.split("/")
        sendungTitle = spl[len(spl)-1]
        if len(match)>1:
          for title,temp,id in match:
                if title.find("onclick=")>=0:
                  match2=re.compile('\'\\)">(.+?)</a>', re.DOTALL).findall(title)
                  title=match2[0]
                addDir(title,"http://de.sevenload.com/sendungen/"+sendungTitle+"/alben/"+id+"?pageLength=50&orderBy=latest&page=1",4,'')
          xbmcplugin.endOfDirectory(pluginhandle)
        elif len(match)==1:
          id=match[0][2]
          content = getUrl("http://de.sevenload.com/sendungen/"+sendungTitle+"/alben/"+id+"?pageLength=50&orderBy=latest&page=1")
          match2=re.compile('<a title="Zur n(.+?)chsten Seite" href="(.+?)" onclick=', re.DOTALL).findall(content)
          content = content[content.find('<div class="overlayWhileAdding"'):]
          match=re.compile('<a href="(.+?)" class="episodeScreenshot uoOmnitureOnclick" title="Video abspielen \'(.+?)\'"> <img src="(.+?)"', re.DOTALL).findall(content)
          for url,title,thumb in match:
                  addLink(title,url,5,thumb)
          if len(match2)>0:
            url="http://de.sevenload.com"+match2[0][1]
            url=url.replace("&amp;","&")
            addDir("Next Page",url,4,'')
          xbmcplugin.endOfDirectory(pluginhandle)

def album(url):
        content = getUrl(url)
        match2=re.compile('<a title="Zur n(.+?)chsten Seite" href="(.+?)" onclick=', re.DOTALL).findall(content)
        content = content[content.find('<div class="overlayWhileAdding"'):]
        match=re.compile('<a href="(.+?)" class="episodeScreenshot uoOmnitureOnclick" title="Video abspielen \'(.+?)\'"> <img src="(.+?)"', re.DOTALL).findall(content)
        for url,title,thumb in match:
                addLink(title,url,5,thumb)
        if len(match2)>0:
          url="http://de.sevenload.com"+match2[0][1]
          url=url.replace("&amp;","&")
          addDir("Next Page",url,4,'')
        xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
        if url.find("/folgen/")>=0:
          match=re.compile('/folgen/(.+?)-', re.DOTALL).findall(url)
          id=match[0]
        elif url.find("/videos/")>=0:
          match=re.compile('/videos/(.+?)-', re.DOTALL).findall(url)
          id=match[0]
          id=id[:(len(id)-1)]
        content = getUrl("http://flash.sevenload.com/player?itemId="+id+"&portalId=de&screenlink=0&pwidth=645&pheight=364&environment=episode&hide_auto_play=1")
        if content.find('<stream quality="high"')>=0:
          match=re.compile('<stream quality="high"(.+?)<location seeking="yes">(.+?)</location>', re.DOTALL).findall(content)
          url=match[0][1]
        elif content.find('<stream quality="normal"')>=0:
          match=re.compile('<stream quality="normal"(.+?)<location seeking="yes">(.+?)</location>', re.DOTALL).findall(content)
          url=match[0][1]
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        
def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
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
       
elif mode==1:
        mainChannel(url)
elif mode==2:
        channel(url)
elif mode==3:
        show(url)
elif mode==4:
        album(url)
elif mode==5:
        playVideo(url)
elif mode==8:
        searchHelper(url)
elif mode==9:
        allShows(url)
