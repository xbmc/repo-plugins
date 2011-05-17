import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.foodnetwork')
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )


def getShows():
		req = urllib2.Request('http://www.foodnetwork.com/food-network-full-episodes/videos/index.html')
		req.addheaders = [('Referer', 'http://www.foodnetwork.com'),
				('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0) Gecko/20100101 Firefox/4.0')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		shows = soup.find('ul', attrs={'class' : "playlists"})('li')
		for show in shows:
				name = show('a')[0].string
				url = show['data-channel']
				addDir(name,url,1,icon)
		addDir('Top Videos - Clips','',4,icon)
		addDir('More Shows - Clips','',2,icon)
		
		
def getTopVideos():
		req = urllib2.Request('http://www.foodnetwork.com/food-network-top-food-videos/videos/index.html')
		req.addheaders = [('Referer', 'http://www.foodnetwork.com'),
				('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0) Gecko/20100101 Firefox/4.0')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		shows = soup.find('ul', attrs={'class' : "playlists"})('li')
		for show in shows:
				name = show('a')[0].string
				url = show['data-channel']
				addDir(name,url,1,icon)

def getShowClips():
		req = urllib2.Request('http://www.foodnetwork.com/shows/index.html')
		req.addheaders = [('Referer', 'http://www.foodnetwork.com'),
				('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0) Gecko/20100101 Firefox/4.0')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		shows = soup.find('div', attrs={'class' : "list-wrap"})('ul')[0]('li')
		del shows[1];del shows[6:7];del shows[7];del shows[8];del shows[16];del shows[20];del shows[24];del shows[25:27];del shows[26:29];del shows[30:33]
		del shows[31:33];del shows[32:35];del shows[33];del shows[34];del shows[36:44];del shows[39];del shows[41:43];del shows[43];del shows[44];del shows[49:51]
		del shows[53:57];del shows[-1]
		for show in shows:
				name = show('a')[0].string
				link = show('a')[0]['href']
				addDir(name,link,3,icon)
		
def index(url):
		req = urllib2.Request('http://www.foodnetwork.com/food/channel/xml/0,,'+url+',00.xml')
		req.addheaders = [('Referer', 'http://www.hgtv.com'),
				('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0) Gecko/20100101 Firefox/4.0')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		videos = soup('video')
		for video in videos:
				name = video('clipname')[0].string
				length = video('length')[0].string
				thumb = video('thumbnailurl')[0].string
				description = video('abstract')[0].string
				link = video('videourl')[0].string
				playpath = link.replace('http://wms.scrippsnetworks.com','').replace('.wmv','')
				url = 'rtmp://flash.scrippsnetworks.com:1935/ondemand?ovpfv=1.1 swfUrl="http://common.scrippsnetworks.com/common/snap/snap-3.0.3.swf" playpath='+playpath
				addLink(name,url,description,length,thumb)


def indexShowClips(url):
		url='http://www.foodnetwork.com'+url
		req = urllib2.Request(url)
		req.addheaders = [('Referer', 'http://www.foodnetwork.com'),
				('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0) Gecko/20100101 Firefox/4.0')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		showID=re.compile("snap = new SNI.Food.Player.FullSize\(\\'vplayer-1\\',\\'(.+?)\\'\)").findall(link)
		if len(showID)<1:
				showID=re.compile("snap = new SNI.Food.Player.FullSize\(\\'vid-player\\', (.+?)\)").findall(link)
		if len(showID)<1:
				try:
						url = soup.findAll('ul', attrs={'class' : "tabnav clrfix"})[0]('a')[-1]['href']
				except:
						print '-------->video not found'
						return
				url='http://www.foodnetwork.com'+url
				req = urllib2.Request(url)
				req.addheaders = [('Referer', 'http://www.foodnetwork.com'),
						('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0) Gecko/20100101 Firefox/4.0')]
				response = urllib2.urlopen(req)
				link=response.read()
				response.close()
				showID=re.compile("snap = new SNI.Food.Player.FullSize\(\\'vplayer-1\\',\\'(.+?)\\'\)").findall(link)
				if len(showID)<1:
						showID=re.compile("snap = new SNI.Food.Player.FullSize\(\\'vid-player\\', (.+?)\)").findall(link)
				if len(showID)<1:
						print '--------->video not found'
						return
		print'--------> '+showID[0]
		req = urllib2.Request('http://www.foodnetwork.com/food/channel/xml/0,,'+showID[0]+',00.xml')
		req.addheaders = [('Referer', 'http://www.hgtv.com'),
				('Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0) Gecko/20100101 Firefox/4.0')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		videos = soup('video')
		for video in videos:
				name = video('clipname')[0].string
				length = video('length')[0].string
				thumb = video('thumbnailurl')[0].string
				description = video('abstract')[0].string
				link = video('videourl')[0].string
				playpath = link.replace('http://wms.scrippsnetworks.com','').replace('.wmv','')
				url = 'rtmp://flash.scrippsnetworks.com:1935/ondemand?ovpfv=1.1 swfUrl="http://common.scrippsnetworks.com/common/snap/snap-3.0.3.swf" playpath='+playpath
				addLink(name,url,description,length,thumb)
		

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


def addLink(name,url,description,length,iconimage):
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name , "Plot":description, "Duration":length } )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
		return ok


def addDir(name,url,mode,iconimage):
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name } )
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
		getShows()
	
elif mode==1:
		print ""+url
		index(url)

elif mode==2:
		print ""+url
		getShowClips()

elif mode==3:
		print ""+url
		indexShowClips(url)

elif mode==4:
		print ""+url
		getTopVideos()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
