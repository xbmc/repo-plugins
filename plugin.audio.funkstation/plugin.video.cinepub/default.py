import sys, os, re
import urllib, urllib2
import unicodedata
import xbmcplugin, xbmcgui, xbmcaddon
from resources.lib.BeautifulSoup import BeautifulSoup
import resources.lib.youtube as yt


siteUrl		= 'http://www.cinepub.ro/'
searchUrl	= 'http://cinepub.ro/site/'
animationUrl	= 'http://cinepub.ro/site/filme/animatie/'
shortsUrl	= 'http://cinepub.ro/site/filme/scurtmetraje/'
moviesUrl	= 'http://cinepub.ro/site/filme/lungmetraje/'
documentariesUrl= 'http://cinepub.ro/site/filme/documentare/'

USER_AGENT 	= 'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2062.120 Safari/537.36'
ACCEPT 		= 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'

#TODO
icon = "DefaultFolder.png"#os.path.join(plugin.getPluginPath(), 'resources', 'media', 'settingsicon.png')
__addon__ = xbmcaddon.Addon()
addonId = 'plugin.video.cinepub'

addonUrl = sys.argv[0]
addonHandle = int(sys.argv[1])

print addonUrl

def localise(id):
	try:
		string = __addon__.getLocalizedString(id)
	except Exception as e:
		print e
		pass
		string = ""
	try:
		string = unicode(string, "utf8")
	except:
		pass
	try:
		string = unicodedata.normalize('NFKD', string).encode('ascii', 'ignore')
	except Exception as e:
		print e
		string = str(id)
	return string

def progressReport(percent):
	return localise(1008) + str(percent) + "%"

def mainMenu():
	addDir(localise(1001),animationUrl,4,icon)
	addDir(localise(1002),shortsUrl,4,icon)
	addDir(localise(1003),moviesUrl,4,icon)
	addDir(localise(1004),documentariesUrl,4,icon)
	addDir(localise(1005),siteUrl,99,icon)
	#addDir('Clear Cache',siteUrl,18)
	
	xbmcplugin.endOfDirectory(addonHandle)

def listMovies(url):
	progress = xbmcgui.DialogProgress()
	progress.create(localise(1006), localise(1007))
	progress.update(1, "", progressReport(1), "")

	list = []
	#TODO: caching
	movieList = BeautifulSoup(httpReq(url)).find("div", {"class": "categoryThumbnailList"}).contents
	total = len(movieList)
	current = 0
	for movie in movieList:
		link = movie.next
		url = link['href']
		title = link['title']
		title = title[:title.find("<")]
		img = link.find("img")
		if img:
			img = img['src']
		addDir(title,url,8,img,folder=False)

		if progress.iscanceled():
			sys.exit()

		current += 1
		percent = int((current * 100) / total)
		progress.update(percent, "", progressReport(percent), "")

	progress.close()
	
	xbmcplugin.endOfDirectory(addonHandle)

def playMovie(url, name, thumb):
	movies = BeautifulSoup(httpReq(url)).findAll("div", {"class": "btn"})
	for movie in movies:
		if movie.text.lower().find("vezi film") > -1:
			print movie
			url = None
			while url == None:
				movie = movie.next
				try:
					if movie.name == "a":
						break
				except: #movie doesn't have field name (string)
					continue
			break
	url = movie['href']
	url = yt.getYoutubeMovie(url)

	win = xbmcgui.Window(10000)
	win.setProperty('cinepub.playing.title', name.lower())
	item = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
	item.setInfo(type = "Video", infoLabels = {"title": name})
	item.setPath(url)

	xbmcplugin.setResolvedUrl(addonHandle, True, item)
	return True

def httpReq(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', USER_AGENT)
        req.add_header('Accept', ACCEPT)
        req.add_header('Cache-Control', 'no-transform')
        response = urllib2.urlopen(req)
        source = response.read()
        response.close()
        return source

def buildRequest(dict):
	out = {}
	for key, value in dict.iteritems():
		if isinstance(value, unicode):
			value = value.encode('utf8')
		elif isinstance(value, str):
			value.decode('utf8')
		out[key] = value
	return addonUrl + '?' + urllib.urlencode(out)

def addDir(name, url, mode, thumbnail='', folder=True):
	ok = True
	params = {'name': name, 'mode': mode, 'url': url, 'thumbnail': thumbnail}

	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
	
	if not folder:
		liz.setProperty('isPlayable', 'true')
		liz.setProperty('resumetime', str(0))
		liz.setProperty('totaltime', str(1))
		
	liz.setInfo(type="Video", infoLabels = {"title": name})

	ok = xbmcplugin.addDirectoryItem(handle = addonHandle, url = buildRequest(params), listitem = liz, isFolder = folder)
	return ok

def getParams():
	param = {'default': 'none'}
	paramstring = sys.argv[2]
	if len(paramstring) >= 2:
			params = sys.argv[2]
			cleanedparams = params.replace('?','')
			if (params[len(params)-1] == '/'):
				params = params[0:len(params)-2]
			pairsofparams = cleanedparams.split('&')
			param = {}
			for i in range(len(pairsofparams)):
				splitparams = {}
				splitparams = pairsofparams[i].split('=')
				if (len(splitparams)) == 2:
					param[splitparams[0]] = splitparams[1]
	return param


params = getParams()

mode = int(params.get('mode', 0))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))
thumbnail = urllib.unquote_plus(params.get('thumbnail', ''))


if mode == 0 or not url or len(url) < 1: mainMenu()
if mode == 4: listMovies(url)
if mode == 8: playMovie(url, name, thumbnail)
