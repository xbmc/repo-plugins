"""
	Copyright: (c) 2013 William Forde (willforde+kodi@gmail.com)
	License: GPLv3, see LICENSE for more details
	
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.
	
	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.
	
	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Call Necessary Imports
from xbmcutil import listitem, urlhandler, plugin

class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode of Site
		url = u"http://www.engineeringtv.com/pages/about.us"
		sourceCode = urlhandler.urlread(url, 604800) # TTL = 1 Week
		
		# Add Search Page
		self.add_search("Videos", u"/search/?search=%s")
		self.add_recent(action="Recent", url="http://www.engineeringtv.com/feed/recent.rss")
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch and Return VideoItems
		self.add_youtube_videos(u"UUaClUPEtVUloRWO9N7g7WBA", hasPlaylist=False)
		return self.regex_scraper(sourceCode) 
	
	def regex_scraper(self, sourceCode):
		# Create Speedup vars
		import re
		localListitem = listitem.ListItem
		
		# Fetch Video Information from Page Source
		for url, title in re.findall('<div class="mvp-global-nav-0">\s*<a href="/pages/(\S+?)">(.+?)</a>\s*</div>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(title)
			item.setThumb(u"%s.jpg" % url, 1)
			item.setParamDict(action="Videos", subaction="subcat", url=url)
			
			# Store Listitem data
			yield item.getListitemTuple(False)

class Recent(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		sourceObj = urlhandler.urlopen(plugin["url"], 14400) # TTL = 4 Hours
		
		# Fetch and Return VideoItems
		return self.xml_scraper(sourceObj)
	
	def xml_scraper(self, sourceObj):
		# Create Speed vars
		localListitem = listitem.ListItem
		
		# Import XML Parser and Parse sourceObj
		import xml.etree.ElementTree as ElementTree
		tree = ElementTree.parse(sourceObj)
		sourceObj.close()
		
		# Loop thought earch Show element
		for node in tree.getiterator("item"):
			# Create listitem of Data
			item = localListitem()
			item.setAudioFlags()
			item.setVideoFlags(False)
			item.setLabel(node.findtext("title"))
			item.setThumb(node.find("enclosure").get("url"))
			item.setInfoDict(plot=node.findtext("description"), credits=node.findtext("author"))
			
			# Fetch url
			url = node.findtext("link")
			url = url[url.rfind("/video/"):]
			item.setParamDict(url=url, action="PlayVideo")
			
			# Add Date Info
			date = node.findtext("pubDate")
			item.setDate(date[:date.rfind("-")-1], "%a, %d %b %Y %H:%M:%S")
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url)
			
			# Store Listitem data
			yield item.getListitemTuple(True)

class Videos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Decide on to Show sub Categories or directly show videos
		if plugin.get("subaction",u"") == u"subcat": return self.subCategories(plugin["url"])
		else: return self.videoList(plugin["url"])
	
	def subCategories(self, catID):
		# Fetch SourceCode
		url = u"http://www.engineeringtv.com/pages/%s" % catID
		sourceCode = urlhandler.urlread(url, 604800) # TTL = 1 Week
		
		# Fetch List of Sub Categories
		import CommonFunctions, re
		searchID = re.compile('href="/feed/magnify.rss/(\S+?)"')
		sources = CommonFunctions.parseDOM(sourceCode, u"div", {u"class":u"mvp_page_title_expressive clearfix"})
		if len(sources) == 1: return self.videoList(u"/watch/playlist/%s" % searchID.findall(sources[0])[0])
		else: return self.genreList(sources, searchID)
	
	def genreList(self, sources, searchID):
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Loop and display each source
		localListitem = listitem.ListItem
		for htmlSegment in sources:
			# Create listitem of Data
			item = localListitem()
			item.setLabel(htmlSegment[htmlSegment.rfind(u"</div>")+6:].strip().title())
			item.setParamDict(action="Videos", url=u"/watch/playlist/%s" % searchID.findall(htmlSegment)[0])
			
			# Store Listitem data
			yield item.getListitemTuple(False)
	
	def videoList(self, playlistID):
		# Fetch SourceCode
		if playlistID.startswith(u"?search="): url = u"http://www.engineeringtv.com/search/%s" % playlistID
		else: url = u"http://www.engineeringtv.com%s" % playlistID
		
		# Fetch redirected Url from database and load webpage
		from xbmcutil import storageDB
		urlDB = storageDB.Metadata()
		sourceObj = urlhandler.urlopen(urlDB.get(url, url), 14400, stripEntity=True) # TTL = 4 Hours
		
		# If Redirect is not found in Database then add it
		if url in urlDB: urlDB.close()
		else:
			# Save DB
			urlDB[url] = sourceObj.geturl()
			urlDB.sync()
			urlDB.close()
		
		# Read in data from cache and decode into unicode
		sourceCode = sourceObj.read().decode("utf-8")
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Loop and display each Video
		import CommonFunctions, re
		localListitem = listitem.ListItem
		searchTitle = re.compile('title="(.+?)"')
		searchUrl = re.compile('<a href="(\S+?)"')
		searchImg = re.compile("background-image: url\('(\S+?)'\)")
		nextUrl = re.findall('<a class="mvp-pagenum-next mvp-pagenum-pagelink" href="(\S+?)">', sourceCode)
		if nextUrl: self.add_next_page(url={"url":nextUrl[0]})
		for htmlSegment in CommonFunctions.parseDOM(sourceCode, u"div", {u"class":u"mvp_grid_panel_\d"}):    
			# Fetch url
			url = searchUrl.findall(htmlSegment)[0]
			url = url[url.rfind("/video/"):]
			
			# Create listitem of Data
			item = localListitem()
			item.setAudioFlags()
			item.setVideoFlags(False)
			item.setLabel(searchTitle.findall(htmlSegment)[0])
			item.setThumb(searchImg.findall(htmlSegment)[0])
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url)
			
			# Store Listitem data
			yield item.getListitemTuple(True)

class Related(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode of Site
		url = u"http://www.engineeringtv.com%(url)s" % plugin
		sourceCode = urlhandler.urlread(url, 14400) # TTL = 4 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Loop and display each Video
		import CommonFunctions, re
		localListitem = listitem.ListItem
		searchTitle = re.compile('title="(.+?)"')
		searchUrl = re.compile('<a href="(\S+?)"')
		searchImg = re.compile("background-image: url\('(http\S+?)'\)")
		for htmlSegment in CommonFunctions.parseDOM(sourceCode, u"div", {u"class":u"magnify-widget-playlist-item"}):    
			# Fetch url
			url = searchUrl.findall(htmlSegment)[0]
			url = url[url.rfind("/video/"):]
			
			# Create listitem of Data
			item = localListitem()
			item.setAudioFlags()
			item.setVideoFlags(False)
			item.setLabel(searchTitle.findall(htmlSegment)[0])
			item.setThumb(searchImg.findall(htmlSegment)[0])
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url, updatelisting="true")
			
			# Store Listitem data
			yield item.getListitemTuple(True)

class PlayVideo(listitem.PlayMedia):
	@plugin.error_handler
	def resolve(self):
		# Call Needed Imports
		import re
		
		try:
			# Fetch SourceCode of Site
			url = u"http://www.engineeringtv.com%(url)s/player" % plugin
			sourceCode = urlhandler.urlread(url, 1800, stripEntity=False) # TTL = 30 Mins
			
			# Fetch Query String with video id
			queryString = re.findall("queryString\s*=\s*'(\S+?)'", sourceCode)[0]
			url = u"http://www.engineeringtv.com/embed/player/container/300/300/?%s" % queryString
			sourceCode = urlhandler.urlread(url, 1800, stripEntity=False) # TTL = 30 Mins
			
			# Fetch Video Url
			videoUrl = re.findall('"pipeline_xid"\s*:\s*"(http://videos\.\S+?)"', sourceCode)
			print videoUrl
			return {"type":u"video/mp4", "url":videoUrl[0]}
		
		except:
			# Fetch SourceCode of Site
			url = u"http://www.engineeringtv.com%(url)s" % plugin
			sourceCode = urlhandler.urlread(url, 1800, stripEntity=False) # TTL = 30 Mins
			
			# Create url to video Content Data
			contentID = re.findall('<div id="mvp_video_(\S+?)"', sourceCode)[0]
			url = u"http://www.engineeringtv.com/item/player_embed.js/%s" % contentID
			sourceCode = urlhandler.urlread(url, 1800, stripEntity=False) # TTL = 30 Mins
			
			# Fetch video url
			videoUrls = re.findall("\d:\s+{\s+bitrate:\s+'(\d+)',\s+src:\s+'(http\S+?)',\s+ftype:\s+'(\S+?)'\s+}", sourceCode)
			if videoUrls:
				videoUrls = sorted(videoUrls, key=lambda videos: videos[0], reverse=True)
				return {"type":u"video/mp4", "url":videoUrls[0]}
