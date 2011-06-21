import urllib, urllib2, re, sys, os
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
		
###################################
##########  Class Day 9  ##########
###################################
				
class Day9:	

	USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"
	__settings__ = xbmcaddon.Addon(id='plugin.video.day9')
	__language__ = __settings__.getLocalizedString
	
	def action(self, params):
		get = params.get
		if (get("action") == "showTitles"):
			self.showTitles(params)
		if (get("action") == "showGames"):
			self.showGames(params)
			
	# ------------------------------------- Menu functions ------------------------------------- #
	
	# display the root menu
	def root(self):
		self.addCategory(self.__language__(31000), 'http://blip.tv/pr/show_get_full_episode_list?users_id=570336&lite=0&esi=1', 'showTitles', 1)
		
		
	# ------------------------------------- Add functions ------------------------------------- #

	
	def addCategory(self, title, url, action, page = 1):
		url=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&title="+title+"&action="+urllib.quote_plus(action)+"&page="+str(page)
		listitem=xbmcgui.ListItem(title, iconImage="DefaultFolder.png", thumbnailImage="DefaultFolder.png")
		listitem.setInfo( type="Video", infoLabels={ "Title": title } )
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=True)
		
	def addVideo(self,title,url):
		liz=xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage="DefaultVideo.png")
		liz.setInfo( type="Video", infoLabels={ "Title": title } )
		xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
		
	# ------------------------------------- Show functions ------------------------------------- #
	
	
	def showTitles(self, params = {}):
		get = params.get
		link = self.getRequest(get("url"))
		title = re.compile('<span class="Title">\n\t\t\n\t\t\t(.*?)\n\t\t\n\t</span>').findall(link)
		url = re.compile('<a class="ArchiveCard" href="(.*?)">').findall(link)
		
		for i in range(len(title)):
			self.addCategory(title[i], 'http://blip.tv'+url[i], 'showGames', '')
			
		page = int(get("page"))+1
		url = 'http://blip.tv/pr/show_get_full_episode_list?users_id=570336&lite=0&esi=1&page='+str(page)
		self.addCategory('more episodes...', url, 'showTitles', page)
			
	def showGames(self, params = {}):
		get = params.get
		url_map = urllib.unquote_plus(get('url')).split('-')
			
		link = self.getRequest('http://blip.tv/rss/view/'+url_map[-1])
		result = re.findall('blip:role="(.*?)".+?isDefault=".*?" type=".*?" url="(.*?)"', link)
		settingsHD = int(self.__settings__.getSetting( "hd_videos" ))
		
		if settingsHD > 0:
			for i in range(len(result)):
				if result[i][0] == 'Blip HD 720':
					url = result[i][1]
				else:
					url = result[i][1]
		else:
			for i in range(len(result)):
				if result[i][0] == 'Blip HD 720':
					pass
				else:
					url = result[i][1]
		self.addVideo(get("title"), url)
		
		
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
