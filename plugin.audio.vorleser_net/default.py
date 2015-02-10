#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64

pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.audio.vorleser_net')
translation = addon.getLocalizedString

def index():
        addDir(translation(30001),"","listAllAuthors","")
        addDir("Krimi & Spannung","Krimi_kUND_Spannung","listCatBooks","")
        addDir("Kinder & Jugendliche","Kinder_kUND_Jugendliche","listCatBooks","")
        addDir("Romane & Erzählungen","Romane_kUND_Erzaehlungen","listCatBooks","")
        addDir("Philosophie & Religion","Philosophie_kUND_Religion","listCatBooks","")
        addDir("Hörspiele & Bühne","Hoerspiel_kUND_Buehne","listCatBooks","")
        addDir("Lyrik & Musik","Lyrik_kUND_Poesie","listCatBooks","")
        addDir("Sachtexte & Essays","Sachtexte_kUND_Essays","listCatBooks","")
        xbmcplugin.endOfDirectory(pluginhandle)

def listAllAuthors():
        content = getUrl("http://www.vorleser.net/alle_autoren.php")
        match=re.compile('<a href="autor.php\\?id=(.+?)" name="(.+?)" class="rel pointer" onclick="setDetail\\(this\\)">(.+?)<br></a>', re.DOTALL).findall(content)
        for id, temp, author in match:
          addDir(cleanTitle(author),id,'listBooks',"")
        xbmcplugin.endOfDirectory(pluginhandle)

def listCatBooks(id):
        content = getUrl("http://www.vorleser.net/hoerbuch.php?kat="+id)
        spl=content.split('<div class="box news')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<div class="autor">(.+?)</div>', re.DOTALL).findall(entry)
            author=match[0]
            match=re.compile('<div class="h2 orange fieldH2">(.+?)</div>', re.DOTALL).findall(entry)
            title=author+": "+match[0]
            title=cleanTitle(title)
            match=re.compile('<a href="hoerbuch.php\\?id=(.+?)"', re.DOTALL).findall(entry)
            id=match[0]
            match=re.compile('background-image:url\\((.+?)\\)', re.DOTALL).findall(entry)
            thumb=""
            if len(match)>0:
              thumb="http://www.vorleser.net/"+match[0]
            addLink(title,id,'playAudio',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)

def listBooks(id):
        content = getUrl("http://www.vorleser.net/autor.php?id="+id)
        spl=content.split('<div class="box news"')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<div class="h2 orange" style="(.+?)">(.+?)</div>', re.DOTALL).findall(entry)
            title=match[0][1]
            title=cleanTitle(title)
            match=re.compile('<a href="hoerbuch.php\\?id=(.+?)"', re.DOTALL).findall(entry)
            id=match[0]
            match=re.compile('background-image:url\\((.+?)\\)', re.DOTALL).findall(entry)
            thumb=""
            if len(match)>0:
              thumb="http://www.vorleser.net/"+match[0]
            addLink(title,id,'playAudio',thumb)
        xbmcplugin.endOfDirectory(pluginhandle)

def playAudio(id):
        listitem = xbmcgui.ListItem(path="http://www.vorleser.net/audio/"+id+".mp3")
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

if mode == 'listBooks':
    listBooks(url)
elif mode == 'listCatBooks':
    listCatBooks(url)
elif mode == 'listAllAuthors':
    listAllAuthors()
elif mode == 'playAudio':
    playAudio(url)
else:
    index()
