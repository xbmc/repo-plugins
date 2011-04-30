import urllib, urllib2, re, sys, os
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
		
###################################
########  Class SC2Casts  #########
###################################
				
class SC2Casts:	

	USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"
	__settings__ = xbmcaddon.Addon(id='plugin.video.sc2casts')
	__language__ = __settings__.getLocalizedString
	
	def action(self, params):
		get = params.get
		if (get("action") == "rootTop"):
			self.rootTop()
		if (get("action") == "rootBrowse"):
			self.rootBrowse()
		if (get("action") == "browseEvents"):
			self.browseEvents(params)
		if (get("action") == "browseMatchups"):
			self.browseMatchups()
		if (get("action") == "browseCasters"):
			self.browseCasters(params)
		if (get("action") == "showTitles" or get("action") == "showTitlesTop" or get("action") == "showTitlesSearch"):
			self.showTitles(params)
		if (get("action") == "showGames"):
			self.showGames(params)
	
	# ------------------------------------- Menu functions ------------------------------------- #
	
	# display the root menu
	def root(self):
		self.addCategory(self.__language__( 31000 ), 'http://sc2casts.com/index.php', 'showTitles')
		self.addCategory(self.__language__( 31001 ), '', 'rootTop')
		self.addCategory(self.__language__( 31002 ), '', 'rootBrowse')
		self.addCategory(self.__language__( 31003 ), '', 'showTitlesSearch')
	
	# display the top casts menu
	def rootTop(self):
		self.addCategory(self.__language__( 31004 ), 'http://sc2casts.com/top/index.php?all', 'showTitlesTop')
		self.addCategory(self.__language__( 31005 ), 'http://sc2casts.com/top/index.php?month', 'showTitlesTop')
		self.addCategory(self.__language__( 31006 ), 'http://sc2casts.com/top/index.php?week', 'showTitlesTop')
		self.addCategory(self.__language__( 31007 ), 'http://sc2casts.com/top/index.php', 'showTitlesTop')
	
	# display the browse casts menu
	def rootBrowse(self):
		self.addCategory(self.__language__( 31008 ), 'http://sc2casts.com/browse/index.php', 'browseEvents')
		self.addCategory(self.__language__( 31009 ), '', 'browseMatchups')
		self.addCategory(self.__language__( 31010 ), 'http://sc2casts.com/browse/index.php', 'browseCasters')
	
	# display the browse events menu
	def browseEvents(self, params = {}):
		get = params.get
		link = self.getRequest(get("url"))
		event = re.compile('<a href="/event(.*?)">(.*?)</a>').findall(link)

		for i in range(len(event)):
			self.addCategory(event[i][1], 'http://sc2casts.com/event'+event[i][0], 'showTitles')

	# display the browse casters menu
	def browseMatchups(self):
		self.addCategory('PvZ', 'http://sc2casts.com/matchups-PvZ', 'showTitles')
		self.addCategory('PvT', 'http://sc2casts.com/matchups-PvT', 'showTitles')
		self.addCategory('TvZ', 'http://sc2casts.com/matchups-TvZ', 'showTitles')
		self.addCategory('PvP', 'http://sc2casts.com/matchups-PvP', 'showTitles')
		self.addCategory('TvT', 'http://sc2casts.com/matchups-TvT', 'showTitles')
		self.addCategory('ZvZ', 'http://sc2casts.com/matchups-ZvZ', 'showTitles')
		
	# display the browse casters menu
	def browseCasters(self, params = {}):
		get = params.get
		link = self.getRequest(get("url"))
		caster = re.compile('<a href="/caster(.*?)">(.*?)</a>').findall(link)

		for i in range(len(caster)):
			self.addCategory(caster[i][1], 'http://sc2casts.com/caster'+caster[i][0], 'showTitles', len(caster))

		
	# ------------------------------------- Add functions ------------------------------------- #

	
	def addCategory(self,title,url,action, count = 0):
		url=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&title="+urllib.quote_plus(title)+"&action="+urllib.quote_plus(action)
		listitem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage="DefaultFolder.png")
		listitem.setInfo( type="Video", infoLabels={ "Title": title } )
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True, totalItems=count)
		
	def addVideo(self,title,url):
		# Check if URL is a 'fillUp' URL
		if url != 'fillUp':
			url = self.getVideoUrl(url)
		liz=xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage="DefaultVideo.png")
		liz.setInfo( type="Video", infoLabels={ "Title": title } )
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)


	# ------------------------------------- Show functions ------------------------------------- #
	
	
	def showTitles(self, params = {}):
		get = params.get
		url = get("url")
		
		# Check if user want to search
		if get("action") == 'showTitlesSearch':
			keyboard = xbmc.Keyboard('')
			keyboard.doModal()
			url = 'http://sc2casts.com/?q='+keyboard.getText()
		link = self.getRequest(url)
		
		# Get settings
		boolMatchup = self.__settings__.getSetting( "matchup" )
		boolNr_games = self.__settings__.getSetting( "nr_games" )
		boolEvent = self.__settings__.getSetting( "event" )
		boolRound = self.__settings__.getSetting( "round" )
		boolCaster = self.__settings__.getSetting( "caster" )
		
		# Get info to show
		caster = re.compile('<a href="/.+?"><span class="caster_name">(.*?)</span></a>').findall(link)
		matchup = re.compile('<span style="color:#cccccc">(.*?)</span>').findall(link)
		roundname = re.compile('<span class="round_name">(.*?)</span>').findall(link)
		checkSource = re.compile('<span class="source_name">(.*?)</span>').findall(link)
		event = re.compile('<span class="event_name".*?>(.*?)</span>').findall(link)
		
		#Different source if URL is .../top
		if get("action") == 'showTitlesTop':
			title = re.compile('<h3><a href="(.+?)"><b >(.+?)</b> vs <b >(.+?)</b>&nbsp;\((.*?)\)</a></h3>').findall(link)
		else:
			title = re.compile('<h2><a href="(.+?)"><b >(.+?)</b> vs <b >(.+?)</b> \((.*?)\)</a>').findall(link)

		for i in range(len(event)):
			if checkSource[i] != '@ YouTube':
				pass
			else:
				url = ''
				if boolMatchup == 'true':
					url += matchup[i] + ' | '

				url += title[i][1] + ' vs ' + title[i][2] + ' | '
					
				if boolNr_games == 'true':
					url += title[i][3] + ' | '
				if boolEvent == 'true':
					url += event[i] + ' | '
				if boolRound == 'true':
					url += roundname[i] + ' | '
				if boolCaster == 'true':
					url += 'cast by: ' + caster[i]
				
				self.addCategory(url,title[i][0],'showGames')
			
	def showGames(self, params = {}):
		get = params.get
		link = self.getRequest('http://sc2casts.com/'+get("url"))
		matchCount = re.compile('<div id="g(.+?)"(.+?)</div></div>').findall(link)
		
		if len(matchCount) > 0:
			for i in range(len(matchCount)):
				videoContent=re.compile('<param name="movie" value="http://www.youtube.com/v/(.+?)\?.+?"></param>').findall(matchCount[i][1])
				if len(videoContent) == 0:
					self.addVideo('Game '+ str(i+1), 'fillUp')
				if len(videoContent) == 1:
					self.addVideo('Game '+ str(i+1), videoContent[0])
				if len(videoContent) > 1:
					for k in range(len(videoContent)):
						self.addVideo('Game '+ str(i+1)+', part '+ str(k+1), videoContent[k])
		else:
			videoContent=re.compile('<param name="movie" value="http://www.youtube.com/v/(.+?)\?.+?"></param>').findall(link)
			if len(videoContent) > 1:
				for n in range(len(videoContent)):
					self.addVideo('Game 1, part '+ str(n+1), videoContent[n])
			else:
				self.addVideo('Game 1', videoContent[0])
			
			
	# ------------------------------------- Data functions ------------------------------------- #

	
	def getParams(self, paramList):	
		splitParams = paramList[paramList.find('?')+1:].split('&')
		paramsFinal = {}
		for value in splitParams:
			splitParams = value.split('=')
			type = splitParams[0]
			content = splitParams[1]
			if type == 'url':
				content = urllib.unquote_plus(content)
			paramsFinal[type] = content
		return paramsFinal
		
	def getRequest(self, url):
		req = urllib2.Request(url)
		req.add_header('User-Agent', self.USERAGENT)
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		return link
	
	def getVideoUrl(self, url):
		link = self.getRequest('http://www.youtube.com/watch?v='+url+'&safeSearch=none&hl=en_us')
		fmtSource = re.findall('"fmt_url_map": "([^"]+)"', link)
		fmt_url_map = urllib.unquote_plus(fmtSource[0]).split('|')
		links = {}
			
		for fmt_url in fmt_url_map:
			if (len(fmt_url) > 7):
				if (fmt_url.rfind(',') > fmt_url.rfind('&id=')):
					final_url = fmt_url[:fmt_url.rfind(',')]
					final_url = final_url.replace('\u0026','&')
					if (final_url.rfind('itag=') > 0):
						quality = final_url[final_url.rfind('itag=') + 5:]
						quality = quality[:quality.find('&')]
					else:
						quality = "5"
					links[int(quality)] = final_url.replace('\/','/')
				else :
					final_url = fmt_url
					if (final_url.rfind('itag=') > 0):
						quality = final_url[final_url.rfind('itag=') + 5:]
						quality = quality[:quality.find('&')]
					else :
						quality = "5"
					links[int(quality)] = final_url.replace('\/','/')
		
		hd_quality = int(self.__settings__.getSetting( "hd_videos" ))
		get = links.get
		
		# Select SD quality, standard
		if (get(35)):
			url = get(35)
		elif (get(34)):
			url = get(34)
		
		# Select HD quality if wanted
		if (hd_quality > 0): # <-- 720p
			if (get(22)):
				url = get(22)
		if (hd_quality > 1): # <-- 1080p
			if (get(37)):
				url = get(37)
				
		return url
		