import sys
import os
import re
import md5
import time
import urllib
import urllib2
import httplib
import cookielib
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import simplejson as json
from BeautifulSoup import BeautifulSoup

__settings__ = sys.modules[ "__main__" ].__settings__

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
		self.currenturl = None
		self.referer = None
		self.opener = None
		self.settings = {}
		self.addon = xbmcaddon.Addon(id='plugin.video.animeftw')
		self.base_cache_path = xbmc.translatePath(self.addon.getAddonInfo('profile'))
		self.settings['username'] = __settings__.getSetting("crunchy_username")
		self.settings['password'] = __settings__.getSetting("crunchy_password")
		self.settings['prev_username'] = __settings__.getSetting("prev_username")
		self.settings['prev_password'] = __settings__.getSetting("prev_password")
		self.resp = None
		
		if self.settings['username'] == '' or self.settings['password'] == '':
			self.resp = xbmcgui.Dialog().yesno("No username/password set!","AnimeFTW.tv requires you to be logged in to view", \
			"videos.  Would you like to log-in now?")
			if self.resp:
				__settings__.openSettings()
				
		elif self.settings['username'] != self.settings['prev_username'] or self.settings['password'] != self.settings['prev_password']:
			self.removeCookie = True
		else:
			self.removeCookie = False

	def login(self):
		if (self.settings['username'] != '' and self.settings['password'] != ''):
			
			COOKIEFILE=os.path.join(self.base_cache_path, 'cookieftw.lwp')
			if self.removeCookie == True:
				try:
					"FTW --> COOKIEFILE DELETED"
					os.remove(COOKIEFILE)
				except:
					pass
			cj = cookielib.LWPCookieJar()
			if os.path.exists(COOKIEFILE):
				print "FTW -- > Already have the cookie!"
				status = self.checkCookie(COOKIEFILE)
				if status is True:
					print "FTW --> Login succeeded."
					cj.load(COOKIEFILE)
					__settings__.setSetting("prev_username", self.settings['username'])
					__settings__.setSetting("prev_password", self.settings['password'])
				else:
					ex = 'XBMC.Notification("Login Failed:","Username/password is incorrect.", 3000)'
					xbmc.executebuiltin(ex)
					os.remove(COOKIEFILE)

			self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
			self.referer = 'https://www.animeftw.tv/login'
			self.opener.addheaders = [('Referer', self.referer),('User-Agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')]

			if not os.path.exists(COOKIEFILE):
				print "FTW --> Cookie missing--attempting login!!!"
				url = 'https://www.animeftw.tv/login.php'
				data = urllib.urlencode({'_submit_check':'1', 'last_page':'http://www.animeftw.tv/videos','username':self.settings['username'],'password':self.settings['password'],'submit':'Sign In', 'remember':'on'})
				urllib2.install_opener(self.opener)
				try:
					req = self.opener.open(url, data)
					req.close()
					cj.save(COOKIEFILE)
					status = self.checkCookie(COOKIEFILE)
					if status == True:
						__settings__.setSetting("prev_username", self.settings['username'])
						__settings__.setSetting("prev_password", self.settings['password'])
				except:
					ex = 'XBMC.Notification("Server Error:","Please try again.", 3000)'
					xbmc.executebuiltin(ex)
			
			return self.opener, status
		else:
			if self.resp:
				return self.opener, False
			else:
				return self.opener, 'exit'
		
	def checkCookie(self, COOKIEFILE):
		file = open(COOKIEFILE,'r').read()
		auth = re.search('authenticate=[0-9a-h]{32}', file)
		if auth != None:
			return True
		else:
			return False
		
class grabFTW:
	def __init__(self, *args, **kwargs):
		self.opener, self.status = LoginFTW().login()
		if not self.status:
			self.opener, self.status = LoginFTW().login()
		elif self.status is 'exit':
			xbmc.executebuiltin('XBMC.Notification("Please Login:","A user account is required to view content.", 3000)')
		self.addon = xbmcaddon.Addon(id='plugin.video.animeftw')
		self.base_cache_path = xbmc.translatePath(self.addon.getAddonInfo('profile'))
		
	def downloadHTML(self, url):
		self.currenturl = url
		self.opener.addheaders = [('Referer', self.referer),('User-Agent','Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.14) Gecko/20080404 Firefox/2.0.0.14')]
		response = self.opener.open(self.currenturl)
		html = response.read()
		print "FTW --> GRABBING URL: "+self.currenturl
		self.referer = self.currenturl
		return html
		
	def getHTML(self, url):	
		self.currenturl = url
		htmlSource = None
		max_age = 3*60*60
		thumbprint = md5.new(self.currenturl).hexdigest()
		thumbprint += ".tmp"
		cache_dir = os.path.join(self.base_cache_path, "cache/");
		if not os.path.exists(cache_dir):
			os.makedirs(cache_dir)
		cache_file = os.path.join(cache_dir, thumbprint)
		if os.path.exists(cache_file):
			cache_modified_time = os.stat(cache_file).st_mtime
			time_now = time.time()
			if cache_modified_time < time_now - max_age:
				print "FTW --> Cache is too old..."
				htmlSource = self.downloadHTML(self.currenturl)
				file = open(cache_file, 'w')
				file.write(htmlSource)
				file.close()
			else:
				htmlSource = open(cache_file, 'r').read()
		else:
			htmlSource = self.downloadHTML(self.currenturl)
			file = open(cache_file, 'w')
			file.write(htmlSource)
			file.close()	
			
		return htmlSource
		
	def getInfo(self, title):
		enableThumbs = __settings__.getSetting("get_ext")
		info = {}
		if(enableThumbs == "true"):
			thumbprint = md5.new(title).hexdigest()
			thumbprint += ".nfo"
			cache_dir = os.path.join(self.base_cache_path, "cache/")
			cache_file = os.path.join(cache_dir, thumbprint)
			if os.path.exists(cache_file):
				datapool = open(cache_file, 'r')
				datapool = datapool.read()
				datapool = json.loads(datapool)
			else:
				try:
					url = "http://mal-api.com/anime/search?q="
					url += urllib.quote(title)
					datapool = urllib2.urlopen(url)
					datapool = datapool.read()
					file = open(cache_file, 'w')
					file.write(datapool)
					file.close()
					datapool = json.loads(datapool)
				except:
					print "FTW --> Could not open MAL-API link for series "+str(title)
					datapool = []
			
			if len(datapool) > 0:
				info['thumb'] = str(datapool[0]['image_url'].replace("t.jpg",".jpg"))
				info['plot'] = unicode(datapool[0]['synopsis'].replace('<br>','\n')).encode('utf-8')
				info['genre'] = ', '.join(datapool[0]['genres'])
				info['rating'] = float(datapool[0]['members_score'])
			else:
				info['thumb'] = 'None'
				info['plot'] = 'No plot info available for this series.'
				info['genre'] = 'None'
				info['rating'] = 0.0
		else:
			info['thumb'] = 'None'
			info['plot'] = 'No plot info available for this series.'
			info['genre'] = 'None'
			info['rating'] = 0.0
			
		return info
		
	def getLatest(self):
		if self.status is True:	
			self.referer = "http://www.animeftw.tv/"
			htmlSource = self.getHTML("http://www.animeftw.tv")
			soup = BeautifulSoup(htmlSource)
			latest_list = soup.find('div', attrs={'class':'pad_good'}).findAll('div', attrs={'align':'center'})
			latestList = []
			for post in latest_list:
				postDict = {}
				epTitle = post.find('span').contents[0].replace('`', '\'')
				showTitle = post.find('a').contents[0].replace('`', '\'')
				info = self.getInfo(showTitle)
				postDict['url'] = post.find('a')['href']
				postDict['name'] = showTitle +" - "+ epTitle
				showInfo = {'name': postDict['name'], 'url':"http://www.animeftw.tv"+postDict['url'], 'thumb':info['thumb'], 'plot':info['plot'], 'rating':info['rating'], 'genre': info['genre']}
				UI().addItem({'Title':postDict['name'], 'mode':'episodes', 'referer':self.referer, 'url':"http://www.animeftw.tv"+postDict['url'], 'Thumb':showInfo['thumb']}, showInfo, True, len(latest_list))
			UI().endofdirectory()
		
	def getAllSeries(self, category = 0):
		if self.status is True:
			self.referer = "http://www.animeftw.tv/"
			htmlSource = self.getHTML("http://www.animeftw.tv/videos")
			soup = BeautifulSoup(htmlSource)
			airing_list = soup.find('ul', attrs={'id':'ddsubmenu2'}).find('ul').findAll('li')
			completed_list = soup.find('ul', attrs={'id':'ddsubmenu2'}).find(text='Completed Series').findNext('ul').findAll('ul')
			completed_list = BeautifulSoup(str(completed_list))
			completed_list = completed_list.findAll('li')
			series_list = airing_list + completed_list
			del soup
			del airing_list
			del completed_list
			for series in series_list:
				series = series.find('a')
				seriesname = series.contents[0].replace('&nbsp;','').replace('`', '\'')
				info = self.getInfo(seriesname)
				seriesdict = {'name': seriesname, 'url':"http://www.animeftw.tv"+series['href'], 'thumb':info['thumb'], 'plot':info['plot'], 'rating':info['rating'], 'genre': info['genre']}
				UI().addItem({'Title':seriesdict['name'], 'mode':'episodes', 'referer':self.referer, 'url':seriesdict['url'], 'category':'anime_all', 'Thumb':seriesdict['thumb']}, seriesdict, True, len(series_list))
			del series_list
			UI().endofdirectory('title')
		
	def getOVAs(self):
		if self.status is True:
			self.referer = "http://www.animeftw.tv/"
			htmlSource = self.getHTML("http://www.animeftw.tv/videos")
			soup = BeautifulSoup(htmlSource)
			completed_list = soup.find('ul', attrs={'id':'ddsubmenu2'}).find(text='OVA Series').findNext('ul').findAll('li')
			del soup
			for series in completed_list:
				series = series.find('a')
				seriesname = series.contents[0].replace('&nbsp;','').replace('`', '\'')
				info = self.getInfo(seriesname)
				series = {'name':seriesname, 'url':"http://www.animeftw.tv"+series['href'], 'thumb':info['thumb'], 'plot':info['plot'], 'rating':info['rating'], 'genre': info['genre']}
				UI().addItem({'Title':series['name'], 'mode':'episodes', 'referer':self.referer, 'url':series['url'], 'category':'ovas', 'Thumb':series['thumb']}, series, True, len(completed_list))
			del completed_list
			UI().endofdirectory('none')
		
	def getMovies(self):
		if self.status is True:
			self.referer = "http://www.animeftw.tv/"
			htmlSource = self.getHTML("http://www.animeftw.tv/movies")
			soup = BeautifulSoup(htmlSource)
			completed_list = soup.find('table', attrs={'width':'100%'}).findAll('tr')
			del soup
			for movie in completed_list:
				cells = movie.findAll('td')
				cell = cells[0].find('img')
				cell2 = movie.findAll('a', attrs={'href' : re.compile("http://www.animeftw.tv/movies/")})
				if len(cell2) > 1:
					for vid in cell2:
						vid_name = vid.string.split(', ')
						movie = {'name':vid_name[1], 'url':vid['href'], 'thumb':cell['src']}
						UI().addItem({'Title':movie['name'], 'mode':'episode', 'referer':self.referer, 'url':movie['url'], 'category':'movies', 'Thumb':movie['thumb']}, None, True, len(completed_list))
				else:
					movie = {'name':cell['title'].replace('`', '\''), 'url':cell2[0]['href'], 'thumb':cell['src']}	
					UI().addItem({'Title':movie['name'], 'mode':'episode', 'referer':self.referer, 'url':movie['url'], 'category':'movies', 'Thumb':movie['thumb']}, None, True, len(completed_list))
			del completed_list
			UI().endofdirectory('none')
		
	def getAiringSeries(self):
		if self.status is True:
			self.referer = "http://www.animeftw.tv/"
			htmlSource = self.getHTML("http://www.animeftw.tv/videos")
			soup = BeautifulSoup(htmlSource)
			airing_list = soup.find('ul', attrs={'id':'ddsubmenu2'}).find('ul').findAll('li')
			del soup
			for series in airing_list:
				series = series.find('a')
				seriesname = series.contents[0].replace('&nbsp;','').replace('`', '\'')
				info = self.getInfo(seriesname)
				series = {'name':seriesname, 'url':"http://www.animeftw.tv"+series['href'], 'thumb':info['thumb'], 'plot':info['plot'], 'rating':info['rating'], 'genre': info['genre']}
				UI().addItem({'Title':series['name'], 'mode':'episodes', 'referer':self.referer, 'url':series['url'], 'Thumb':series['thumb']}, series, True, len(airing_list))
			del airing_list
			UI().endofdirectory('title')
		
	def getCompletedSeries(self):
		if self.status is True:
			self.referer = "http://www.animeftw.tv/"
			htmlSource = self.getHTML("http://www.animeftw.tv/videos")
			soup = BeautifulSoup(htmlSource)
			completed_list = soup.find('ul', attrs={'id':'ddsubmenu2'}).find(text='Completed Series').findNext('ul').findAll('ul')
			completed_list = BeautifulSoup(str(completed_list))
			completed_list = completed_list.findAll('li')
			del soup
			for series in completed_list:
				series = series.find('a')
				seriesname = series.contents[0].replace('&nbsp;','').replace('`', '\'')
				info = self.getInfo(seriesname)
				series = {'name':seriesname, 'url':"http://www.animeftw.tv"+series['href'], 'thumb':info['thumb'], 'plot':info['plot'], 'rating':info['rating'], 'genre': info['genre']}
				UI().addItem({'Title':series['name'], 'mode':'episodes', 'referer':self.referer, 'url':series['url'], 'Thumb':series['thumb']}, series, True, len(completed_list))
			del completed_list
			UI().endofdirectory('title')
	
	def getGenreSeries(self, id):
		if self.status is True:
			self.referer = "http://www.animeftw.tv/videos"
			htmlSource = self.getHTML("http://www.animeftw.tv/videos/sort/"+id)
			soup = BeautifulSoup(htmlSource)
			container = soup.find('div', attrs={'id':'left_side'})
			genre_list = container.findAll(href=re.compile('/videos/.*/'))
			del genre_list[0:10]
			del soup
			for series in genre_list:
				seriesname = series.string.replace('`', '\'')
				info = self.getInfo(seriesname)
				series = {"name":seriesname, "url":"http://www.animeftw.tv"+series['href'], 'thumb':info['thumb'], 'plot':info['plot'], 'rating':info['rating'], 'genre': info['genre']}
				UI().addItem({'Title':series['name'], 'mode':'episodes', 'referer':self.referer, 'url':series['url'], 'Thumb':series['thumb']}, series, True, len(genre_list))
			del genre_list
			UI().endofdirectory('title')
		
	def getEpisodes(self, url, referer, category = None):
		if self.status is True:
			self.referer = referer
			htmlSource = self.getHTML(url)
			soup = BeautifulSoup(htmlSource)
			content_table = soup.find('table', attrs={'width':'100%'})
			content_tr = content_table.findAll('tr')
			content_td = content_tr[int(len(content_tr))-1].findAll('td')
			content = content_td[int(len(content_td))-1].findAll('div')
			del soup
			del content_tr
			del content_td
			for i, item in enumerate(content):
				itemname = str(item.contents[0]) + item.a.string.replace('`', '\'')
				list_item = {'name':unicode(itemname).encode('utf-8'), 'url':item.a['href'], 'thumb':'None', 'plot':'None'}
				UI().addItem({'Title':list_item['name'],'mode':'episode', 'referer':self.referer, 'url':list_item['url']}, None, True, len(content))
			del content
			UI().endofdirectory('none')
			
	def getVidLink(self, url, referer, name):
		self.referer = referer
		self.name = name
		htmlSource = self.getHTML(url)
		r_src = re.compile('(src="(.*).divx")|(src="(.*).mkv")')
		src = re.search(r_src, htmlSource)
		src = src.group()
		src = src.replace('src="','').replace('"','')
		self.playVid(src, self.referer, self.name)
		
	def playVid(self, url, referer, name):
		stream_url = url+"?bar=1|Referer="+referer
		item = xbmcgui.ListItem(name)
		xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(stream_url, item)

class UI:
	
	def __init__(self):
		self.main = Main(checkMode = False)
		xbmcplugin.setContent(int(sys.argv[1]), 'movies')
	
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
		info.setdefault('referer','None')
		info.setdefault('Icon', info['Thumb'])
		#create params for xbmcplugin module
		u = sys.argv[0]+\
			'?url='+urllib.quote_plus(info['url'])+\
			'&mode='+urllib.quote_plus(info['mode'])+\
			'&name='+urllib.quote_plus(info['Title'])+\
			'&id='+urllib.quote_plus(info['id'])+\
			'&category='+urllib.quote_plus(info['category'])+\
			'&referer='+urllib.quote_plus(info['referer'])+\
			'&icon='+urllib.quote_plus(info['Thumb'])
		#create list item
		if extrainfo != None:
			li=xbmcgui.ListItem(label = extrainfo['name'], iconImage = info['Icon'], thumbnailImage = info['Thumb'])
			li.setInfo( type="Video", infoLabels={ "Title":extrainfo['name'], "Plot":extrainfo['plot'], "Genre":extrainfo['genre'], 'Rating':extrainfo['rating']})
		else:
			li=xbmcgui.ListItem(label = info['Title'], iconImage = info['Icon'], thumbnailImage = info['Thumb'])
		#for videos, replace context menu with queue and add to favorites
		if not isFolder:
			li.setProperty("IsPlayable", "true")#let xbmc know this can be played, unlike a folder.
			#add context menu items to non-folder items.
			contextmenu = [('Queue Video', 'Action(Queue)')]
		#for folders, completely remove contextmenu, as it is totally useless.
		else:
			li.addContextMenuItems([], replaceItems=True)
			li.setProperty("IsPlayable", "true")
		#add item to list
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=li, isFolder=isFolder,totalItems=total_items)

	def showCategories(self):
		self.addItem({'Title':__settings__.getLocalizedString(50003), 'mode':'latest', 'cateogry':'series'})
		self.addItem({'Title':__settings__.getLocalizedString(50000), 'mode':'series', 'category':'series'})
		self.addItem({'Title':__settings__.getLocalizedString(50001), 'mode':'ovas', 'category':'series'})
		self.addItem({'Title':__settings__.getLocalizedString(50002), 'mode':'movies', 'category':'movie'})
		self.endofdirectory()
		
	def showAnimeSeries(self):
		self.addItem({'Title':__settings__.getLocalizedString(51000), 'mode':'anime_all'})
		self.addItem({'Title':__settings__.getLocalizedString(51001), 'mode':'anime_airing'})
		self.addItem({'Title':__settings__.getLocalizedString(51002), 'mode':'anime_completed'})
		self.addItem({'Title':__settings__.getLocalizedString(51004), 'mode':'anime_genre'})
		self.endofdirectory()

	def animeGenre(self):
		self.addItem({'Title':__settings__.getLocalizedString(50005), 'mode':'anime_withtag','id':'Action'})
		self.addItem({'Title':__settings__.getLocalizedString(50006), 'mode':'anime_withtag','id':'Adventure'})
		self.addItem({'Title':__settings__.getLocalizedString(50007), 'mode':'anime_withtag','id':'Aliens'})
		self.addItem({'Title':__settings__.getLocalizedString(50008), 'mode':'anime_withtag','id':'Angst'})
		self.addItem({'Title':__settings__.getLocalizedString(50009), 'mode':'anime_withtag','id':'Bishounen'})
		self.addItem({'Title':__settings__.getLocalizedString(50010), 'mode':'anime_withtag','id':'Bounty%20Hunters'})
		self.addItem({'Title':__settings__.getLocalizedString(50011), 'mode':'anime_withtag','id':'Clubs'})
		self.addItem({'Title':__settings__.getLocalizedString(50012), 'mode':'anime_withtag','id':'Comedy'})
		self.addItem({'Title':__settings__.getLocalizedString(50013), 'mode':'anime_withtag','id':'Coming%20of%20Age'})
		self.addItem({'Title':__settings__.getLocalizedString(50014), 'mode':'anime_withtag','id':'Conspiracy'})
		self.addItem({'Title':__settings__.getLocalizedString(50015), 'mode':'anime_withtag','id':'Contemporary%20Fantasy'})
		self.addItem({'Title':__settings__.getLocalizedString(50016), 'mode':'anime_withtag','id':'Cyberpunk'})
		self.addItem({'Title':__settings__.getLocalizedString(50017), 'mode':'anime_withtag','id':'Daily%20Life'})
		self.addItem({'Title':__settings__.getLocalizedString(50018), 'mode':'anime_withtag','id':'Demons'})
		self.addItem({'Title':__settings__.getLocalizedString(50019), 'mode':'anime_withtag','id':'Detective'})
		self.addItem({'Title':__settings__.getLocalizedString(50020), 'mode':'anime_withtag','id':'Dystopia'})
		self.addItem({'Title':__settings__.getLocalizedString(50021), 'mode':'anime_withtag','id':'Ecchi'})
		self.addItem({'Title':__settings__.getLocalizedString(50022), 'mode':'anime_withtag','id':'Elementary%20School'})
		self.addItem({'Title':__settings__.getLocalizedString(50023), 'mode':'anime_withtag','id':'Elves'})
		self.addItem({'Title':__settings__.getLocalizedString(50024), 'mode':'anime_withtag','id':'Fantasy'})
		self.addItem({'Title':__settings__.getLocalizedString(50025), 'mode':'anime_withtag','id':'Female%20Students'})
		self.addItem({'Title':__settings__.getLocalizedString(50026), 'mode':'anime_withtag','id':'Gunfights'})
		self.addItem({'Title':__settings__.getLocalizedString(50027), 'mode':'anime_withtag','id':'Harem'})
		self.addItem({'Title':__settings__.getLocalizedString(50028), 'mode':'anime_withtag','id':'High%20School'})
		self.addItem({'Title':__settings__.getLocalizedString(50029), 'mode':'anime_withtag','id':'Historical'})
		self.addItem({'Title':__settings__.getLocalizedString(50030), 'mode':'anime_withtag','id':'Horror'})
		self.addItem({'Title':__settings__.getLocalizedString(50031), 'mode':'anime_withtag','id':'Humanoid'})
		self.addItem({'Title':__settings__.getLocalizedString(50032), 'mode':'anime_withtag','id':'Idol'})
		self.addItem({'Title':__settings__.getLocalizedString(50033), 'mode':'anime_withtag','id':'Love%20Polygon'})
		self.addItem({'Title':__settings__.getLocalizedString(50034), 'mode':'anime_withtag','id':'Magical'})
		self.addItem({'Title':__settings__.getLocalizedString(50035), 'mode':'anime_withtag','id':'Martial%20Arts'})
		self.addItem({'Title':__settings__.getLocalizedString(50036), 'mode':'anime_withtag','id':'Mecha'})
		self.addItem({'Title':__settings__.getLocalizedString(50037), 'mode':'anime_withtag','id':'Military'})
		self.addItem({'Title':__settings__.getLocalizedString(50038), 'mode':'anime_withtag','id':'Music'})
		self.addItem({'Title':__settings__.getLocalizedString(50039), 'mode':'anime_withtag','id':'Novel'})
		self.addItem({'Title':__settings__.getLocalizedString(50040), 'mode':'anime_withtag','id':'Nudity'})
		self.addItem({'Title':__settings__.getLocalizedString(50041), 'mode':'anime_withtag','id':'Parallel%20Universe'})
		self.addItem({'Title':__settings__.getLocalizedString(50042), 'mode':'anime_withtag','id':'Parody'})
		self.addItem({'Title':__settings__.getLocalizedString(50043), 'mode':'anime_withtag','id':'Piloted%20Robots'})
		self.addItem({'Title':__settings__.getLocalizedString(50044), 'mode':'anime_withtag','id':'Post-apocalyptic'})
		self.addItem({'Title':__settings__.getLocalizedString(50045), 'mode':'anime_withtag','id':'School%20Life'})
		self.addItem({'Title':__settings__.getLocalizedString(50046), 'mode':'anime_withtag','id':'SciFi'})
		self.addItem({'Title':__settings__.getLocalizedString(50047), 'mode':'anime_withtag','id':'Seinen'})
		self.addItem({'Title':__settings__.getLocalizedString(50048), 'mode':'anime_withtag','id':'Shoujo'})
		self.addItem({'Title':__settings__.getLocalizedString(50049), 'mode':'anime_withtag','id':'Shounen'})
		self.addItem({'Title':__settings__.getLocalizedString(50050), 'mode':'anime_withtag','id':'Slapstick'})
		self.addItem({'Title':__settings__.getLocalizedString(50051), 'mode':'anime_withtag','id':'Space%20Travel'})
		self.addItem({'Title':__settings__.getLocalizedString(50052), 'mode':'anime_withtag','id':'Special%20Squads'})
		self.addItem({'Title':__settings__.getLocalizedString(50053), 'mode':'anime_withtag','id':'Sports'})
		self.addItem({'Title':__settings__.getLocalizedString(50054), 'mode':'anime_withtag','id':'Sudden%20Girlfriend%20Appearance'})
		self.addItem({'Title':__settings__.getLocalizedString(50055), 'mode':'anime_withtag','id':'Swordplay'})
		self.addItem({'Title':__settings__.getLocalizedString(50056), 'mode':'anime_withtag','id':'Thriller'})
		self.addItem({'Title':__settings__.getLocalizedString(50057), 'mode':'anime_withtag','id':'Tragedy'})
		self.addItem({'Title':__settings__.getLocalizedString(50058), 'mode':'anime_withtag','id':'Underworld'})
		self.addItem({'Title':__settings__.getLocalizedString(50059), 'mode':'anime_withtag','id':'Vampires'})
		self.addItem({'Title':__settings__.getLocalizedString(50060), 'mode':'anime_withtag','id':'Virtual%20Reality'})
		self.addItem({'Title':__settings__.getLocalizedString(50061), 'mode':'anime_withtag','id':'World%20War%20II'})
		self.endofdirectory()
		
	def series(self):
		cat_dict = {'ovas':0,'movies':1,'anime_all':2}
		if(self.main.args.mode == 'anime_all'):
			grabFTW().getAllSeries(cat_dict[self.main.args.mode])
		elif(self.main.args.mode == 'ovas'):
			grabFTW().getOVAs()
			
	def latestAdditions(self):
		grabFTW().getLatest()
		
	def movies(self):
		grabFTW().getMovies()
			
	def airing(self):
		grabFTW().getAiringSeries()
		
	def completed(self):
		grabFTW().getCompletedSeries()
		
	def seriesGenre(self):
		grabFTW().getGenreSeries(self.main.args.id)
			
	def episodes(self):
		grabFTW().getEpisodes(self.main.args.url, self.main.args.referer, self.main.args.category)
		
	def startVideo(self):
		grabFTW().getVidLink(self.main.args.url, self.main.args.referer, self.main.args.name)

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
		if mode is None:
			UI().showCategories()
		elif mode == 'latest':
			UI().latestAdditions()
		elif mode == 'series':
			UI().showAnimeSeries()
		elif mode == 'anime_airing':
			UI().airing()
		elif mode == 'anime_completed':
			UI().completed()
		elif mode == 'anime_genre':
			UI().animeGenre()
		elif mode == 'anime_withtag':
			UI().seriesGenre()
		elif mode == 'featured':
			UI().featured()
		elif mode == 'anime_all' or mode == 'ovas':
			UI().series()
		elif mode == 'movies':
			UI().movies()
		elif mode == 'episodes':
			UI().episodes()
		elif mode == 'episode':
			UI().startVideo()