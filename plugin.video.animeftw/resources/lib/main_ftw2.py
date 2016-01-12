import os
import sys
import json
import urllib
import requests
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

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
		self.settings['token'] = SETTINGS.getSetting("token")
		self.params = {"devkey":"hVhS-672s-sKhK-yUn0"}
	
	def checkLogin(self):
		# checking if the token is not set.
		if self.settings['token'] == '':
			# first, if the token isnt set, but the username and password is.
			# Create the token, and continue on with the process.
			if self.settings['username'] == '' or self.settings['password'] == '':				
				self.loginOptions(0)
			else:
				# we will build the the token since username and password are set.
				response = self.validateLogin(SETTINGS.getSetting("username_ftw"), SETTINGS.getSetting("password_ftw"))
				response = json.loads(response)
				if 'status' in response and response['status'] == "200":
					# Successful login, return the token.
					SETTINGS.setSetting(id="token", value=response['message'])
					SETTINGS.setSetting(id="password_ftw", value="")
					return response['message'] # this is the token.
				else:
					self.loginOptions(2)
		else:
			# validate the token.
			response = self.validateToken(self.settings['token'])
			response = json.loads(response)
			if response['status'] == "500":
				# the validation was successful.
				return self.settings['token']
			else:
				SETTINGS.setSetting(id="token", value="")
				self.loginOptions(1)
		
	def validateLogin(self, username, password):
		self.url = "https://www.animeftw.tv/api/v2/"
		self.actionData = self.params # build in the parameters first.
		self.actionData.update({"username":username,"password":password,"remember":"true"})
		self.headers = {'content-type': 'application/json'}
		print "[AFTW DATA] Login Data:"
		print self.params
		#Send the data to the server
		response = requests.post(self.url,data=self.actionData)
		finalResponse = response.text
		return finalResponse
		
	def validateToken(self, token):
		self.url = "https://www.animeftw.tv/api/v2/"
		self.actionData = self.params # build in the parameters first.
		self.actionData.update({"token":token,"action":"validate-token"})
		self.headers = {'content-type': 'application/json'}
		#Send the data to the server
		response = requests.post(self.url,data=self.actionData)
		finalResponse = response.text
		SETTINGS.setSetting(id="password_ftw", value="")
		return finalResponse
		
	def loginOptions(self, type):
		if type == 0:
			self.resp = xbmcgui.Dialog().yesno("You are not currently logged in.","AnimeFTW.tv requires you to be logged in to view videos. Would you like to log-in now?")
		elif type == 2:
			self.resp = xbmcgui.Dialog().yesno("Username or Password incorrect.","Please log in again.")
		else:
			self.resp = xbmcgui.Dialog().yesno("Session Expired!","Your existing session has expired. Would you like to log-in again?")
			
		if self.resp:
			self.respLogin = SETTINGS.openSettings()
					
			if SETTINGS.getSetting("username_ftw") == '' or SETTINGS.getSetting("password_ftw") == '':
				xbmc.executebuiltin('XBMC.Notification("Please Login:","An Advanced member account is required to view more than 2 episodes of a series.", 3000)')
				return ''
			else:
				response = self.validateLogin(SETTINGS.getSetting("username_ftw"), SETTINGS.getSetting("password_ftw"))
				response = json.loads(response)
				if 'status' in response and response['status'] == "200":
					# Successful login, return the token.
					SETTINGS.setSetting(id="password_ftw", value="")
					SETTINGS.setSetting(id="token", value=response['message'])
					return response['message'] # this is the token.
				else:
					xbmc.executebuiltin('XBMC.Notification("Please Login:","Your Username or Password were not valid, please try again.", 3000)')
		else:
			xbmc.executebuiltin('XBMC.Notification("Please Login:","An account is required to view videos.", 3000)')
			return ''
		
	
class grabFTW:
	
	def __init__(self, *args, **kwargs):
		self.settings = {}
		self.settings['token'] = LoginFTW().checkLogin()
		self.params = {"devkey":"hVhS-672s-sKhK-yUn0","token":self.settings['token']}

	def getContent(self, data, action):
		self.currentAction = action
		self.url = "https://www.animeftw.tv/api/v2/"
		self.actionData = self.params # build in the parameters first.
		self.actionData.update(data) # combine with the data supplied by the various functions.
		jsonSource = None
		response = requests.post(self.url,data=self.actionData)
		jsonSource = response.text
		return jsonSource
		
	def getLatestEpisodes(self, count = 30):
		data = {"action":"display-episodes","latest":"true","start":"0","count":str(count)}
		action = "Display Latest Episodes"
		jsonSource = self.getContent(data, action)
		parsed_json = json.loads(jsonSource)
		if 'status' in parsed_json and parsed_json['status'] == "200":
			latest_results = parsed_json['results']
			print latest_results
			for episode in latest_results:
				UI().addItem({'Seriesname': unicode(episode['fullSeriesName'].replace('`', '\'')).encode('utf-8'), 'Title': unicode(episode['fullSeriesName'].replace('`', '\'') + " - " + episode['epnumber'] + " - " + episode['epname'].replace('`', '\'')).encode('utf-8'), 'mode': 'playEpisode', 'url': episode['video'] })
			del latest_results	
			UI().endofdirectory('title')
		else :
			self.resp = xbmcgui.Dialog().ok("Something went wrong!","Please try again, if you see this more than once uninstall and reinstall the plugin.")
	
	def getWatchlist(self, count = 25):
		data = {"action":"display-mywatchlist","start":"0","count":"30"}
		action = "Display My WatchList Entries"
		jsonSource = self.getContent(data, action)
		parsed_json = json.loads(jsonSource)
		watchlist_results = parsed_json['results']
		
		for series in watchlist:
			UI().addItem({'Seriesname': unicode(series['fullSeriesName'].replace('`', '\'')).encode('utf-8'), 'Title': unicode(series['series'].replace('`', '\'') + ", Watched to Ep " + series['last-episode']).encode('utf-8'),'mode': 'episodes', 'url': series['href']})
		del watchlist
		UI().endofdirectory('series')
		
	def getGenres(self):
		data = {"action":"display-categories","start":"0","count":"200"}
		action = "Display Category Listing."
		jsonSource = self.getContent(data, action)
		parsed_json = json.loads(jsonSource)
		if 'status' in parsed_json and parsed_json['status'] == "200":
			tag_results = parsed_json['results']
			for tag in tag_results:
				UI().addItem({'Title': unicode(tag['name'].replace('`', '\'')).encode('utf-8'), 'mode': 'anime_all', 'category': tag['id']})
			del tag_results
			UI().endofdirectory('title')
		else :
			self.resp = xbmcgui.Dialog().ok("Something went wrong!","Please try again, if you see this more than once uninstall and reinstall the plugin.")
		
	def getListing(self, category = 0, showType = 'anime', count = 2000, filter = None):
		if showType == 'anime':
			display = 'display-series'
		else:
			display = 'display-series'
			
		data = {"action":display,"start":"0","count":str(count)}
		action = "Display Category Listing."
		print "[AFTW] FILTER is set to: " + str(filter)
		
		if filter:
			data.update({"filter":str(filter)})
		
		jsonSource = self.getContent(data, action)
		parsed_json = json.loads(jsonSource)
		
		cat_list = ['episode', 'episode', 'episode', 'episode', 'episode', 'movie']
		videoType = cat_list[category]
		print "[AFTW] Current video type: " + str(videoType)
		
		if 'status' in parsed_json and parsed_json['status'] == "200":
			series_results = parsed_json['results']
			for series in series_results:
				moviesonly = int(series['moviesonly'])
				numberOfEpisodes = 1
				isAiring = int(series['stillRelease'])
				if moviesonly == 1 and numberOfEpisodes == 1 and category != 5:
					continue
				elif moviesonly < 1 and category == 5:
					continue
				elif isAiring == 0 and category == 2:
					continue
				elif isAiring == 1 and category == 3:
					continue
				else:				
					seriesdict = {'id': series['id'], \
								  'name': unicode(series['fullSeriesName'].replace('`', '\'')).encode('utf-8'), \
								  'nameorig': unicode(series['romaji']).encode('utf-8'), \
								  'url': '0', \
								  'thumb': series['image'], \
								  'plot':unicode(series['description']).encode('utf-8'), \
								  'rating': int(series['reviews-average-stars']), \
								  'episodes': numberOfEpisodes, \
								  'genre': unicode(series['category']).encode('utf-8') }
								  
					UI().addItem({'Title':seriesdict['name'], 'mode': videoType, 'url':seriesdict['url'], 'Thumb':seriesdict['thumb'], 'id':seriesdict['id']}, seriesdict, True, len(series_results))
					
			del series_results
			UI().endofdirectory('title')
		else :
			self.resp = xbmcgui.Dialog().ok("Something went wrong!","Please try again, if you see this more than once uninstall and reinstall the plugin.")
		
	def getEpisodes(self, url, seriesid = None, seriesimage = None, category = None):
		data = {"id":seriesid,"action":"display-episodes","start":"0","count":"300"}
		action = "Display Category Listing."
		jsonSource = self.getContent(data, action)
		parsed_json = json.loads(jsonSource)
		
		if 'status' in parsed_json and parsed_json['status'] == "200":
			episode_results = parsed_json['results']	
			
			for episode in episode_results:
				if category == 'episode':
					epname = unicode(episode['epnumber'] + ".) " + episode['epname'].replace('`', '\'')).encode('utf-8')
				else:
					epname = unicode(episode['epname'].replace('`', '\'')).encode('utf-8')
				
				url = episode['video']
				thumbnail = episode['image']
				if thumbnail == "http://img02.animeftw.tv/video-images/noimage.png":
					thumbnail = seriesimage
				
				li = xbmcgui.ListItem(epname, path = url, thumbnailImage = thumbnail)
				li.setInfo(type="Video", infoLabels={ "Title": epname })
				li.setProperty("IsPlayable","true");
				xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=False)
			UI().endofdirectory()
		else :
			self.resp = xbmcgui.Dialog().ok("Something went wrong!","Please try again, if you see this more than once uninstall and reinstall the plugin.")
		
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
		#self.addItem({'Title':SETTINGS.getLocalizedString(50004), 'mode':'watchlist'})
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

	def watchlist(self):
		grabFTW().getWatchlist()
	
	def latest(self):
		grabFTW().getLatestEpisodes(25)
		
	def series(self):
		cat_dict = {'ovas': 0, 'anime_all': 1, 'anime_airing': 2, 'anime_completed': 3, 'anime_genres': 4, 'movies': 5}
		if(self.main.args.category != None):
			print "[FTW] Looks like there's a filter..."
			grabFTW().getListing(category=cat_dict[self.main.args.mode], filter=self.main.args.category)
		else:
			grabFTW().getListing(cat_dict[self.main.args.mode])
	
	def episodes(self):
		grabFTW().getEpisodes(self.main.args.url, self.main.args.id, self.main.args.icon, self.main.args.mode)
		
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
		elif mode == 'watchlist':
			UI().watchlist()


