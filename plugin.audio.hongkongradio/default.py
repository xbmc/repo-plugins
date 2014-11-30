#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64

pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.audio.hongkongradio')
translation = addon.getLocalizedString

def index():
        li = xbmcgui.ListItem(translation(30001), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/881.png')
        url = 'http://s06.hktoolbar.com/radio-HTTP/cr1-hd.3gp/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)
        li = xbmcgui.ListItem(translation(30002), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/903.png')
        url = 'http://s06.hktoolbar.com/radio-HTTP/cr2-hd.3gp/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)
        li = xbmcgui.ListItem(translation(30003), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/864.png')
        url = 'http://s06.hktoolbar.com/radio-HTTP/cr2-hd.3gp/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)     
        li = xbmcgui.ListItem(translation(30011), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/radio1.png')
        url = 'http://stmw2.rthk.hk/live/smil:radio1_aac_1.smil/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)     
        li = xbmcgui.ListItem(translation(30012), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/radio2.png')
        url = 'http://stmw2.rthk.hk/live/smil:radio2_aac_1.smil/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)   
        li = xbmcgui.ListItem(translation(30013), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/radio3.png')
        url = 'http://stmw2.rthk.hk/live/smil:radio3_aac_1.smil/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)   
        li = xbmcgui.ListItem(translation(30014), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/radio4.png')
        url = 'http://stmw2.rthk.hk/live/smil:radio4_aac_1.smil/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)   
        li = xbmcgui.ListItem(translation(30015), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/radio5.png')
        url = 'http://stmw2.rthk.hk/live/smil:radio5_aac_1.smil/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)   
        li = xbmcgui.ListItem(translation(30016), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/pth.png')
        url = 'http://stmw3.rthk.hk/live/smil:pth_aac_1.smil/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)   
        li = xbmcgui.ListItem(translation(30017), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/dab31.png')
        url = 'http://stmw2.rthk.hk/live/smil:dab31_aac_1.smil/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)   
        li = xbmcgui.ListItem(translation(30018), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/dab33.png')
        url = 'http://stmw2.rthk.hk/live/smil:dab33_aac_1.smil/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)   
        li = xbmcgui.ListItem(translation(30019), iconImage='special://home/addons/plugin.audio.hongkongradio/resources/media/dab35.png')
        url = 'http://stmw2.rthk.hk/live/smil:dab35_aac_1.smil/playlist.m3u8'
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=li)   
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

def playAudioList(id):
        listitem = xbmcgui.ListItem(path=id)
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
