#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonID='plugin.video.ardmediathek_de'
addon = xbmcaddon.Addon(id=addonID)
translation = addon.getLocalizedString
channelFavsFile=xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".favorites")

forceViewMode=addon.getSetting("forceViewMode")
if forceViewMode=="true":
  forceViewMode=True
else:
  forceViewMode=False
viewMode=str(addon.getSetting("viewMode"))

def index():
        addDir(translation(30001),"http://www.ardmediathek.de/ard/servlet/ajax-cache/3516220/view=switch/index.html",'listVideos',"")
        addDir(translation(30002),"http://www.ardmediathek.de/ard/servlet/ajax-cache/3516210/view=list/show=recent/index.html",'listVideos',"")
        addDir(translation(30010),"http://www.ardmediathek.de/ard/servlet/ajax-cache/3516188/view=switch/index.html",'listVideos',"")
        addDir(translation(30003),"http://www.ardmediathek.de/ard/servlet/ajax-cache/3474718/view=switch/index.html",'listVideos',"")
        addDir(translation(30004),"http://www.ardmediathek.de/ard/servlet/ajax-cache/4585472/view=switch/index.html",'listVideos',"")
        addDir(translation(30005),"",'listShowsAZMain',"")
        addDir(translation(30011),"",'listShowsFavs',"")
        addDir(translation(30006),"",'listCats',"")
        addDir(translation(30007),"",'listDossiers',"")
        addDir(translation(30008),"",'search',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listShowsFavs():
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        if os.path.exists(channelFavsFile):
          fh = open(channelFavsFile, 'r')
          all_lines = fh.readlines()
          for line in all_lines:
            title=line[line.find("###TITLE###=")+12:]
            title=title[:title.find("#")]
            url=line[line.find("###URL###=")+10:]
            url=url[:url.find("#")]
            thumb=line[line.find("###THUMB###=")+12:]
            thumb=thumb[:thumb.find("#")]
            addShowFavDir(title,urllib.unquote_plus(url),"listShowVideos",thumb)
          fh.close()
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listDossiers():
        content = getUrl("http://www.ardmediathek.de/ard/servlet/ajax-cache/3516154/view=switch/index.html")
        spl=content.split('<div class="mt-media_item">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<a href="(.+?)"', re.DOTALL).findall(entry)
            url="http://www.ardmediathek.de"+match[0]
            id=url[url.find("documentId=")+11:]
            url="http://www.ardmediathek.de/ard/servlet/ajax-cache/3517004/view=list/documentId="+id+"/goto=1/index.html"
            match=re.compile('<span class="mt-icon mt-icon-toggle_arrows"></span>\n                (.+?)\n', re.DOTALL).findall(entry)
            title=cleanTitle(match[0])
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb="http://www.ardmediathek.de"+match[0]
            addDir(title,url,'listVideosDossier',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listShowVideos(url):
        content = getUrl(url)
        spl=content.split('<div class="mt-media_item">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            if "mt-icon_video" in entry:
              match=re.compile('<a href="(.+?)" class="mt-fo_source" rel="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
              url="http://www.ardmediathek.de"+match[0][0]
              title=cleanTitle(match[0][2])
              match=re.compile('<span class="mt-airtime">\n                    (.+?)\n                    (.+?) min\n            </span>', re.DOTALL).findall(entry)
              duration=""
              if len(match)>0:
                date=match[0][0]
                duration=match[0][1]
                title=date[:5]+" - "+title
              if "00:" in duration:
                duration=1
              match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
              thumb="http://www.ardmediathek.de"+match[0]
              if "Livestream" not in title:
                addLink(title,url,'playVideo',thumb,duration)
        match=re.compile('<a  href="(.+?)" rel="(.+?)"\n         class="(.+?)">(.+?)</a>', re.DOTALL).findall(content)
        for url, temp1, temp2, title in match:
          if title=="Weiter":
            addDir(translation(30009),"http://www.ardmediathek.de"+url,'listShowVideos',"","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listShowsAZMain():
        addDir("0-9","0-9",'listShowsAZ',"")
        letters = [chr(i) for i in xrange(ord('a'), ord('z')+1)]
        for letter in letters:
          addDir(letter.upper(),letter.upper(),'listShowsAZ',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def listShowsAZ(letter):
        content = getUrl("http://www.ardmediathek.de/ard/servlet/ajax-cache/3474820/view=list/initial="+letter+"/index.html")
        spl=content.split('<div class="mt-media_item">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<a href="(.+?)" class="mt-fo_source" rel="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
            url="http://www.ardmediathek.de"+match[0][0]
            id=url[url.find("documentId=")+11:]
            url="http://www.ardmediathek.de/ard/servlet/ajax-cache/3516962/view=list/documentId="+id+"/goto=1/index.html"
            title=cleanTitle(match[0][2])
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb="http://www.ardmediathek.de"+match[0]
            addShowDir(title,url,'listShowVideos',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listCats():
        content = getUrl("http://www.ardmediathek.de/")
        content = content[content.find('<div class="mt-reset mt-categories">'):]
        content = content[:content.find('</div>')]
        match=re.compile('<li><a href="(.+?)" title="">(.+?)</a></li>', re.DOTALL).findall(content)
        for url, title in match:
          id=url[url.find("documentId=")+11:]
          addDir(cleanTitle(title),id,'listVideosMain',"","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideosMain(id):
        addDir(translation(30001),"http://www.ardmediathek.de/ard/servlet/ajax-cache/3516698/view=switch/clipFilter=fernsehen/documentId="+id+"/index.html",'listVideos',"")
        addDir(translation(30002),"http://www.ardmediathek.de/ard/servlet/ajax-cache/3516700/view=list/clipFilter=fernsehen/documentId="+id+"/show=recent/index.html",'listVideos',"")
        addDir(translation(30010),"http://www.ardmediathek.de/ard/servlet/ajax-cache/3516702/view=switch/clipFilter=fernsehen/documentId="+id+"/index.html",'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<div class="mt-media_item">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            if "mt-icon_video" in entry:
              match=re.compile('<a href="(.+?)" class="mt-fo_source" rel="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
              url="http://www.ardmediathek.de"+match[0][0]
              title=cleanTitle(match[0][2])
              match=re.compile('<p class="mt-source mt-tile-view_hide">aus: (.+?)</p>', re.DOTALL).findall(entry)
              show=""
              if len(match)>0:
                show=match[0]
              match=re.compile('<span class="mt-channel mt-tile-view_hide">(.+?)</span>', re.DOTALL).findall(entry)
              channel=""
              if len(match)>0:
                channel=match[0]
              match=re.compile('<span class="mt-airtime">\n                    (.+?)\n                    (.+?) min\n            </span>', re.DOTALL).findall(entry)
              duration=""
              if len(match)>0:
                date=match[0][0]
                duration=match[0][1]
                title=date[:5]+" - "+title
              if "00:" in duration:
                duration=1
              match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
              thumb="http://www.ardmediathek.de"+match[0]
              desc=cleanTitle(date+" - "+show+" ("+channel+")")
              if "Livestream" not in title:
                addLink(title,url,'playVideo',thumb,duration,desc)
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listVideosDossier(url):
        content = getUrl(url)
        spl=content.split('<div class="mt-media_item">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            if 'class="mt-fo_source"' in entry:
              match=re.compile('<a href="(.+?)" class="mt-fo_source" rel="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
              url="http://www.ardmediathek.de"+match[0][0]
              title=cleanTitle(match[0][2])
              match=re.compile('<p class="mt-source mt-tile-view_hide">aus: (.+?)</p>', re.DOTALL).findall(entry)
              show=""
              if len(match)>0:
                show=match[0]
              match=re.compile('<span class="mt-channel mt-tile-view_hide">(.+?)</span>', re.DOTALL).findall(entry)
              channel=""
              if len(match)>0:
                channel=match[0]
              match=re.compile('<span class="mt-airtime">\n                    (.+?)\n                    (.+?) min\n            </span>', re.DOTALL).findall(entry)
              duration=""
              if len(match)>0:
                date=match[0][0]
                duration=match[0][1]
                title=date[:5]+" - "+title
              if "00:" in duration:
                duration=1
              match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
              thumb="http://www.ardmediathek.de"+match[0]
              desc=cleanTitle(date+" - "+show+" ("+channel+")")
              if "Livestream" not in title:
                addLink(title,url,'playVideo',thumb,duration,desc)
        match=re.compile('<a  href="(.+?)" rel="(.+?)"\n         class="(.+?)">(.+?)</a>', re.DOTALL).findall(content)
        for url, temp1, temp2, title in match:
          if title=="Weiter":
            addDir(translation(30009),"http://www.ardmediathek.de"+url,'listVideosDossier',"","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playVideo(url):
        content = getUrl(url)
        match1=re.compile('addMediaStream\\(0, 2, "(.+?)", "(.+?)"', re.DOTALL).findall(content)
        match2=re.compile('addMediaStream\\(0, 2, "", "(.+?)"', re.DOTALL).findall(content)
        match3=re.compile('addMediaStream\\(0, 1, "(.+?)", "(.+?)"', re.DOTALL).findall(content)
        match4=re.compile('addMediaStream\\(0, 1, "", "(.+?)"', re.DOTALL).findall(content)
        url=""
        if len(match2)>0:
          url=match2[0]
        elif len(match1)>0:
          base=match1[0][0]
          if not base.endswith("/"):
            base=base+"/"
          url=base+match1[0][1]
        elif len(match4)>0:
          url=match4[0]
        elif len(match3)>0:
          base=match3[0][0]
          if not base.endswith("/"):
            base=base+"/"
          url=base+match3[0][1]
        if url!="":
          if "?" in url:
            url=url[:url.find("?")]
          listitem = xbmcgui.ListItem(path=cleanUrl(url))
          return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def search():
        keyboard = xbmc.Keyboard('', translation(30008))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
          search_string = keyboard.getText().replace(" ","+")
          listVideosSearch("http://www.ardmediathek.de/suche?detail=40&sort=r&s="+search_string+"&inhalt=tv&goto=1")

def listVideosSearch(url):
        content = getUrl(url)
        spl=content.split('<div class="mt-media_item mt-media-item">')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<a href="(.+?)" class="mt-fo_source" rel="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
            url="http://www.ardmediathek.de"+match[0][0]
            title=cleanTitle(match[0][2])
            match=re.compile('<p class="mt-source mt-tile-view_hide">aus: (.+?)</p>', re.DOTALL).findall(entry)
            show=""
            if len(match)>0:
              show=match[0]
            match=re.compile('<span class="mt-channel mt-tile-view_hide">(.+?)</span>', re.DOTALL).findall(entry)
            channel=""
            if len(match)>0:
              channel=match[0]
            match=re.compile('<span class="mt-airtime">(.+?) · (.+?) min</span>', re.DOTALL).findall(entry)
            duration=""
            if len(match)>0:
              date=match[0][0]
              duration=match[0][1]
              title=date[:5]+" - "+title
            match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
            thumb="http://www.ardmediathek.de"+match[0]
            desc=cleanTitle(date+" - "+show+" ("+channel+")")
            if "Livestream" not in title:
              addLink(title,url,'playVideo',thumb,duration,desc)
        match=re.compile('<a  href="(.+?)"  class="(.+?)" rel="(.+?)">(.+?)</a>', re.DOTALL).findall(content)
        for url, temp1, temp2, title in match:
          if title=="Weiter":
            addDir(translation(30009),"http://www.ardmediathek.de"+url.replace("&amp;","&"),'listVideosSearch',"","")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode==True:
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#034;","\"").replace("&#039;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö").replace("&eacute;","é").replace("&egrave;","è")
        title=title.strip()
        if "(FSK" in title:
          title = title[:title.find(" (FSK")]
        return title

def cleanUrl(title):
        return title.replace("%F6","ö").replace("%FC","ü").replace("%E4","ä").replace("%26","&").replace("%C4","Ä").replace("%D6","Ö").replace("%DC","Ü")

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

def addLink(name,url,mode,iconimage,duration="",desc=""):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Duration": duration, "Plot": desc } )
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

def addShowDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        playListInfos="###MODE###=ADD###TITLE###="+name+"###URL###="+urllib.quote_plus(url)+"###THUMB###="+iconimage+"###END###"
        liz.addContextMenuItems([(translation(30028), 'XBMC.RunScript(special://home/addons/'+addonID+'/favs.py,'+urllib.quote_plus(playListInfos)+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

def addShowFavDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        playListInfos="###MODE###=REMOVE###REFRESH###=TRUE###TITLE###="+name+"###URL###="+urllib.quote_plus(url)+"###THUMB###="+iconimage+"###END###"
        liz.addContextMenuItems([(translation(30029), 'XBMC.RunScript(special://home/addons/'+addonID+'/favs.py,'+urllib.quote_plus(playListInfos)+')',)])
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listChannel':
    listChannel(url)
elif mode == 'listVideos':
    listVideos(url)
elif mode == 'listVideosMain':
    listVideosMain(url)
elif mode == 'listDossiers':
    listDossiers()
elif mode == 'listShowsFavs':
    listShowsFavs()
elif mode == 'listVideosDossier':
    listVideosDossier(url)
elif mode == 'listVideosSearch':
    listVideosSearch(url)
elif mode == 'listShowsAZMain':
    listShowsAZMain()
elif mode == 'listShowsAZ':
    listShowsAZ(url)
elif mode == 'listCats':
    listCats()
elif mode == 'listShowVideos':
    listShowVideos(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'search':
    search()
else:
    index()
