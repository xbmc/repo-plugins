#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64

pluginhandle = int(sys.argv[1])

def index():
        content = getUrl("http://www.vorleser.net/html/autoren.html")
        content = content[content.find("Autoren</B></P>"):]
        content = content[:content.find('<TR STYLE="height: 32px;">')]
        spl=content.split('<TR VALIGN="TOP"')
        for i in range(1,len(spl),1):
          entry=spl[i]
          match=re.compile('<A HREF="(.+?)">(.+?)</A>', re.DOTALL).findall(entry)
          for url, author in match:
            if url.find("../")==0:
              addDir(cleanTitle(author),url.replace("../","http://www.vorleser.net/"),'listAuthor',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def listAuthor(url):
        content = getUrl(url)
        match=re.compile('HREF="http://xoup.de/audio/(.+?).mp3"', re.DOTALL).findall(content)
        for url in match:
          spl=url.split('/')
          title=spl[len(spl)-1]
          url="http://xoup.de/audio/"+url+".mp3"
          addLink(title,url,'playAudio',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def playAudio(url):
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","\\").replace("&#263;","c").replace("&#269;","c").replace("&#273;","d").replace("&#8220;","\"").replace("&#8221;","\"").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.replace('<SPAN STYLE="font-family: Arial,Helvetica,Geneva,Sans-serif;">',"").replace("</SPAN>","")
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

if mode == 'listAuthors':
    listAuthors(url)
elif mode == 'listAuthor':
    listAuthor(url)
elif mode == 'playAudio':
    playAudio(url)
else:
    index()
