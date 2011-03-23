import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.hgtv')


def getShows():
		url='http://www.hgtv.com/full-episodes/package/index.html'
		req = urllib2.Request(url)
		req.addheaders = [('Referer', 'http://www.hgtv.com'),
                          ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		shows = soup.findAll('ol', attrs={'id' : "fe-list"})[1]('li')
		del shows[0];del shows[7];del shows[9];del shows[13];del shows[15];del shows[24];del shows[33];del shows[41]
		shows[22]('a')[1]['href'] = '/hgtv-house-of-bryan/videos/index.html'
		shows[35]('a')[1]['href'] = '/paint-over-with-jennifer-bertrand-special/video/index.html'
		shows[37]('a')[1]['href'] = '/hgtv48/videos/index.html'
		for show in shows:
				name = show('h2')[0].string
				thumb = show('a')[0]('img')[0]['src']
				thumbnail = thumb.replace(' ','')
				url = show('a')[1]['href']
				addDir(name,url,1,thumbnail)
		
		
def INDEX(url):
		url='http://www.hgtv.com'+url
		req = urllib2.Request(url)
		req.addheaders = [('Referer', 'http://www.hgtv.com'),
				('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		showID=re.compile("var snap = new SNI.HGTV.Player.FullSize\(\\'.+?\\',\\'(.+?)\\', \\'\\'\);").findall(link)
		if len(showID)<1:
				showID=re.compile("var snap = new SNI.HGTV.Player.FullSize\(\'.+?','(.+?)', '.+?'\);").findall(link)
		print'--------> '+showID[0]
		url='http://www.hgtv.com/hgtv/channel/xml/0,,'+showID[0]+',00.xml'
		req = urllib2.Request(url)
		req.addheaders = [('Referer', 'http://www.hgtv.com'),
				('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
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

if mode==None or url==None or len(url)<1:
		print ""
		getShows()
	
elif mode==1:
		print ""+url
		INDEX(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
