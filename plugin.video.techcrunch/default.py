import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.techcrunch')
home = __settings__.getAddonInfo('path')


def getShows():
		req = urllib2.Request('http://techcrunch.tv/')
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
		shows = soup.findAll('div', attrs={'class' : "show_container"})
		for show in shows:
				title = show('a')[0].string
				url = show('a')[1]['href']
				thumbnail = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
				addDir(title,url,1,thumbnail)


def index(url):
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		link=response.read()
		soup = BeautifulStoneSoup(link, convertEntities=BeautifulStoneSoup.XML_ENTITIES)
		shows = soup('item')
		if soup.channel.title.string == 'TechCrunch Disrupt':
				for show in shows:
						title = show.title.string
						thumbnail = show('media:thumbnail')[0]['url']
						try:
								url = show('enclosure')[0]['url']
						except:
								pass
						try:
								description = show.description.string
						except:
								description = ''
						try:
								pubdate = show.pubdate.string
						except:
								pubdate = ''
						try:
								duration = show('itunes:duration')[0].string
						except:
								duration = ''
						addLink(title,url,pubdate,description,duration,thumbnail)
		else:
				for show in shows:
						title = show.title.string
						thumbnail = show('media:thumbnail')[0]['url']
						try:
								url = show('media:content')[5]['url']
						except:
								try:
										url = show('media:content')[0]['url']
								except:
										pass
						try:
								description = show.description.string
						except:
								description = ''
						try:
								pubdate = show.pubdate.string
						except:
								pubdate = ''
						try:
								duration = show('media:content')[0]['duration']
						except:
								duration = ''
						addLink(title,url,pubdate,description,duration,thumbnail)

	
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


def addLink(name,url,pubdate,description,duration,iconimage):
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		description = description + "\n \n Published: " +pubdate
		liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description,"Duration":duration } )
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
		
if mode==1:
		print""
		index(url)
		
xbmcplugin.endOfDirectory(int(sys.argv[1]))
