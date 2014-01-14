import urllib
import urllib2
import xbmcplugin
import xbmcgui
import xbmcaddon
import os
import re
import string
import sys
from t0mm0.common.addon import Addon
from t0mm0.common.net import Net
import urlresolver


addon = Addon('plugin.video.creationtoday_org', sys.argv)
net = Net()
settings = xbmcaddon.Addon( id = 'plugin.video.creationtoday_org' )
fanart = os.path.join( settings.getAddonInfo( 'path' ), 'fanart.jpg' )
icon = os.path.join( settings.getAddonInfo( 'path' ), 'icon.png' )
xbmc.log('blah'+fanart)
play = addon.queries.get('play', None)


def MAIN():
	addDir('Creation Today Show', 'http://www.creationtoday.org',1,'')	
	addDir('Creation Minute', 'https://www.youtube.com/playlist?list=PLvFrrGonrTSOO8_ZtChPQrBxx4MSla9Qb',2,'')
	addDir('Creation Bytes', 'https://www.youtube.com/playlist?list=PLA2805B73D20F70D3',2,'')
	addDir('Creation Seminars', 'https://www.youtube.com/playlist?list=PL6-cVj-ZRivqKeqAklhYfFFmmAdvwcnCT',2,'')	
	addDir('Debates', 'https://www.youtube.com/playlist?list=PL6-cVj-ZRivpHQhRLUXmLV3nxZ_kWtND-',2,'')	

##################################################################################################################################

def ADDLINKS_Creation_Today(url):
	url='https://www.youtube.com/playlist?list=PLvFrrGonrTSNru0E3AEhBTTAsOvPxK5Q8'
	link = getUrl(url)
	match=re.compile('<a href=.+?watch\?v=(.+?)&amp.+?class="yt-uix-sessionlink"').findall(link)
	title=re.compile('<a href=.+?watch.+?title="(.+?)" class="yt-uix-sessionlink"').findall(link)
	mylist=zip((match),(title))
	for match,title in reversed(mylist):
		thumb = "http://img.youtube.com/vi/"+match+"/0.jpg"
		title=title.replace("&#8211;","-")
		title=title.replace("&#8217;","\'")
		addon.add_video_item({'url': 'http://www.youtube.com/watch?v=' + match},{'title': title},img=thumb,fanart=fanart)
	url='https://www.youtube.com/playlist?list=PLvFrrGonrTSORF70pT4NyrLNVDfWZE4hu'
	link = getUrl(url)
	match=re.compile('<a href=.+?watch\?v=(.+?)&amp.+?class="yt-uix-sessionlink"').findall(link)
	title=re.compile('<a href=.+?watch.+?title="(.+?)" class="yt-uix-sessionlink"').findall(link)
	mylist=zip((match),(title))
	for match,title in reversed(mylist):
		thumb = "http://img.youtube.com/vi/"+match+"/0.jpg"
		title=title.replace("&#8211;","-")
		title=title.replace("&#8217;","\'")
		addon.add_video_item({'url': 'http://www.youtube.com/watch?v=' + match},{'title': title},img=thumb,fanart=fanart)
	url='https://www.youtube.com/playlist?list=PLA5F3E0C0A891053E'
	link = getUrl(url)
	match=re.compile('<a href=.+?watch\?v=(.+?)&amp.+?class="yt-uix-sessionlink"').findall(link)
	title=re.compile('<a href=.+?watch.+?title="(.+?)" class="yt-uix-sessionlink"').findall(link)
	mylist=zip((match),(title))
	for match,title in reversed(mylist):
		thumb = "http://img.youtube.com/vi/"+match+"/0.jpg"
		title=title.replace("&#8211;","-")
		title=title.replace("&#8217;","\'")
		addon.add_video_item({'url': 'http://www.youtube.com/watch?v=' + match},{'title': title},img=thumb,fanart=fanart)

##################################################################################################################################

def ADDLINKS_Youtube_Playlist(url):
	link = getUrl(url)
	match=re.compile('<a href=.+?watch\?v=(.+?)&amp.+?class="yt-uix-sessionlink"').findall(link)
	title=re.compile('<a href=.+?watch.+?title="(.+?)" class="yt-uix-sessionlink"').findall(link)
	mylist=zip((match),(title))
	for match,title in mylist:
		thumb = "http://img.youtube.com/vi/"+match+"/0.jpg"
		title=title.replace("&#8211;","-")
		title=title.replace("&#8217;","\'")
		addon.add_video_item({'url': 'http://www.youtube.com/watch?v=' + match},{'title': title},img=thumb,fanart=fanart)



if play:
	url = addon.queries.get('url', '')
	host = addon.queries.get('host', '')
	media_id = addon.queries.get('media_id', '')
	#stream_url = urlresolver.resolve(play)
	stream_url = urlresolver.HostedMediaFile(url=url, host=host, media_id=media_id).resolve()
	addon.resolve_url(stream_url)

##################################################################################################################################

def getUrl(url):
	req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
	return link

##################################################################################################################################

def get_params():
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


##################################################################################################################################

def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=icon, thumbnailImage=icon)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty( "Fanart_Image", fanart )
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

##################################################################################################################################
        
              
params=get_params()
url=None
name=None
iconimage=None
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
        iconimage=urllib.unquote_plus(params["iconimage"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

xbmc.log("Mode: "+str(mode))
xbmc.log("URL: "+str(url))
xbmc.log("Name: "+str(name))

if mode==None or url==None or len(url)<1:
        xbmc.log ("")
        MAIN()
       
elif mode==1:
        xbmc.log(""+url)
        ADDLINKS_Creation_Today(url)
        
elif mode==2:
        xbmc.log(""+url)
        ADDLINKS_Youtube_Playlist(url)



xbmcplugin.endOfDirectory(int(sys.argv[1]))





