import re
import os
import sys
import urllib
import urllib2
import httplib
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from BeautifulSoup import BeautifulSoup, Comment

class updateArgs:

	def __init__(self, *args, **kwargs):
		for key, value in kwargs.iteritems():
			if value == 'None':
				kwargs[key] = None
			else:
				kwargs[key] = urllib.unquote_plus(kwargs[key])
		self.__dict__.update(kwargs)

class Common:
	
	def capWords(self, words):
		return ' '.join([x.capitalize() for x in words.split()])
	
	def downloadHTML(self, url):
		request = urllib2.Request(url)
		request.add_header("Host", "pitchfork.com")
		request.add_header("User-Agent", "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10")
		opener = urllib2.build_opener()
		return opener.open(request).read()
		
	def getPage(self, html):
		soup = BeautifulSoup(html)
		pages = soup.findAll('a', attrs={'class':'page-link'})
		curPage = soup.find('a', attrs={'class':'page-link current'})
		if not curPage:
			curPage = 1
		else:
			curPage = int(curPage.string)
		if len(pages) > 1:
			endPage = pages[-1]
			endPage = int(endPage.string)
		elif len(pages) == 1:
			endPage = pages[0]
			endPage = int(endPage.string)
		else:
			endPage = curPage
		del soup
		return curPage, endPage
		
	def returnVideos(self, html, isList = False, category = None):
		soup = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
		comments = soup.findAll(text=lambda text:isinstance(text, Comment))
		[comment.extract() for comment in comments]
		reg_id = re.compile('[0-9a-f]{32}')
		videos = []
		if isList is False:
			videoList = soup.findAll('div', attrs={'class':'td-contents'})
			for video in videoList:
				file = {}
				href = video.a['href']
				links = video.findAll('a')
				if len(links) > 1:
					file['name'] = unicode(links[-1].string).encode('utf-8')
				else:
					linkList = video.findAll(text=lambda(x): len(x) > 3)
					if len(linkList) > 1:
						linkList[1] = " ".join(linkList[1].split())
						linkList[1] = linkList[1]
					links = " | ".join(linkList)
					file['name'] = unicode(links).encode('utf-8')
				file['img'] = video.a.img['src']
				if href:
					ids = re.findall(reg_id, href)
					if len(ids) > 1:
						idStr = ''
						for id in ids:
							idStr += str(id)
						file['url'] = idStr
					else:
						file['url'] = str(ids[0])
				videos.append(file)
		else:
			videoSoup = soup.find('div', attrs={'id':category})
			videoList = videoSoup.findAll('a')
			for video in videoList:
				file = {}
				text = video.findAll(text=lambda(x): len(x) > 3)
				file['name'] = unicode("".join(text)).encode('utf-8')
				ids = re.findall(reg_id, video['href'])
				if len(ids) > 1:
					idStr = ''
					for id in ids:
						idStr += str(id)
					file['url'] = idStr
				else:
					file['url'] = str(ids[0])
				file['img'] = 'None'
				videos.append(file)
		del soup
		del comments
		return videos

class VideoObject:
	
	def __init__(self, IDs):
		print len(IDs)
		if len(IDs) > 32:
			self.mediaID = IDs[0:32]
			self.channelID = IDs[32:64]
			print "PITCHFORK: --> media ID: "+str(self.mediaID)
			print "PITCHFORK: --> channel ID: "+str(self.channelID)
		else:
			self.mediaID = IDs
			self.channelID = None
			print "PITCHFORK: --> mediaID: "+str(self.mediaID)
			print "PITCHFORK: --> channel ID: NULL"
		self.streams = self.requestStreams(self.mediaID, self.channelID)
	
	def requestStreams(self, mediaID, channelID=None):
		in0 = '<tns:in0>' + mediaID + '</tns:in0>'
		if not channelID:
			in1 = '<tns:in1 xsi:nil="true" />'
		else:
			in1 = '<tns:in1>' + channelID + '</tns:in1>'
		SoapMessage = """<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><SOAP-ENV:Body><tns:getPlaylistByMediaId xmlns:tns="http://service.data.media.pluggd.com">"""+in0+in1+"""</tns:getPlaylistByMediaId></SOAP-ENV:Body></SOAP-ENV:Envelope>"""

		webservice = httplib.HTTP("ps2.delvenetworks.com")
		webservice.putrequest("POST", "/PlaylistService")
		webservice.putheader("Host", "ps2.delvenetworks.com")
		webservice.putheader("User-Agent", "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10")
		webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
		webservice.putheader("Content-length", "%d" % len(SoapMessage))
		webservice.putheader("Referer", "http://static.delvenetworks.com/deployments/player/player-3.27.1.0.swf?playerForm=Chromeless")
		webservice.putheader("X-Page-URL", "http://pitchfork.com/tv/")
		webservice.putheader("SOAPAction", "\"\"")
		webservice.endheaders()
		webservice.send(SoapMessage)
	
		statuscode, statusmessage, header = webservice.getreply()
		res = webservice.getfile().read()
	
		soup = BeautifulSoup(res)
		streams = soup.findAll('stream')
		streamList = []
		for stream in streams:
			if stream.previewstream.string == 'false':
				video = {}
				video['videoBitrate'] = int(float(stream.videobitrate.string))
				video['audioBitrate'] = int(float(stream.audiobitrate.string))
				video['url'] = str(stream.url.string)
				streamList.append(video)
		streamList = sorted(streamList, key=lambda k: k['videoBitrate'])
		print streamList
		return streamList
		
	def returnURL(self):
		if len(self.streams) > 0:
			return self.streams[-1]['url']

class UI:
	def __init__(self):
		self.main = Main(checkMode = False)
		self.addon = xbmcaddon.Addon(id='plugin.video.pitchfork')
		self.addonDir = xbmc.translatePath(self.addon.getAddonInfo('path'))
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
			
	def addItem(self, info, isFolder=True, total_items = 0):
		info.setdefault('name', 'None')
		info.setdefault('url', 'None')
		info.setdefault('Thumb', 'None')
		info.setdefault('mode','None')
		
		u = sys.argv[0]+\
			'?name='+urllib.quote_plus(info['Title'])+\
			'&url='+urllib.quote_plus(info['url'])+\
			'&mode='+urllib.quote_plus(info['mode'])
	
		li=xbmcgui.ListItem(label = info['Title'], iconImage = info['Thumb'], thumbnailImage = info['Thumb'])

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
		self.addItem({'Title':'Featured Videos', 'url':'http://pitchfork.com/tv/ajax/featured_videos_grid/1/', 'mode':'featured'})
		self.addItem({'Title':'Most Recent', 'url':'http://pitchfork.com/tv/', 'mode':'mostRecent'})
		self.addItem({'Title':'Most Viewed', 'url':'http://pitchfork.com/tv/', 'mode':'mostViewed'})
		self.addItem({'Title':'Music Videos', 'url':'http://pitchfork.com/tv/ajax/videos_grid/1/', 'mode':'musicVideos'})
		self.addItem({'Title':'Shows', 'url':'http://pitchfork.com/tv/', 'mode':'listShows'})
		self.endofdirectory()
		xbmc.executebuiltin("Container.SetViewMode(5)")	
			
	def featuredVideos(self):
		htmlSource = Common().downloadHTML(self.main.args.url)
		curPage, endPage = Common().getPage(htmlSource)
		currentVideos = Common().returnVideos(htmlSource)
		for video in currentVideos:
			self.addItem({'Title':video['name'], 'url':video['url'], 'Thumb': video['img'], 'mode':'video'}, True, len(currentVideos))
		if(curPage is not endPage):
			nextPage = curPage + 1
			self.addItem({'Title':'Next Page', 'url':"http://pitchfork.com/tv/ajax/featured_videos_grid/"+str(nextPage)+"/", 'Thumb':self.addonDir+'/thumbnails/next.png', 'mode':'featured'})
		self.endofdirectory()
		xbmc.executebuiltin("Container.SetViewMode(500)")
		
	def mostRecent(self):
		htmlSource = Common().downloadHTML(self.main.args.url)
		currentVideos = Common().returnVideos(htmlSource, True, 'mostrecent_tab')
		for video in currentVideos:
			self.addItem({'Title':video['name'], 'url':video['url'], 'Thumb': video['img'], 'mode':'video'}, True, len(currentVideos))
		self.endofdirectory()
		xbmc.executebuiltin("Container.SetViewMode(5)")
		
	def mostViewed(self):
		htmlSource = Common().downloadHTML(self.main.args.url)
		currentVideos = Common().returnVideos(htmlSource, True, 'mostread_tab')
		for video in currentVideos:
			self.addItem({'Title':video['name'], 'url':video['url'], 'Thumb': video['img'], 'mode':'video'}, True, len(currentVideos))
		self.endofdirectory()
		xbmc.executebuiltin("Container.SetViewMode(5)")
		
	def musicVideos(self):
		htmlSource = Common().downloadHTML(self.main.args.url)
		curPage, endPage = Common().getPage(htmlSource)
		currentVideos = Common().returnVideos(htmlSource)
		for video in currentVideos:
			self.addItem({'Title':video['name'], 'url':video['url'], 'Thumb': video['img'], 'mode':'video'}, True, len(currentVideos))
		if(curPage is not endPage):
			nextPage = curPage + 1
			self.addItem({'Title':'Next Page', 'url':"http://pitchfork.com/tv/ajax/videos_grid/"+str(nextPage)+"/", 'Thumb':self.addonDir+'/thumbnails/next.png', 'mode':'musicVideos'})
		self.endofdirectory()
		xbmc.executebuiltin("Container.SetViewMode(500)")
		
	def listShows(self):
		htmlSource = Common().downloadHTML(self.main.args.url)
		soup = BeautifulSoup(htmlSource, convertEntities=BeautifulSoup.HTML_ENTITIES)
		showList = soup.findAll('option', attrs={'value':True})
		self.addItem({'Title':'All Shows', 'url':'http://pitchfork.com/tv/ajax/shows_grid/1/', 'mode':'shows'})
		for show in showList[1:]:
			self.addItem({'Title':show.contents[0], 'url':'http://pitchfork.com/tv/ajax/shows_grid/1/'+str(show['value'])+'/', 'mode':'specificShow'}, True, len(showList))
		self.endofdirectory()
		xbmc.executebuiltin("Container.SetViewMode(5)")
		
	def shows(self):
		htmlSource = Common().downloadHTML(self.main.args.url)
		curPage, endPage = Common().getPage(htmlSource)
		currentVideos = Common().returnVideos(htmlSource)
		for video in currentVideos:
			self.addItem({'Title':video['name'], 'url':video['url'], 'Thumb': video['img'], 'mode':'video'}, True, len(currentVideos))
		if(curPage is not endPage):
			nextPage = curPage + 1
			self.addItem({'Title':'Next Page', 'url':"http://pitchfork.com/tv/ajax/shows_grid/"+str(nextPage)+"/", 'Thumb':self.addonDir+'/thumbnails/next.png', 'mode':'shows'})
		self.endofdirectory()
		xbmc.executebuiltin("Container.SetViewMode(500)")

	def specificShow(self):
		showIDArray = self.main.args.url.split('/')
		showID = showIDArray[-2]
		htmlSource = Common().downloadHTML(self.main.args.url)
		curPage, endPage = Common().getPage(htmlSource)
		currentVideos = Common().returnVideos(htmlSource)
		for video in currentVideos:
			self.addItem({'Title':video['name'], 'url':video['url'], 'Thumb': video['img'], 'mode':'video'}, True, len(currentVideos))
		if(curPage < endPage):
			nextPage = curPage + 1
			self.addItem({'Title':'Next Page', 'url':"http://pitchfork.com/tv/ajax/shows_grid/"+str(nextPage)+"/"+str(showID)+"/", 'Thumb':self.addonDir+'/thumbnails/next.png', 'mode':'specificShow'})
		self.endofdirectory()
		xbmc.executebuiltin("Container.SetViewMode(500)")
		
	def startVideo(self):
		playlist = xbmc.PlayList(1)
		playlist.clear()
		
		if len(self.main.args.url) > 64:
			i = 0
			vidNum = len(self.main.args.url)/64
			videoUrl = 'stack://'
			while (i < vidNum):
				vidStart = i*64
				vidEnd = vidStart+64
				video = VideoObject(self.main.args.url[vidStart:vidEnd])
				videoUrl += video.returnURL() + " , "
				i = i + 1
			videoUrl = videoUrl[0:-3]
		else:
			video = VideoObject(self.main.args.url)
			videoUrl = video.returnURL()
		item = xbmcgui.ListItem(label=self.main.args.name, iconImage=self.addonDir+'/icon.png', thumbnailImage=self.addonDir+'/icon.png')
		xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(videoUrl, item)
		
class Main:

	def __init__(self, checkMode = True):
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
		elif mode == 'featured':
			UI().featuredVideos()
		elif mode == 'mostRecent':
			UI().mostRecent()
		elif mode == 'mostViewed':
			UI().mostViewed()
		elif mode == 'musicVideos':
			UI().musicVideos()
		elif mode == 'listShows':
			UI().listShows()
		elif mode == 'shows':
			UI().shows()
		elif mode == 'specificShow':
			UI().specificShow()
		elif mode == 'video':
			UI().startVideo()

