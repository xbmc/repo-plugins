"""
	Copyright: (c) 2013 William Forde (willforde+xbmc@gmail.com)
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
		sourceCode = urlhandler.urlread(url, 2678400) # TTL = 1 Week
		
		# Add Search Page
		self.add_search("Videos", u"/search/?search=%s")
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		self.set_content("files")
		
		# Fetch and Return VideoItems
		self.add_youtube_channel(u"engineeringtv")
		return self.regex_scraper(sourceCode) 
	
	def regex_scraper(self, sourceCode):
		# Create Speedup vars
		import re
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Fetch Video Information from Page Source
		for url, title in re.findall('<div class="mvp-global-nav-0">\s*<a href="/pages/(\S+?)">(.+?)</a>\s*</div>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(title)
			item.setThumbnailImage(u"%s.jpg" % url, 1)
			item.setParamDict(action="Videos", subaction="subcat", url=url)
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=False))
		
		# Return list of listitems
		return results

class Videos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Decide on to Show sub Categories or directly show videos
		if plugin.get("subaction",u"") == u"subcat": return self.subCategories(plugin["url"])
		else: return self.videoList(plugin["url"])
	
	def subCategories(self, catID):
		# Fetch SourceCode
		url = u"http://www.engineeringtv.com/pages/%s" % catID
		sourceCode = urlhandler.urlread(url, 2678400) # TTL = 1 Week
		
		# Fetch List of Sub Categories
		import CommonFunctions, re
		searchID = re.compile('href="/feed/magnify.rss/(\S+?)"')
		sources = CommonFunctions.parseDOM(sourceCode, u"div", {u"class":u"mvp_page_title_expressive clearfix"})
		if len(sources) == 1: return self.videoList(u"/watch/playlist/%s" % searchID.findall(sources[0])[0])
		else:
			# Set Content Properties
			self.set_sort_methods(self.sort_method_unsorted)
			self.set_content("files")
			
			# Create Speed vars
			results = []
			additem = results.append
			localListitem = listitem.ListItem
			
			# Loop and display each source
			for htmlSegment in sources:
				# Create listitem of Data
				item = localListitem()
				item.setLabel(htmlSegment[htmlSegment.rfind(u"</div>")+6:].strip().title())
				item.setParamDict(action="Videos", url=u"/watch/playlist/%s" % searchID.findall(htmlSegment)[0])
				
				# Store Listitem data
				additem(item.getListitemTuple(isPlayable=False))
			
			# Return list of listitems
			return results
	
	def videoList(self, playlistID):
		# Fetch SourceCode
		if playlistID.startswith(u"?search="): url = u"http://www.engineeringtv.com/search/%s" % playlistID
		else: url = u"http://www.engineeringtv.com%s" % playlistID
		sourceCode = urlhandler.urlread(url, 28800) # TTL = 8 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		self.set_content("episodes")
		
		# Create Speed vars
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Loop and display each Video
		import CommonFunctions, re
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
			item.setAudioInfo()
			item.setQualityIcon(False)
			item.setLabel(searchTitle.findall(htmlSegment)[0])
			item.setThumbnailImage(searchImg.findall(htmlSegment)[0])
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url)
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=True))
			
		# Return list of listitems
		return results

class Related(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode of Site
		url = u"http://www.engineeringtv.com%(url)s" % plugin
		sourceCode = urlhandler.urlread(url, 28800) # TTL = 8 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		self.set_content("episodes")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Loop and display each Video
		import CommonFunctions, re
		searchTitle = re.compile('title="(.+?)"')
		searchUrl = re.compile('<a href="(\S+?)"')
		searchImg = re.compile("background-image: url\('(http\S+?)'\)")
		for htmlSegment in CommonFunctions.parseDOM(sourceCode, u"div", {u"class":u"magnify-widget-playlist-item"}):    
			# Fetch url
			url = searchUrl.findall(htmlSegment)[0]
			url = url[url.rfind("/video/"):]
			
			# Create listitem of Data
			item = localListitem()
			item.setAudioInfo()
			item.setQualityIcon(False)
			item.setLabel(searchTitle.findall(htmlSegment)[0])
			item.setThumbnailImage(searchImg.findall(htmlSegment)[0])
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url, updatelisting="true")
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=True))
			
		# Return list of listitems
		return results

class PlayVideo(listitem.PlayMedia):
	@plugin.error_handler
	def resolve(self):
		# Call Needed Imports
		import re
		
		try:
			# Fetch SourceCode of Site
			url = u"http://www.engineeringtv.com%(url)s/player" % plugin
			sourceCode = urlhandler.urlread(url, 1800) # TTL = 30 Mins
			
			# Fetch Query String with video id
			queryString = re.findall("queryString\s*=\s*'(\S+?)'", sourceCode)[0]
			url = u"http://www.engineeringtv.com/embed/player/container/300/300/?%s" % queryString
			sourceCode = urlhandler.urlread(url, 1800) # TTL = 30 Mins
			
			# Fetch Video Url
			videoUrl = re.findall('"pipeline_xid"\s*:\s*"(http://videos\.\S+?)"', sourceCode)[0]
			return {"type":u"video/mp4", "url":videoUrl}
		
		except:
			# Fetch SourceCode of Site
			url = u"http://www.engineeringtv.com%(url)s" % plugin
			sourceCode = urlhandler.urlread(url, 86400) # TTL = 24 Hours
			
			# Fetch Video Url
			try: url = re.findall('src=\\\\"(http://videos\.cache\.magnify\.net/\S+?)\\\\" autoplay controls poster', sourceCode)[0]
			except: return None
			else: return {"type":u"video/mp4", "url":url}
