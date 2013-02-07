#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64,socket

socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.audio.booksshouldbefree_com')
translation = addon.getLocalizedString
forceViewMode=addon.getSetting("forceViewMode")
viewMode=str(addon.getSetting("viewMode"))

def index():
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
        addDir(translation(30001),"",'enMain',"")
        content = getUrl("http://www.booksshouldbefree.com/")
        content = content[content.find('<select name="languageselect"'):]
        content = content[content.find('>Select<'):]
        content = content[:content.find('</select>')].replace('<option value="">English</option>','')
        match=re.compile('<option value="(.+?)">(.+?)</option>', re.DOTALL).findall(content)
        for url, title in match:
          addDir(title,"http://www.booksshouldbefree.com/"+url+"?results=100",'listEbooks',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def enMain():
        addDir(translation(30002),"http://www.booksshouldbefree.com/Top_100",'listEbooks',"")
        content = getUrl("http://www.booksshouldbefree.com/")
        content = content[content.find('<select name="genreselect"'):]
        content = content[content.find('>Select<'):]
        content = content[:content.find('</select>')]
        match=re.compile('<option value="(.+?)">(.+?)</option>', re.DOTALL).findall(content)
        for url, title in match:
          addDir(title,"http://www.booksshouldbefree.com/"+url+"?results=100",'listEbooks',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listEbooks(url):
        content = getUrl(url)
        contentPage = content[content.find('<div class="result-pages">'):]
        contentPage = contentPage[:contentPage.find('</ul></div></div>')]
        spl=content.split('<td class="layout2-blue"')
        for i in range(1,len(spl),1):
            entry=spl[i]
            if "alt=" in entry:
              match=re.compile('alt="(.+?)"', re.DOTALL).findall(entry)
              title=match[0]
              title=cleanTitle(title)
              match=re.compile('href="(.+?)"', re.DOTALL).findall(entry)
              url="http://www.booksshouldbefree.com/"+match[0]
              match=re.compile('src="(.+?)"', re.DOTALL).findall(entry)
              thumb="http://www.booksshouldbefree.com/"+match[0]
              addDir(title,url,'listChapters',thumb)
        match=re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(contentPage)
        for url, title in match:
          if title==">":
            addDir(translation(30003),"http://www.booksshouldbefree.com/"+url,'listEbooks',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def listChapters(url):
        content = getUrl(url)
        match=re.compile('<a href="itpc://(.+?)"', re.DOTALL).findall(content)
        content = getUrl("http://"+match[0])
        spl=content.split('<item>')
        for i in range(1,len(spl),1):
            entry=spl[i]
            match=re.compile('<title>(.+?)</title>', re.DOTALL).findall(entry)
            title=match[0]
            title=cleanTitle(title)
            match=re.compile('<link>(.+?)</link>', re.DOTALL).findall(entry)
            url=match[0]
            addLink(title,url,'playAudio',"")
        xbmcplugin.endOfDirectory(pluginhandle)
        if forceViewMode=="true":
          xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playAudio(url):
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def cleanTitle(title):
        title=title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#8217;","'").replace("&#8211;","-").replace("&#039;","'").replace("&quot;","\"").replace("&szlig;","ß").replace("&ndash;","-")
        title=title.replace("&Auml;","Ä").replace("&Uuml;","Ü").replace("&Ouml;","Ö").replace("&auml;","ä").replace("&uuml;","ü").replace("&ouml;","ö")
        title=title.replace("<![CDATA[","").replace("]]>","")
        title=title.strip()
        return title

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:18.0) Gecko/20100101 Firefox/18.0')
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

if mode == 'enMain':
    enMain()
elif mode == 'otherMain':
    otherMain()
elif mode == 'listEbooks':
    listEbooks(url)
elif mode == 'listChapters':
    listChapters(url)
elif mode == 'playAudio':
    playAudio(url)
else:
    index()
