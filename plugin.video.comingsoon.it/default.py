import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import datetime, re, sys, urllib2
from bs4 import BeautifulSoup

__addon__ = xbmcaddon.Addon()
__language__ = __addon__.getLocalizedString
addonID = __addon__.getAddonInfo('id')
thisPlugin = int(sys.argv[1])

home = "http://www.comingsoon.it"

def log(msg, force = False):
	if force:
		xbmc.log((u'### [' + addonID + u'] - ' + str(msg)).encode('utf-8'), level = xbmc.LOGNOTICE)
	else:
		xbmc.log((u'### [' + addonID + u'] - ' + str(msg)).encode('utf-8'), level = xbmc.LOGDEBUG)

def loadPage(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:29.0) Gecko/20100101 Firefox/29.0')
	try:
		response = urllib2.urlopen(req)
		code = response.read().decode("utf-8")
		response.close()
	except:
		return False
	return code

def getMoviesList(page = 1, intheaters = True):
	try: 
		page = int(page)
	except:
		page = 1
	movies = []
	if (intheaters):
		content =  loadPage(home + "/cinema/filmalcinema/?page=" + str(page))
	else:
		content =  loadPage(home + "/cinema/calendariouscite/?r=" + str(page))
	if (content):
		bpage = BeautifulSoup(content, "html.parser")
		if (bpage):
			htmlmovies = bpage.find_all("a", attrs={"class": "col-xs-12 cinema"})
			if (htmlmovies):
				for htmlmovie in htmlmovies:
					if (htmlmovie and htmlmovie.has_attr('href')):
						res = re.search(".*?\/.*?\/([0-9]+)\/scheda\/", htmlmovie['href'])
						if (res):
							id = res.group(1)						
							titolo = ""
							titolooriginale = ""
							data = ""
							genere = ""
							nazione = ""
							anno = ""
							regia = ""
							cast = ""
							div = htmlmovie.find("div", attrs={"class": "h3 titolo cat-hover-color anim25"})
							if (div):
								titolo= div.string
							div = htmlmovie.find("div", attrs={"class": "h5 sottotitolo"})
							if (div):
								titolo= div.string
							ul = htmlmovie.find("ul", attrs={"class": "col-xs-9 box-descrizione"})
							if (ul):
								infos = ul.find_all('li')
								if (infos):
									for info in infos:
										if (info.span):
											if (info.span.string == 'DATA USCITA'):
												data = info.contents[1][1:].strip()
											elif (info.span.string == 'GENERE'):
												genere = info.contents[1][1:].strip()
											elif (info.span.string == 'NAZIONALITA&#39;'):
												nazione = info.contents[1][1:].strip()
											elif (info.span.string == 'ANNO'):
												anno = info.contents[1][1:].strip()
											elif (info.span.string == 'REGIA'):
												regia = info.contents[1][1:].strip()
											elif (info.span.string == 'CAST'):
												cast = info.contents[1][1:].strip()
							movies.append( { "id": id,  "title": titolo, "originaltitle": titolooriginale, "date": data, "genre": genere, "nation": nazione, "year": anno, "director": regia, "cast": cast } )
				if (intheaters):
					ul = bpage.find("ul", attrs={"class": "pagination"})
					if (ul):
						pages = ul.find_all('li')
						if (pages):
							first = pages[0].a
							if (not (first and first.has_attr("class") and 'disattivato' in first["class"])):
								movies.append( { "id": page - 1,  "title": 32001 } )
							last = pages[-1].a
							if (not (last and last.has_attr("class") and 'disattivato' in last["class"])):
								movies.append( { "id": page + 1,  "title": 32002 } )
				else:
					movies.append( { "id": page - 7,  "title": 32003 } )
					movies.append( { "id": page + 7,  "title": 32004 } )
	return movies

def getMoviesVideos(id):
	videos = []
	content =  loadPage("http://www.comingsoon.it/film/movie/%s/video/" % str(id)) # url http://www.comingsoon.it/film/something/{movieid}/scheda/
	if (content):
		page = BeautifulSoup(content, "html.parser")
		if (page):
			htmlrows = page.find_all("div", attrs={"class": "video-player-xl-articolo video-player-xl-sinistra"})
			if (htmlrows):
				for htmlrow in htmlrows:
					htmlvideos = htmlrow.find_all('a')
					if (htmlvideos):
						for htmlvideo in htmlvideos:
							res = re.search(".*?\/.*?\/[0-9]+\/video\/\?vid=([0-9]+)", htmlvideo['href'])
							if (res):
								vid = res.group(1)
								nome = ""
								div = htmlvideo.find("div", attrs={"class": "h6 descrizione"})
								if (div):
									nome = div.string
							videos.append( { "vid": vid,  "name": nome } )
		return videos
							
def getVideoUrls(vid):
	videourls = {}
	content =  loadPage("http://www.comingsoon.it/VideoPlayer/embed/?ply=1&idv=" + str(vid))
	if (content):
		res = re.search('vLwRes\:.*?\"(.*?)\"', content)
		if (res):
			videourls['sd'] = "http://video.comingsoon.it/" + res.group(1)
		res = re.search('vHiRes\:.*?\"(.*?)\"', content)
		if (res):
			videourls['hd'] = "http://video.comingsoon.it/" + res.group(1)
	return videourls

def addDirectoryItem(label, id, mode, iconImage):
	url = sys.argv[0]+"?id="+str(id)+"&mode="+str(mode)
	li = xbmcgui.ListItem(label, iconImage="DefaultFolder.png", thumbnailImage=iconImage)
	li.setInfo(type="Video", infoLabels={"title": label})
	return xbmcplugin.addDirectoryItem(handle=thisPlugin, url=url, listitem=li, isFolder=True)
	
def addLinkItem(label, id, mode, iconImage, description="", duration=""):
	url = sys.argv[0]+"?id="+str(id)+"&mode="+str(mode)
	li = xbmcgui.ListItem(label, iconImage="DefaultVideo.png", thumbnailImage=iconImage)
	if duration == "":
		li.setInfo(type="Video", infoLabels={"title": label, "plot": description})
	else:
		li.setInfo(type="Video", infoLabels={"title": label, "plot": description, "duration": str(round(int(duration)/60,0))})
		li.addStreamInfo("video", {"duration": int(duration)})
	li.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=thisPlugin, url=url, listitem=li, isFolder=False) 

def loadList():
	global thisPlugin
	addDirectoryItem(__language__(32005), "", "moviesintheaters", "")
	addDirectoryItem(__language__(32006), "", "moviescomingsoon", "")
	xbmcplugin.endOfDirectory(thisPlugin)

def loadMovies(page = 1, intheaters = True):
	global thisPlugin
	for movie in getMoviesList(page, intheaters):
		if (isinstance( movie['title'], ( int, long ) )):
			if ( movie['title'] == 32002):
				addDirectoryItem(__language__(movie['title']), movie['id'], "moviesintheaters", "")
			else:
				addDirectoryItem(__language__(movie['title']), movie['id'], "comingweek", "")
		else:
			quality = int(__addon__.getSetting( 'Quality' ))
			if (quality == 2):
				addDirectoryItem(movie['title'], movie['id'], "videos", "http://mr.comingsoon.it/imgdb/locandine/140x200/%s.png" % movie['id'])
			elif (quality == 1):
				addDirectoryItem(movie['title'], movie['id'], "videos", "http://mr.comingsoon.it/imgdb/locandine/235x336/%s.jpg" % movie['id'])
			else:
				addDirectoryItem(movie['title'], movie['id'], "videos", "http://mr.comingsoon.it/imgdb/locandine/big/%s.jpg" % movie['id'])
	xbmcplugin.endOfDirectory(thisPlugin)

def loadDates(offset = 0):
	global thisPlugin
	try: 
		offset = int(offset)
	except:
		offset = 0
	d = datetime.date.today() + datetime.timedelta(offset)
	days_behind = d.weekday() - 3
	if days_behind < 0: # Target day already happened this week
		days_behind += 7
	nextthursday = d - datetime.timedelta(days_behind)
	for x in range(0,9):
		addDirectoryItem(__language__(32007) + " " + str(nextthursday + datetime.timedelta(x * 7)), offset + (x * 7), "comingweek"	, "")
	addDirectoryItem(__language__(32001), offset - 63, "moviescomingsoon", "")
	addDirectoryItem(__language__(32002), offset + 63, "moviescomingsoon", "")
	xbmcplugin.endOfDirectory(thisPlugin)

def loadVideos(id):
	global thisPlugin
	for video in getMoviesVideos(id):
		quality =int(__addon__.getSetting( 'Quality' ))
		if (quality == 2):
			addLinkItem(video['name'], video['vid'], "videourl", "http://mr.comingsoon.it/imgdb/video/%s_icov.jpg" % video['vid'])
		else:
			addLinkItem(video['name'], video['vid'], "videourl", "http://mr.comingsoon.it/imgdb/video/%s_big.jpg" % video['vid'])
	xbmcplugin.endOfDirectory(thisPlugin)

def watchVideo(id):
	urls = getVideoUrls(id)
	url = ""
	PreferHD = (__addon__.getSetting( 'PreferHD' ) == 'true')
	if (PreferHD and 'hd' in urls):
		url = urls['hd']
	elif ('sd' in urls):
		url = urls['sd']
	elif ('hd' in urls):
		url = urls['hd']
	else:
		log('No links found')
		return
	listItem = xbmcgui.ListItem(path=url)
	xbmcplugin.setResolvedUrl(thisPlugin, True, listItem)

def getParams():
	param = []
	paramstring = sys.argv[2]
	if len(paramstring) >= 2:
		params = sys.argv[2]
		cleanedparams = params.replace('?', '')
		if (params[len(params) - 1] == '/'):
			params = params[0:len(params) - 2]
		pairsofparams = cleanedparams.split('&')
		param = {}
		for i in range(len(pairsofparams)):
			splitparams = {}
			splitparams = pairsofparams[i].split('=')
			if (len(splitparams)) == 2:
				param[splitparams[0]] = splitparams[1]
								
		return param

if not sys.argv[2]:
	loadList()
else:
	params = getParams()
	if params['mode'] == "moviesintheaters":
		if ("id" in params):
			loadMovies(params['id'])
		else:
			loadMovies()
	elif params['mode'] == "moviescomingsoon":
		if ("id" in params):
			loadDates(params['id'])
		else:
			loadDates()
	elif params['mode'] == "comingweek":
		if ("id" in params):
			loadMovies(params['id'], False)
		else:
			loadMovies(0, False)
	elif params['mode'] == "videos":
		loadVideos(params['id'])
	elif params['mode'] == "videourl":
		watchVideo(params['id'])
	else:
		loadList()
