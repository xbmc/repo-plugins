import urllib,urllib2,re,os,xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup
import simplejson as json

__settings__ = xbmcaddon.Addon(id='plugin.image.lastfm')
__language__ = __settings__.getLocalizedString
__home__ = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( __home__, 'icon.png' ) )
nexticon = xbmc.translatePath( os.path.join( __home__, 'resources/next.png' ) )
searchicon = xbmc.translatePath( os.path.join( __home__, 'resources/search.png' ) )
showicon = xbmc.translatePath( os.path.join( __home__, 'resources/slideshow.png' ) )
username = str(xbmc.executehttpapi('GetGuiSetting(3;scrobbler.lastfmusername)'))[4:]


def Catagories():
		addDir(__language__(30009),'',8,icon)
		print 'user------------>'+username
		if username != "":
				# add lastfm user library
				addDir(__language__(30000),'http://ws.audioscrobbler.com/2.0/?method=library.getartists&api_key=71e468a84c1f40d4991ddccc46e40f1b&user='+username,3,icon)
				# add neighbours
				addDir(__language__(30008),'http://ws.audioscrobbler.com/2.0/?method=user.getneighbours&user='+username+'&api_key=b25b959554ed76058ac220b7b2e0a026',5,icon)
				# add friends
				addDir(__language__(30007),'http://ws.audioscrobbler.com/2.0/?method=user.getfriends&user='+username+'&api_key=b25b959554ed76058ac220b7b2e0a026',5,icon)
		# add search dir
		addDir(__language__(30001),'',2,searchicon)
		if xbmc.Player().isPlayingAudio() == True:
				name = xbmc.Player().getMusicInfoTag().getArtist()
				url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getimages&artist='+name.replace(' ','+')+'&autocorrect=1&api_key=71e468a84c1f40d4991ddccc46e40f1b'
				# add now playing dir
				addDir(__language__(30002)+name,url,1,icon)
				# add last.fm slideshow
				addDir(__language__(30013),'',7,showicon)
	

def getXBMCArtist():
		data = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "AudioLibrary.GetArtists", "id": 1}')
		udata = json.loads(data)
		artists = udata["result"]["artists"]
		for artist in artists:
				try:
						name = artist["label"]
						try:
								thumbnail = artist["thumbnail"]
						except:
								thumbnail = ''
						url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getimages&artist='+name.replace(' ','+')+'&autocorrect=1&api_key=71e468a84c1f40d4991ddccc46e40f1b'
						addDir(name,url,1,thumbnail)
				except:
						pass


# this gets the lastfm user library
def getLibraryArtist(url):
		# add dir for 'getArtistSlideShow'
		addDir(__language__(30006),'http://ws.audioscrobbler.com/2.0/?method=library.getartists&api_key=71e468a84c1f40d4991ddccc46e40f1b&user='+username,4,icon)
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
		images = soup('artist')
		for image in images:
				name = image('name')[0].string
				thumbnail = image(attrs={'size' : "mega"})[0].string
				url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getimages&artist='+name.replace(' ','+')+'&autocorrect=1&api_key=71e468a84c1f40d4991ddccc46e40f1b'
				try:
						addDir(name,url,1,thumbnail)
				except:
						pass				
		try:
				if int(soup('artists')[0]['page']) < int(soup('artists')[0]['totalpages']):
						url = 'http://ws.audioscrobbler.com/2.0/?method=library.getartists&api_key=71e468a84c1f40d4991ddccc46e40f1b&user='+username+'&page='+str(int(soup('artists')[0]['page'])+1)
						#add next page
						addDir(__language__(30003),url,3,nexticon)
		except:
				pass


# this gets friends and neighbour list				
def getOthers(url):
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
		users = soup('user')
		try:
				for user in  users:
						name = user('name')[0].string
						thumbnail = user('image')[3].string
						if thumbnail=='None':
								thumbnail = icon
						url = 'http://ws.audioscrobbler.com/2.0/?method=library.getartists&api_key=71e468a84c1f40d4991ddccc46e40f1b&user='+name
						addDir(name,url,6,thumbnail)
		except:
				pass		


# this gets friends and neighbour artist
def getOthersArtist(url,name):
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
		images = soup('artist')
		for image in images:
				title = image('name')[0].string
				thumbnail = image(attrs={'size' : "large"})[0].string
				url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getimages&artist='+title.replace(' ','+')+'&autocorrect=1&api_key=71e468a84c1f40d4991ddccc46e40f1b'
				try:
						addDir(title,url,1,thumbnail)
				except:
						pass
		try:
				if int(soup('artists')[0]['page']) < int(soup('artists')[0]['totalpages']):
						url = 'http://ws.audioscrobbler.com/2.0/?method=library.getartists&api_key=71e468a84c1f40d4991ddccc46e40f1b&user='+name+'&page='+str(int(soup('artists')[0]['page'])+1)
						#add next page
						addDir(__language__(30003),url,6,nexticon)
		except:
				pass


def getArtistSlideShow(url):
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
		images = soup('artist')
		xbmc.executehttpapi("ClearSlideshow")
		for image in images:
				try:
						url = image(attrs={'size' : "mega"})[0].string
						xbmc.executehttpapi("AddToSlideshow(%s)" % url)
				except:
						pass
			
		try:
				if int(soup('artists')[0]['page']) < int(soup('artists')[0]['totalpages']):
						url = 'http://ws.audioscrobbler.com/2.0/?method=library.getartists&api_key=71e468a84c1f40d4991ddccc46e40f1b&user='+username+'&page='+str(int(soup('artists')[0]['page'])+1)
						# add next page
						addDir(__language__(30003),url,4,nexticon)
		except:
				pass
		xbmc.executebuiltin( "SlideShow(,recursive,notrandom)" )


def Search():
		searchStr = ''
		keyboard = xbmc.Keyboard(searchStr, __language__(30005))
		keyboard.doModal()
		if (keyboard.isConfirmed() == False):
				return
		newStr = keyboard.getText()
		if len(newStr) == 0:
				return
		url = 'http://ws.audioscrobbler.com/2.0/?method=artist.getimages&artist='+newStr.replace(' ','+')+'&autocorrect=1&api_key=71e468a84c1f40d4991ddccc46e40f1b'
		getImageList(url)


def getImageList(url):
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
		images = soup('image')
		for image in images:
				name = image.title.string
				if name==None:
						try:
								name = image('name')[0].string
						except:
								name = 'unknown'
				date = image.dateadded.string
				url = image.size.string
				addLink(name,url,'')
				

class DownloadFiles:
		def __init__(self):
				url = sys.argv[2]
				filename = sys.argv[3]
				def download(url, dest):
						dialog = xbmcgui.DialogProgress()
						dialog.create(__language__(30015),__language__(30016), filename)
						urllib.urlretrieve(url, dest, lambda nb, bs, fs, url = url: _pbhook(nb, bs, fs, url, dialog))
				def _pbhook(numblocks, blocksize, filesize, url = None,dialog = None):
						try:
								percent = min((numblocks * blocksize * 100) / filesize, 100)
								dialog.update(percent)
						except:
								percent = 100
								dialog.update(percent)
						if dialog.iscanceled():
								dialog.close()
				# check for a download location, if not open settings
				if (__settings__.getSetting('save_path') == ''):
						__settings__.openSettings('save_path')
				# lets the user rename the file
				keyboard = xbmc.Keyboard(filename,__language__(30011))
				keyboard.doModal()
				if (keyboard.isConfirmed() == False):
						return
				filename = keyboard.getText()
				if len(filename) == 0:
						return
				filepath = xbmc.translatePath(os.path.join(__settings__.getSetting('save_path'),filename))
				download(url, filepath)
		

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


def addLink(name,url,iconimage,showcontext=True):
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultImage.png", thumbnailImage=iconimage)
		liz.setInfo( type="image", infoLabels={ "Title": name } )
		# this adds 'save image' to the context menu
		if showcontext:
				try:
						filename = url.rsplit('/')[-1].replace('+','_')
				except:
						pass
				contextMenu = [(__language__(30004),'XBMC.RunScript(special://home/addons/plugin.image.lastfm/default.py,download,'+url+','+filename+')')]
				liz.addContextMenuItems(contextMenu)
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
		return ok


def addDir(name,url,mode,iconimage):
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultImage.png", thumbnailImage=iconimage)
		liz.setInfo( type="image", infoLabels={ "Title": name } )
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

		if mode==None:
				print ""
				Catagories()
				
		elif mode==1:
				print ""
				getImageList(url)

		elif mode==2:
				print ""
				Search()

		elif mode==3:
				print ""
				getLibraryArtist(url)
				
		elif mode==4:
				print ""
				getArtistSlideShow(url)

		elif mode==5:
				print ""
				getOthers(url)
				
		elif mode==6:
				print ""
				getOthersArtist(url,name)
				
		elif mode==7:
				print ""
				xbmc.executescript(xbmc.translatePath( os.path.join( __home__, 'resources/slideshow.py' ) ))
						
		elif mode==8:
				print ""
				getXBMCArtist()
						
		xbmcplugin.endOfDirectory(int(sys.argv[1]))


if sys.argv[1] == 'download':
		DownloadFiles()
	
else:
		startPlugin()