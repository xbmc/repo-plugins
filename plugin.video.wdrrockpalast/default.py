#!/usr/bin/python
# -*- coding: utf8 -*-

""" 
WDR Rockpalast
Copyright (C) 2012 Xycl

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""




# os imports
import urllib, urllib2, re
# xbmc imports
import xbmcplugin, xbmcgui, xbmc



def showConcerts():
        req = urllib2.Request('http://www.wdr.de/tv/rockpalast/videos/uebersicht.jsp')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<li><a href="([^"]+)">(.*?)</a></li>').findall(link)
	
        for url,name in match:
                name = name.decode('ISO-8859-1').encode('utf-8')
                addDir(urllib.unquote_plus(name), 'HTTP://www.wdr.de'+url, 1, 'HTTP://www.wdr.de/tv/rockpalast/codebase/img/audioplayerbild_512x288.jpg')
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
def playVideo(url, name):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        video_url=re.compile('dslSrc=([^&]+?)&amp;').findall(link)
        url = urllib.unquote_plus(video_url[0])
        
        if len(name)>2:
            title = name
        else:
            title_url=re.compile('<title>(.+?)- Rockpalast').findall(link)
            
            try:
                title = urllib.unquote_plus(title_url[0])
            except:
                title = 'unnamed'
        
        listitem = xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage='HTTP://www.wdr.de/tv/rockpalast/codebase/img/audioplayerbild_512x288.jpg')
        listitem.setInfo('video', {'Title': title})
        xbmc.Player(xbmc.PLAYER_CORE_AUTO).play( url, listitem)       

def getParams():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                                
        return param

def addDir(name, url, mode, iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
        return ok
        
              
params=getParams()
url=None
name=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass


if mode==None or url==None or len(url)<1:
        showConcerts()
       
elif mode==1:
        playVideo(url, name)


