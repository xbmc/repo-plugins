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
import re

class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		url = u"http://metalvideo.com/mobile/category.html"
		sourceCode = urlhandler.urlread(url, 604800, headers={"Cookie":"COOKIE_DEVICE=mobile"}, userAgent=2) # TTL = 1 Week
		
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
		self.add_item(label=u"-Random Video", url={"action":"PlayVideo", "url":u"http://www.metalvideo.com/randomizer.php"}, isPlayable=True)
		self.add_item(label=u"-Top 50 Videos", url={"action":"TopVideos", "url":u"http://www.metalvideo.com/topvideos.html"}, isPlayable=False)
		self.add_item(label=u"-Latest Videos", url={"action":"NewVideos", "url":u"http://www.metalvideo.com/newvideos.html"}, isPlayable=False)
		self.add_search("VideoList", "http://www.metalvideo.com/search.php?keywords=%s")
		
		# Loop and display each Video
		for url, title, count in re.findall('<li class=""><a href="http://metalvideo.com/mobile/(\S+?)date.html">(.+?)</a>\s+<span class="category_count">(\d+)</span></li>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(u"%s (%s)" % (title, count))
			item.setParamDict(action="VideoList", url=u"http://metalvideo.com/%s" % url)
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=False))
			
		# Return list of listitems
		return results

class TopVideos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		sourceCode = urlhandler.urlread(self.regex_selector(), 28800) # TTL = 8 Hours
		self.cacheToDisc= True
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_program_count)
		self.set_content("episodes")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_selector(self):
		# Fetch SourceCode
		url = u"http://metalvideo.com/topvideos.html"
		sourceCode = urlhandler.urlread(url, 2678400) # TTL = 1 Month
		
		# Fetch list of Top Video Category
		topLists = [part for part in re.findall('<option value="(\S+?)"\s*>\s*(.+?)\s*</option>', sourceCode) if not u"Select one" in part[1]]
		titleList = [part[1] for part in topLists]
		
		# Display list for Selection
		ret = plugin.dialogSelect(plugin.getuni(30600), titleList)
		if ret >= 0: return topLists[ret][0]
		else: raise plugin.ScraperError(0, "User Has Quit the Top Display")
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		results = []
		intCmd = int
		additem = results.append
		localListitem = listitem.ListItem
		
		# Iterate the list of videos
		for count, url, img, artist, track, views in re.findall('<tr>\s+<td align="center" class="row\d">(\d+).</td>\s+<td align="center" class="row\d" width="\d+"><a href="(\S+?)"><img src="(\S+?)" alt=".+?" class="tinythumb" width="\d+" height="\d+" align="left" border="1" /></a></td>\s+<td class="row\d">(.+?)</td>\s+<td class="row\d"><a href="\S+?">(.+?)</a></td>\s+<td class="row\d">([\d,]+)</td>\s+</tr>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(u"%s. %s - %s" % (count, artist, track))
			item.setThumbnailImage(img)
			item.setInfoDict(artist=[artist], count=intCmd(views.replace(u",",u"")))
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")])
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=True))
		
		# Return list of listitems
		return results

class NewVideos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		sourceCode = urlhandler.urlread(plugin["url"], 28800) # TTL = 8 Hours
		
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
		
		# Add Next Page if Exists   
		nextUrl = re.findall('<a href="(\S+?)">next \xc2\xbb</a>', sourceCode)
		if nextUrl: self.add_next_page(url={"url":u"http://www.metalvideo.com/%s" % nextUrl[0]})
		
		# Iterate the list of videos
		for url, img, artist, track in re.findall('<tr><td align="center" class="\w+" width="\d+"><a href="(\S+?)"><img src="(\S+?)" alt=".+?"  class="tinythumb" width="\d+" height="\d+" align="left" border="1" /></a></td><td class="\w+" width="\w+">(.+?)<td class="\w+"><a href="\S+?">(.+?)</a></td><td class="\w+">.+?</td></tr>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			
			# Create listitem of Data
			item = localListitem()
			item.setLabel(u"%s - %s" % (artist, track))
			item.setThumbnailImage(img)
			item.setInfoDict(artist=[artist])
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")])
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=True))
		
		# Return list of listitems
		return results

class Related(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		url = u"http://metalvideo.com/relatedclips.php?vid=%(url)s" % plugin
		sourceObj = urlhandler.urlopen(url, 28800) # TTL = 8 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		self.set_content("episodes")
		
		# Fetch and Return VideoItems
		return self.xml_scraper(sourceObj)
	
	def xml_scraper(self, sourceObj):
		# Create Speed vars
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Import XML Parser and Parse sourceObj
		import xml.etree.ElementTree as ElementTree
		tree = ElementTree.fromstring(sourceObj.read().replace("&","&amp;"))
		sourceObj.close()
		
		# Loop through each Show element
		for node in tree.getiterator(u"video"):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(node.findtext(u"title"))
			item.setThumbnailImage(node.findtext(u"thumb"))
			
			# Add url Param
			url = node.findtext(u"url")
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")], updatelisting="true")
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=True))
		
		# Return list of listitems
		return results

class VideoList(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Sort Method and Crerate New Url
		if u"search.php" in plugin["url"]: url = plugin["url"]
		else:
			urlString = {u"0":u"%sdate.html", u"1":u"%sartist.html", u"2":u"%srating.html", u"3":u"%sviews.html"}[plugin.getSetting("sort")]
			url = urlString % plugin["url"]
		
		# Fetch SourceCode
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
		import CommonFunctions
		
		# Add Next Page if Exists   
		nextUrl = re.findall('<a href="(\S+?)">next \xbb</a>', sourceCode)
		if nextUrl: self.add_next_page(url={"url":u"http://www.metalvideo.com/%s" % nextUrl[0]})
		
		# Iterate the list of videos
		searchUrl = re.compile('<a href="(\S+?)">')
		searchImg = re.compile('<img src="(\S+?)"')
		searchSong = re.compile('<span class="song_name">(.+?)</span>')
		searchArtist = re.compile('<span class="artist_name">(.+?)</span>')
		for htmlSegment in CommonFunctions.parseDOM(sourceCode, u"li", {u"class":u"video"}):
			# Fetch artist and url
			artist = searchArtist.findall(htmlSegment)[0]
			url = searchUrl.findall(htmlSegment)[0]
			
			# Create listitem of Data
			item = localListitem()
			item.setLabel(u"%s - %s" % (artist, searchSong.findall(htmlSegment)[0]))
			item.setInfoDict(artist=[artist])
			item.setParamDict(action="PlayVideo", url=url)
			
			# Set Thumbnail Image
			image = searchImg.findall(htmlSegment)
			if image: item.setThumbnailImage(image[0])
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")])
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=True))
			
		# Return list of listitems
		return results

class PlayVideo(listitem.PlayMedia):
	@plugin.error_handler
	def resolve(self):
		# Set TTL
		if plugin["url"].endswith(u"randomizer.php"): TTL=0
		else: TTL=604800 # TTL = 1 Week
		
		# Fetch Page Source
		sourceCode = urlhandler.urlread(plugin["url"], TTL)
		from xbmcutil import videoResolver
		
		# Look for Youtube Video First
		videoId = [part for part in re.findall('src="(http://www.youtube.com/embed/\S+?)"|file:\s+\'(\S+?)\'', sourceCode)[0] if part][0]
		if u"metalvideo.com" in videoId: return {"url":videoId}
		elif u"youtube.com" in videoId: return videoResolver.youtube_com().decode(videoId)
