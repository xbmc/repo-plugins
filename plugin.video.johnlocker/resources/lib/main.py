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
		# Fetch List of Revision3 Shows
		url = u"http://johnlocker.com/home/main?mlvd=oc&mmvd=oc&mhrvd=oc&mfvd=oc&"
		sourceCode = urlhandler.urlread(url, 604800) # TTL = 1 Week
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_title)
		self.set_content("files")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Add Extra Items
		#self.add_item(u"-Channels", thumbnail=(u"channels.jpg",1), url={"action":"Channels", "url":"http://johnlocker.com/home/channel"})
		self.add_item(u"-%s" % plugin.getuni(32941), thumbnail=(u"latest.png",1), url={"action":"Videos", "url":"http://johnlocker.com/home/main?mlvd=oc&mmvd=oc&mhrvd=oc&mfvd=oc", "section":"latestvideos"})
		self.add_item(u"-%s" % plugin.getuni(30101), thumbnail=(u"viewed.jpg",1), url={"action":"Videos", "url":"http://johnlocker.com/home/main?mlvd=oc&mmvd=oc&mhrvd=oc&mfvd=oc", "section":"mostviewed"})
		self.add_item(u"-%s" % plugin.getuni(30102), thumbnail=(u"rated.jpg",1), url={"action":"Videos", "url":"http://johnlocker.com/home/main?mlvd=oc&mmvd=oc&mhrvd=oc&mfvd=oc", "section":"highestrated"})
		self.add_item(u"-%s" % plugin.getuni(30103), thumbnail=(u"featured.png",1), url={"action":"Videos", "url":"http://johnlocker.com/home/main?mlvd=oc&mmvd=oc&mhrvd=oc&mfvd=oc", "section":"featured"})
		
		# Loop and display each Video
		import CommonFunctions, re
		searchUrlTitle = re.compile('<a href="(http://johnlocker.com/home/category/videos/\d+)" style="font-weight:bold;">\s+(.+?)\s+</a>')
		searchImg = re.compile('<img class="listedvideolistthumbnailmc" src="(http://johnlocker.com/categories/\S+.jpg)"')
		sectionCat = CommonFunctions.parseDOM(sourceCode, u"div", {u"id":u"categories"})
		for htmlSegment in CommonFunctions.parseDOM(sectionCat, u"div", {u"class":u"listedvideolistvideomc"}):
			# Fetch Url and Title
			url, title = searchUrlTitle.findall(htmlSegment)[0]
			
			# Create listitem of Data
			item = localListitem()
			item.setLabel(title)
			item.setThumbnailImage(searchImg.findall(htmlSegment)[0])
			item.setParamDict(action="Videos", url=u"%s?cvld=oc" % url)
			
			# Store Listitem data
			additem(item.getListitemTuple(False))
			
		# Return list of listitems
		return results

class Channels(listitem.VirtualFS):
	""" Disabled as most Channels do not work anymore """
	@plugin.error_handler
	def scraper(self):
		# Fetch List of Revision3 Shows
		sourceCode = urlhandler.urlread(plugin["url"], 604800) # TTL = 1 Week
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_title)
		self.set_content("files")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Loop and display each Video
		import CommonFunctions, re
		searchUrlTitle = re.compile('<div class="channelitemtitle"><a href="(http://johnlocker.com/home/channel/\d+)">(.+?)</a>')
		searchImg = re.compile('<img class="channelitemimage" src="(http://johnlocker.com/\S+\.jpg)"')
		for htmlSegment in CommonFunctions.parseDOM(sourceCode, u"div", {u"class":u"channelitem"}):
			img = searchImg.findall(htmlSegment)
			if img: img = img[0]
			else: continue
			
			# Fetch Url and Title
			url, title = searchUrlTitle.findall(htmlSegment)[0]
			
			# Create listitem of Data
			item = localListitem()
			item.setLabel(title)
			item.setThumbnailImage(img)
			item.setParamDict(action="Videos", url=url)
			
			# Store Listitem data
			additem(item.getListitemTuple(False))
			
		# Return list of listitems
		return results

class Videos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		sourceCode = urlhandler.urlread(plugin["url"], 14400) # TTL = 4 Hours
		
		# Set Content Properties
		if "section" in plugin and plugin["section"] == u"mostviewed": self.set_sort_methods(self.sort_method_program_count, self.sort_method_date, self.sort_method_video_runtime, self.sort_method_title)
		else: self.set_sort_methods(self.sort_method_date, self.sort_method_video_runtime, self.sort_method_program_count, self.sort_method_title)
		self.set_content("episodes")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		intcmd = int
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Restrict to Selected Section and Add Next Page
		import CommonFunctions, re
		if "section" in plugin: sourceCode = CommonFunctions.parseDOM(sourceCode, u"div", {u"id":plugin["section"]})[0]
		nextUrl = re.findall('<a class="pagination" href="(\S+?)">Next</a>', sourceCode)
		if nextUrl: self.add_next_page(url={"url":u"http://johnlocker.com%s&mlvd=oc&mmvd=oc&mhrvd=oc&mfvd=oc&cvld=oc" % nextUrl[0], "section":plugin.get("section","")})
		
		# Loop and display each Video
		searchUrl = re.compile('<a href="(http://johnlocker.com/home/video/\S+?)"')
		searchTitle = re.compile('<a href="http://johnlocker.com/home/video/\S+?" style="font-weight:bold;">\s*(.+?)\s*</a>')
		searchPlot = re.compile('<div class="listedvideolistdescdivoc">\s*(.+?)\s*</div>')
		searchDate = re.compile('<div class="listedvideolistfootdivoc">\s+Added date: (\d+-\d+-\d+)\s+- Duration:.+?\s+</div>')
		searchTime = re.compile('<div class="listedvideolistfootdivoc">\s+Added date: \d+-\d+-\d+\s+- Duration:(.+?)\s+</div>')
		searchImg = re.compile('<img class="listedvideolistthumbnailoc" src="(http://\S+?)"')
		searchViews = re.compile('<div class="clear"></div>\s+</div>\s+Views : (\d+)\s+</div>')
		for htmlSegment in CommonFunctions.parseDOM(sourceCode, u"div", {u"class":u"listedvideolistvideooc"}):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(searchTitle.findall(htmlSegment)[0])
			
			# Fetch Url
			url = searchUrl.findall(htmlSegment)[0]
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Posable Extras
			try: item.setThumbnailImage(searchImg.findall(htmlSegment)[0])
			except: pass
			try: item.setInfoDict("plot", searchPlot.findall(htmlSegment)[0])
			except: pass
			try: item.setInfoDict("count", intcmd(searchViews.findall(htmlSegment)[0]))
			except: pass
			try: item.setDurationInfo(searchTime.findall(htmlSegment)[0].strip())
			except: pass
			try: item.setDateInfo(searchDate.findall(htmlSegment)[0], "%d-%m-%Y")
			except: pass
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=u"%s?rvds=oc" % url)
			
			# Store Listitem data
			additem(item.getListitemTuple(True))
			
		# Return list of listitems
		return results

class Related(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		sourceCode = urlhandler.urlread(plugin["url"], 14400) # TTL = 4 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_date, self.sort_method_video_runtime, self.sort_method_program_count, self.sort_method_title)
		self.set_content("episodes")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		intcmd = int
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Loop and display each Video
		import CommonFunctions, re
		searchUrl = re.compile('<a href="(http://johnlocker.com/home/video/\S+?)" class="videolink">')
		searchTitle = re.compile('class="videolink">\s+(.+?)\s+</a>\s+</div>')
		searchDate = re.compile('<div\s+class="watchpagelistaddeddatediv">\s+Date: (\d+-\d+-\d+)\s+</div>')
		searchTime = re.compile('<div class="watchpagelistdurationdivmc">\s*(\d+:\d+:\d+)\s+</div>')
		searchImg = re.compile('<img class="videothumbscv" src="(http://\S+?)"')
		searchViews = re.compile('<div\s+class="watchpagelistviewsdiv">\s+Views: (\d+)\s+</div>')
		for htmlSegment in CommonFunctions.parseDOM(sourceCode, u"div", {u"class":u"relatedvideoslistrow"}):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(searchTitle.findall(htmlSegment)[0])
			
			# Fetch Url
			url = searchUrl.findall(htmlSegment)[0]
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Posable Extras
			try: item.setThumbnailImage(searchImg.findall(htmlSegment)[0])
			except: pass
			try: item.setInfoDict("count", intcmd(searchViews.findall(htmlSegment)[0]))
			except: pass
			try: item.setDurationInfo(searchTime.findall(htmlSegment)[0].strip())
			except: pass
			try: item.setDateInfo(searchDate.findall(htmlSegment)[0], "%d-%m-%Y")
			except: pass
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=u"%s?rvds=oc" % url, updatelisting="true")
			
			# Store Listitem data
			additem(item.getListitemTuple(True))
			
		# Return list of listitems
		return results

class PlayVideo(listitem.PlayMedia):
	@plugin.error_handler
	def resolve(self):
		# Fetch List of Revision3 Shows
		sourceCode = urlhandler.urlread(plugin["url"], 14400, stripEntity=False) # TTL = 4 Hours
		import re
		
		# Fetch the List of Available Source on the Site
		urls = re.findall("'file':\s+'(http://\S+?)'", sourceCode)
		urls.extend(re.findall('<div id="videooriginalurl">\s+<a href="(http://\S+?)"', sourceCode))
		
		# Fetch Video Url From Sources
		if urls: return self.sources(urls=urls)
