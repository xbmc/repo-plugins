import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.audio.engadget')
__language__ = __settings__.getLocalizedString
__home__ = __settings__.getAddonInfo('path')
picon = xbmc.translatePath( os.path.join( __home__, 'resources/podcast.png' ) )
micon = xbmc.translatePath( os.path.join( __home__, 'resources/mobile.png' ) )
hicon = xbmc.translatePath( os.path.join( __home__, 'resources/hd.png' ) )


def Catagories():
		addDir('Engadget','http://podcasts.engadget.com/rss.xml',1,picon)
		addDir('Engadget Mobile','http://mobile.engadget.com/rss-mp3.xml',1,micon)
		addDir('Engadget HD','http://hd.engadget.com/rss-mp3.xml',1,hicon)


def INDEX(url):
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		link=response.read()
		soup = BeautifulSoup(link)
		episodes = soup('item')
		for episode in episodes:
				try:
						url = episode('enclosure')[0]['url']
						duration = episode('enclosure')[0]('itunes:duration')[0].string[1:]
						date = episode('enclosure')[0]('pubdate')[0].string[:16]
						title = episode('enclosure')[0]('itunes:subtitle')[0].string
						addLink(title+' - '+date,duration,url,picon)
				except:
						pass

	
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


def addLink(name,duration,url,iconimage):
		ok=True
		liz=xbmcgui.ListItem(label = name, iconImage = duration, thumbnailImage=iconimage)
		liz.setInfo( type="audio", infoLabels={ "Title": name ,"Duration":duration } )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
		return ok


def addDir(name,url,mode,iconimage):
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo( type="audio", infoLabels={ "Title": name } )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
		return ok
		
			
params=get_params()
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

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None:
		print ""
		Catagories()
		
if mode==1:
		print ""
		INDEX(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
