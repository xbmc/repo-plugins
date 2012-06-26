#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])

settings = xbmcaddon.Addon(id='plugin.video.sueddeutsche_de')
translation = settings.getLocalizedString

def index():
        addDir(translation(30001),"http://rss.sueddeutsche.de/query/%23/sort/-docdatetime/drilldown/%C2%A7documenttype%3AVideo",'listVideos',"")
        addDir(translation(30002),"http://rss.sueddeutsche.de/query/%23/nav/%C2%A7documenttype%3AVideo/sort/-docdatetime/drilldown/%C2%A7ressort%3A%5EPanorama%24",'listVideos',"")
        addDir(translation(30003),"http://rss.sueddeutsche.de/query/%23/nav/%C2%A7documenttype%3AVideo/sort/-docdatetime/drilldown/%C2%A7ressort%3A%5EPolitik%24",'listVideos',"")
        addDir(translation(30004),"http://rss.sueddeutsche.de/query/%23/nav/%C2%A7documenttype%3AVideo/sort/-docdatetime/drilldown/%C2%A7ressort%3A%5ESport%24",'listVideos',"")
        addDir(translation(30005),"http://rss.sueddeutsche.de/query/%23/nav/%C2%A7documenttype%3AVideo/sort/-docdatetime/drilldown/%C2%A7ressort%3A%5EKultur%24",'listVideos',"")
        addDir(translation(30006),"http://rss.sueddeutsche.de/query/%23/nav/%C2%A7documenttype%3AVideo/sort/-docdatetime/drilldown/%C2%A7ressort%3A%5EWirtschaft%24",'listVideos',"")
        addDir(translation(30007),"http://rss.sueddeutsche.de/query/%23/nav/%C2%A7documenttype%3AVideo/sort/-docdatetime/drilldown/%C2%A7ressort%3A%5ELeben%24",'listVideos',"")
        addDir(translation(30008),"",'listColumns',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def listColumns():
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        addDir("Rasenschach - Die EM Taktikkolumne","http://www.sueddeutsche.de/thema/Taktik-Kolumne",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/rasenschach.jpg")
        addDir("Der Nächste, bitte","http://www.sueddeutsche.de/thema/Der_N%C3%A4chste_bitte",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/der_naechste_bitte.jpg")
        addDir("Prantls Politik","http://www.sueddeutsche.de/thema/Prantls_Politik",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/prantl.jpg")
        addDir("Global betrachtet","http://www.sueddeutsche.de/thema/global_betrachtet",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/global_betrachtet.jpg")
        addDir("Summa summarum","http://www.sueddeutsche.de/thema/Summa_Summarum",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/summa_summarum.jpg")
        addDir("Zoom - Die Kinopremiere","http://www.sueddeutsche.de/thema/zoom_-_Die_Kinopremiere",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/zoom.gif")
        addDir("Augsteins Auslese","http://www.sueddeutsche.de/thema/Augsteins_Auslese",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/schloemann_augstein.gif")
        addDir("Schloemanns Auslese","http://www.sueddeutsche.de/thema/Schloemanns_Auslese",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/schloemann_augstein.gif")
        addDir("Münchner Mysterien","http://www.sueddeutsche.de/thema/M%C3%BCnchner_Mysterien",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/muenchner_mysterien.gif")
        addDir("Aktenlage","http://www.sueddeutsche.de/thema/Aktenlage",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/aktenlage.gif")
        addDir("Der Flügelflitzer","http://www.sueddeutsche.de/thema/Fl%C3%BCgelflitzer",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/fluegelflitzer.jpg")
        addDir("2 mal 2 - Der Fußball Schlagabtausch","http://www.sueddeutsche.de/thema/2_mal_2",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/2x2.jpg")
        addDir("Auftakt","http://www.sueddeutsche.de/thema/Auftakt",'listColumnVideos',"http://gfx.sueddeutsche.de/video/kolumnen/auftakt.jpg")
        xbmcplugin.endOfDirectory(pluginhandle)

def listColumnVideos(url):
        content = getUrl(url)
        spl=content.split("<li class='hentry")
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('<a href="(.+?)"', re.DOTALL).findall(entry)
          url=match[0]
          match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
          thumb=match[0]
          match=re.compile('</span>\n	      (.+?)\n', re.DOTALL).findall(entry)
          title=match[0]
          title=cleanTitle(title)
          addLink(title,url,'playVideo',thumb)
        content=content[content.find('class="offscreen">Pagination</p>'):]
        match=re.compile('<li><a href="(.+?)" rel="next">', re.DOTALL).findall(content)
        if len(match)>0:
          addDir(translation(30009),match[0],'listColumnVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def listVideos(url):
        content = getUrl(url)
        spl=content.split('<li class="hentry">')
        for i in range(2,len(spl),1):
          entry=spl[i]
          match=re.compile('<a href="(.+?)"', re.DOTALL).findall(entry)
          url=match[0]
          match=re.compile('<img src="(.+?)"', re.DOTALL).findall(entry)
          thumb=match[0]
          match=re.compile('</span>(.+?)<', re.DOTALL).findall(entry)
          title=match[0]
          match=re.compile('<p class="entry-summary">\n              (.+?) ', re.DOTALL).findall(entry)
          date=match[0]
          date=date[:6]
          title=cleanTitle(title)
          addLink(date+" "+title,url,'playVideo',thumb)
        match=re.compile('<li class="next">\n          	<a href="(.+?)"', re.DOTALL).findall(content)
        if len(match)>0:
          addDir(translation(30009),"http://rss.sueddeutsche.de"+match[0],'listVideos',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
        try:
          content = getUrl(url)
          match=re.compile('"video"      : "(.+?)"', re.DOTALL).findall(content)
          if len(match)>0:
            listitem = xbmcgui.ListItem(path=match[0])
            return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        except:
          pass

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.strip()
        return title

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
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listColumns':
    listColumns()
elif mode == 'listColumnVideos':
    listColumnVideos(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
