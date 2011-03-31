import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.funny.or.die')
__language__ = __settings__.getLocalizedString
sort = __settings__.getSetting('sort_by')
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )


def CATEGORIES():
	if sort==__language__(30015):
		u = ''
	elif sort==__language__(30016):
		u = 'most_recent'
	elif sort==__language__(30017):
		u = 'most_viewed'
	elif sort==__language__(30018):
		u = 'most_favorited'
	elif sort==__language__(30019):
		u = 'highest_rated'
	else:
		u = ''
	addDir(__language__(30000),'http://www.funnyordie.com/browse/videos/all/exclusives/'+u,1,icon)
	addDir(__language__(30001),'http://www.funnyordie.com/browse/videos/all/immortal/'+u,1,icon)
	addDir(__language__(30002),'http://www.funnyordie.com/browse/videos/stand_up/all/'+u,1,icon)
	addDir(__language__(30003),'http://www.funnyordie.com/browse/videos/animation/all/'+u,1,icon)
	addDir(__language__(30004),'http://www.funnyordie.com/browse/videos/web_series/all/'+u,1,icon)
	addDir(__language__(30005),'http://www.funnyordie.com/browse/videos/nsfw/all/'+u,1,icon)
	addDir(__language__(30006),'http://www.funnyordie.com/browse/videos/sketch/all/'+u,1,icon)
	addDir(__language__(30007),'http://www.funnyordie.com/browse/videos/sports/all/'+u,1,icon)
	addDir(__language__(30008),'http://www.funnyordie.com/browse/videos/clean_comedy/all/'+u,1,icon)
	addDir(__language__(30009),'http://www.funnyordie.com/browse/videos/politics/all/'+u,1,icon)
	addDir(__language__(30010),'http://www.funnyordie.com/browse/videos/music/all/'+u,1,icon)
	addDir(__language__(30011),'http://www.funnyordie.com/browse/videos/parody/all/'+u,1,icon)
	addDir(__language__(30012),'http://www.funnyordie.com/browse/videos/real_life/all/'+u,1,icon)
	addDir(__language__(30013),'http://www.funnyordie.com/browse/videos/all/all/'+u,1,icon)


def INDEX(url):
	req = urllib2.Request(url)
	req.addheaders = [('Referer', 'http://www.funnyordie.com/videos'),
			('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
	videos = soup.findAll('div', attrs={'class' : "detailed_vp"})
	for video in videos:
		try:
			link = video('a')[0]['href'].split('/')[2]
			name = video('a')[0]['title']
			thumbnail = video('img')[0]['src'].replace('medium','fullsize')
			addLink(name,link,2,thumbnail)
		except:
			pass
	try:
		page = soup.find('a', attrs={'class' : "next_page"})['href']
		addDir(__language__(30021),'http://www.funnyordie.com'+page,1,'')
	except:
		pass


def getPlayList():
	url = sys.argv[2]
	req = urllib2.Request(url)
	req.addheaders = [('Referer', 'http://www.funnyordie.com/videos'),
			('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
	videos = soup.findAll('div', attrs={'class' : "detailed_vp"})
	playlist = xbmc.PlayList(1)
	playlist.clear()
	for video in videos:
		try:
			link = video('a')[0]['href'].split('/')[2]
			name = video('a')[0]['title']
			thumbnail = video('img')[0]['src'].replace('medium','fullsize')
			url = get_smil(link)
			info = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
			playlist.add(url, info)
		except:
			pass
	play=xbmc.Player( xbmc.PLAYER_CORE_DVDPLAYER ).play(playlist)


def playVid(url):
	url = get_smil(url)
	item = xbmcgui.ListItem(path=url)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def addToPlayList():
	url = sys.argv[2]
	name = sys.argv[3]
	iconimage = sys.argv[4]
	url = get_smil(url)
	info = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	playlist = xbmc.PlayList(1)
	playlist.add(url, info)


def get_smil(id):
	req = urllib2.Request("http://www.funnyordie.com/player/"+id+"?v=3")
	response = urllib2.urlopen(req)
	smil = response.read()
	response.close()
	soup = BeautifulSoup(smil)
	title = soup.find('title').string
	stream_list = soup.findAll('stream')
	if len(stream_list) < 1:
		stream = soup.find('location').contents[0]
		return stream
	streams = []
	for stream in stream_list:
		streams.append(stream.file.contents[0])
	return streams[0]


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


def addLink(name,url,mode,iconimage,showcontext=True):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	if showcontext:
		contextMenu = [(__language__(30022),'XBMC.RunScript(special://home/addons/plugin.video.funny.or.die/default.py,addToPlayList,'+url+','+name+','+iconimage+')')]
		liz.addContextMenuItems(contextMenu)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=20)
	return ok

def addDir(name,url,mode,iconimage,showcontext=True):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	if showcontext:
		contextMenu = [(__language__(30023),'XBMC.RunScript(special://home/addons/plugin.video.funny.or.die/default.py,autoPlay,'+url+')')]
		liz.addContextMenuItems(contextMenu)
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok


def startPlugin():	
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
		CATEGORIES()

	elif mode==1:
		print ""+url
		INDEX(url)

	elif mode==2:
		print "NEW LINK: "+url
		playVid(url)

	xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))

if sys.argv[1] == 'addToPlayList':
		addToPlayList()

elif sys.argv[1] == 'autoPlay':
		getPlayList()

else:
		startPlugin()
