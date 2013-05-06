import os
import sys
import md5
import urllib
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
from xml.etree import ElementTree

SETTINGS = sys.modules[ "__main__" ].__settings__

class updateArgs:

	def __init__(self, *args, **kwargs):
		for key, value in kwargs.iteritems():
			if value == 'None':
				kwargs[key] = None
			else:
				kwargs[key] = urllib.unquote_plus(kwargs[key])
		self.__dict__.update(kwargs)

class LoginFTW:
	
	def __init__(self, *args, **kwargs):
		self.status = 0
		self.settings = {}
		self.settings['username'] = SETTINGS.getSetting("username_ftw")
		self.settings['password'] = SETTINGS.getSetting("password_ftw")
	
	def checkLogin(self):
		if self.settings['username'] == '' or self.settings['password'] == '':
			self.resp = xbmcgui.Dialog().yesno("No username/password set!","AnimeFTW.tv requires you to be logged in to view", \
			"videos.  Would you like to log-in now?")
			if self.resp:
				self.respLogin = SETTINGS.openSettings()
				if self.respLogin:
					self.settings['username'] = SETTINGS.getSetting("username_ftw")
					self.settings['password'] = SETTINGS.getSetting("password_ftw")
					return self.settings['username'], self.settings['password']
				else:
					xbmc.executebuiltin('XBMC.Notification("Please Login:","An advanced user account is required to view content.", 3000)')
					return '', ''
			else:
				xbmc.executebuiltin('XBMC.Notification("Please Login:","An advanced user account is required to view content.", 3000)')
				return '', ''
		else:
			return self.settings['username'], self.settings['password']
			
	def hashPassword(self, password):
		return md5.new(password).hexdigest()
		
class grabFTW:
	
	def __init__(self, *args, **kwargs):
		self.settings = {}
		self.settings['username'], self.settings['password'] = LoginFTW().checkLogin()
		self.settings['passHash'] = LoginFTW().hashPassword(self.settings['password'])
		self.urlString = 'did=hVhS-672s-sKhK-yUn0&username=' + self.settings['username'] + '&password=' + self.settings['passHash']

	def getHTML(self, url):	
		self.currenturl = url
		htmlSource = None
		print "[FTW] Finding URL: "+self.currenturl
		htmlSource = urllib.urlopen(url).read()
		print "[FTW] Got URL."
		return htmlSource
		
	def getLatest(self, count = 25):
		htmlSource = self.getHTML("https://www.animeftw.tv/api/v1/show?" + self.urlString + "&show=latest&start=0&count=" + str(count))
		root = ElementTree.fromstring(htmlSource)
		latest_list = root.findall('episode')
		for episode in latest_list:
			UI().addItem({'Seriesname': unicode(episode.find('series').text.replace('`', '\'')).encode('utf-8'), 'Title': unicode(episode.find('series').text.replace('`', '\'') + " - " + episode.find('epnumber').text + " - " + episode.find('name').text.replace('`', '\'')).encode('utf-8'), 'mode': 'playEpisode', 'url': episode.find('videolink').text })
		del latest_list
		del root
		UI().endofdirectory('title')
		
	def getGenres(self):
		htmlSource = self.getHTML("https://www.animeftw.tv/api/v1/show?" + self.urlString + "&show=tagcloud")
		root = ElementTree.fromstring(htmlSource)
		tag_list = root.findall('tag')
		for tag in tag_list:
			genreFilter = tag.attrib['href'].split('filter=')[1]
			UI().addItem({'Title': unicode(tag.text).encode('utf-8').title(), 'mode': 'anime_all', 'url': tag.attrib['href'], 'category': str(genreFilter)})
		del tag_list
		del root
		UI().endofdirectory('title')
		
	def getListing(self, category = 0, showType = 'anime', count = 2000, filter = None):
		print "[FTW] FILTER is set to: " + str(filter)
		url = "https://www.animeftw.tv/api/v1/show?" + self.urlString + "&show=" + showType + "&start=0&count=" + str(count)
		if filter:
			url += "&filter=" + str(filter)
		htmlSource = self.getHTML(url)
		root = ElementTree.fromstring(htmlSource)
		cat_list = ['episode', 'episode', 'episode', 'episode', 'episode', 'movie']
		videoType = cat_list[category]
		print "[FTW] Current video type: " + str(videoType)
		series_list = root.findall('series')
		for series in series_list:
			numberOfMovies = int(series.find('movies').text)
			numberOfEpisodes = int(series.find('episodes').text)
			isOVA = series.find('ova').text
			isAiring = series.find('airing').text
			if numberOfMovies == 1 and numberOfEpisodes == 1 and category != 5:
				continue
			elif numberOfMovies < 1 and category == 5:
				continue
			elif isOVA == 'yes' and category != 0:
				continue
			elif isOVA == 'no' and category == 0:
				continue
			elif isAiring == 'no' and category == 2:
				continue
			elif isAiring == 'yes' and category == 3:
				continue
			else:
				seriesname = series.find('seriesName').text
				seriesname = unicode(seriesname.replace('`', '\'')).encode('utf-8')
				
				seriesdict = {'name': seriesname, \
							  'nameorig': unicode(series.find('romaji').text).encode('utf-8'), \
							  'url': series.attrib['href'], \
							  'thumb': series.find('image').text, \
							  'plot':unicode(series.find('description').text).encode('utf-8'), \
							  'rating': 0.0, \
							  'episodes': numberOfEpisodes, \
							  'genre': unicode(series.find('category').text).encode('utf-8') }

				UI().addItem({'Title':seriesdict['name'], 'mode': videoType, 'url':seriesdict['url'], 'Thumb':seriesdict['thumb']}, seriesdict, True, len(series_list))
				
		del series_list
		del root
		UI().endofdirectory('title')
		
	def getEpisodes(self, url, seriesname = None, seriesimage = None, category = None):
		htmlSource = self.getHTML(url)
		root = ElementTree.fromstring(htmlSource)
		episodes = root.findall('.//' + category)
		
		for i, episode in enumerate(episodes):
			if category == 'episode':
				epname = unicode(episode.find('epnumber').text + ".) " + episode.find('name').text.replace('`', '\'')).encode('utf-8')
			else:
				epname = unicode(episode.find('name').text.replace('`', '\'')).encode('utf-8')
			
			url = episode.find('videolink').text
			thumbnail = episode.find('image').text
			if thumbnail == "http://static.ftw-cdn.com/site-images/video-images/noimage.png":
				thumbnail = seriesimage
			
			li = xbmcgui.ListItem(epname, path = url, thumbnailImage = thumbnail)
			li.setInfo(type="Video", infoLabels={ "Title": epname })
			li.setProperty("IsPlayable","true");
			xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=False)
		del episodes
		del root
		UI().endofdirectory()
		
	def playVid(self, url, name, thumb):
		stream_url = url.replace(' ', '')
		stream_url += '?Referrer=www.animeftw.tv'
		if thumb == None:
			thumb = ''
		item = xbmcgui.ListItem( label = name, label2 = name, iconImage = thumb, thumbnailImage = thumb)
		item.setInfo("video", infoLabels={ "Title": name })
		xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(stream_url, item)

class UI:
	
	def __init__(self):
		self.main = Main(checkMode = False)
		xbmcplugin.setContent(int(sys.argv[1]), 'videos')
	
	def endofdirectory(self, sortMethod = 'none'):
		# set sortmethod to something xbmc can use
		if sortMethod == 'title':
			xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
			xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
		elif sortMethod == 'none':
			xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)

		dontAddToHierarchy = False
		xbmcplugin.endOfDirectory(handle = int(sys.argv[1]), updateListing = dontAddToHierarchy)
			
	def addItem(self, info, extrainfo = None, isFolder=True, total_items = 0):
		#Defaults in dict. Use 'None' instead of None so it is compatible for quote_plus in parseArgs
		info.setdefault('url', 'None')
		info.setdefault('Thumb', 'None')
		info.setdefault('id','None')
		info.setdefault('category','None')
		info.setdefault('Seriesname','None')
		info.setdefault('Icon', info['Thumb'])
		
		#create params for xbmcplugin module
		u = sys.argv[0]+\
			'?url='+urllib.quote_plus(info['url'])+\
			'&mode='+urllib.quote_plus(info['mode'])+\
			'&name='+urllib.quote_plus(info['Title'])+\
			'&seriesname='+urllib.quote_plus(info['Seriesname'])+\
			'&id='+urllib.quote_plus(info['id'])+\
			'&category='+urllib.quote_plus(info['category'])+\
			'&icon='+urllib.quote_plus(info['Thumb'])
		#create list item
		if extrainfo != None:
			li=xbmcgui.ListItem(label = extrainfo['name'], iconImage = info['Icon'], thumbnailImage = info['Thumb'])
			li.setInfo("video", infoLabels={ "Title":extrainfo['name'], "OriginalTitle": extrainfo['nameorig'], "episode": extrainfo['episodes'], "Plot":extrainfo['plot'], "Genre":extrainfo['genre'], 'Rating':extrainfo['rating']})
		else:
			li=xbmcgui.ListItem(label = info['Title'], iconImage = info['Icon'], thumbnailImage = info['Thumb'])
		#for videos, replace context menu with queue and add to favorites
		if not isFolder:
			li.setProperty("IsPlayable", "true") 
			#let xbmc know this can be played, unlike a folder.
			#add context menu items to non-folder items.
			contextmenu = [('Queue Video', 'Action(Queue)')]
		#for folders, completely remove contextmenu, as it is totally useless.
		else:
			li.setProperty("IsPlayable", "false")
		#add item to list
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=li, isFolder=isFolder,totalItems=total_items)

	def showCategories(self):
		self.addItem({'Title':SETTINGS.getLocalizedString(50003), 'mode':'latest'})
		self.addItem({'Title':SETTINGS.getLocalizedString(50000), 'mode':'series'})
		self.addItem({'Title':SETTINGS.getLocalizedString(50001), 'mode':'ovas'})
		self.addItem({'Title':SETTINGS.getLocalizedString(50002), 'mode':'movies'})
		self.endofdirectory()
		
	def showAnimeSeries(self):
		self.addItem({'Title':SETTINGS.getLocalizedString(51000), 'mode':'anime_all'})
		self.addItem({'Title':SETTINGS.getLocalizedString(51001), 'mode':'anime_airing'})
		self.addItem({'Title':SETTINGS.getLocalizedString(51002), 'mode':'anime_completed'})
		self.addItem({'Title':SETTINGS.getLocalizedString(51004), 'mode':'anime_genres'})
		self.endofdirectory()

	def animeGenre(self):
		grabFTW().getGenres()
		self.endofdirectory()
	
	def latest(self):
		grabFTW().getLatest(25)
		
	def series(self):
		cat_dict = {'ovas': 0, 'anime_all': 1, 'anime_airing': 2, 'anime_completed': 3, 'anime_genres': 4, 'movies': 5}
		if(self.main.args.category != None):
			print "[FTW] Looks like there's a filter..."
			grabFTW().getListing(category=cat_dict[self.main.args.mode], filter=self.main.args.category)
		else:
			grabFTW().getListing(cat_dict[self.main.args.mode])
	
	def episodes(self):
		grabFTW().getEpisodes(self.main.args.url, self.main.args.name, self.main.args.icon, self.main.args.mode)
		
	def startVideo(self):
		grabFTW().playVid(self.main.args.url, self.main.args.name, self.main.args.icon)

class Main:

	def __init__(self, checkMode = True):
		#self.user = None
		self.parseArgs()
		if checkMode:
			self.checkMode()

	def parseArgs(self):
		if (sys.argv[2]):
			exec "self.args = updateArgs(%s')" % (sys.argv[2][1:].replace('&', "',").replace('=', "='"))
		else:
			self.args = updateArgs(mode = 'None', url = 'None', name = 'None')

	def checkMode(self):
		mode = self.args.mode
		print "[FTW] Current mode is: " + str(self.args.mode)
		if mode is None:
			UI().showCategories()
		elif mode == 'series':
			UI().showAnimeSeries()
		elif mode == 'episode' or mode == 'movie':
			UI().episodes()
		elif mode == 'playEpisode':
			UI().startVideo()
		elif mode == 'latest':
			UI().latest()
		elif mode == 'anime_genres':
			UI().animeGenre()
		elif mode == 'anime_all' or mode == 'ovas' or mode == 'anime_airing' or mode == 'anime_completed' or mode == 'movies':
			UI().series()
