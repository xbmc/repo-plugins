import urllib,urllib2,re,xbmcplugin,xbmcgui,day9,sys,os,xbmc

Day = day9.Day9()

params=Day.get_params()
url=None
mode=None
Name=None
duration=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        duration=urllib.unquote_plus(params["duration"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

if mode==None or url==None or len(url)<1:
    Day.categories() 
if mode==2:
    Day.index(url)  
if mode==3:
    Day.videolinks(url,name,duration) 	
	
xbmcplugin.endOfDirectory(int(sys.argv[1]))