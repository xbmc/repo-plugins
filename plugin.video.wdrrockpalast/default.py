import urllib, urllib2, re, xbmcplugin, xbmcaddon, xbmcgui, xbmc, os
from HTMLParser import HTMLParser



# WDR Rockpalast by xycl

def showConcerts():
        req = urllib2.Request('http://www.wdr.de/tv/rockpalast/videos/uebersicht.jsp')
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<li><a href="([^"]+)">(.*?)</a></li>').findall(link)
	
        for url,name in match:
                addDir( HTMLParser().unescape(name), 'HTTP://www.wdr.de'+url,1,'HTTP://www.wdr.de/tv/rockpalast/codebase/img/audioplayerbild_512x288.jpg')
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        
def playVideo(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        video_url=re.compile('dslSrc=([^&]+?)&amp;').findall(link)
        title_url=re.compile('<title>([^-]+?)- Rockpalast').findall(link)
        xbmc.Player().play(video_url[0])

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

def addDir(name,url,mode,iconimage):
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

#print "Mode: "+str(mode)
#print "URL: "+str(url)
#print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
        print ""
        showConcerts()
       
elif mode==1:
        print ""+url
        playVideo(url)


