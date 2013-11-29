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
		url = "http://metalvideo.com/mobile/category.html"
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
		self.add_item(label="-Random Video", url={"action":"PlayVideo", "url":"http://www.metalvideo.com/randomizer.php"}, isPlayable=True)
		self.add_item(label="-Top 50 Videos", url={"action":"TopVideos", "url":"http://www.metalvideo.com/topvideos.html"}, isPlayable=False)
		self.add_item(label="-Latest Videos", url={"action":"NewVideos", "url":"http://www.metalvideo.com/newvideos.html"}, isPlayable=False)
		self.add_item(label="-Search", url={"action":"VideoList"}, isPlayable=False)
		
		# Loop and display each Video
		for url, title, count in re.findall('<li class=""><a href="http://metalvideo.com/mobile/(\S+?)date.html">(.+?)</a>\s+<span class="category_count">(\d+)</span></li>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			item.setLabel("%s (%s)" % (title, count))
			item.setParamDict(action="VideoList", url="http://metalvideo.com/%s" % url)
			
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
		self.set_content("musicvideos")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_selector(self):
		# Fetch SourceCode
		url = "http://metalvideo.com/topvideos.html"
		sourceCode = urlhandler.urlread(url, 2678400) # TTL = 1 Month
		
		# Fetch list of Top Video Category
		topLists = [part for part in re.findall('<option value="(\S+?)"\s*>\s*(.+?)\s*</option>', sourceCode) if not "Select one" in part[1]]
		titleList = [part[1] for part in topLists]
		
		# Display list for Selection
		ret = plugin.dialogSelect(plugin.getstr(30600), titleList)
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
			item.setLabel("%s. %s - %s" % (count, artist, track))
			item.setThumbnailImage(img)
			item.setInfoDict(artist=artist, count=intCmd(views.replace(",","")))
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind("_")+1:url.rfind(".")])
			
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
		self.set_content("musicvideos")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Add Next Page if Exists   
		nextUrl = re.findall('<a href="(\S+?)">next \xc2\xbb</a>', sourceCode)
		if nextUrl: self.add_next_page(url={"url":"http://www.metalvideo.com/%s" % nextUrl[0]})
		
		# Iterate the list of videos
		for url, img, artist, track in re.findall('<tr><td align="center" class="\w+" width="\d+"><a href="(\S+?)"><img src="(\S+?)" alt=".+?"  class="tinythumb" width="\d+" height="\d+" align="left" border="1" /></a></td><td class="\w+" width="\w+">(.+?)<td class="\w+"><a href="\S+?">(.+?)</a></td><td class="\w+">.+?</td></tr>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			
			# Create listitem of Data
			item = localListitem()
			item.setLabel("%s - %s" % (artist, track))
			item.setThumbnailImage(img)
			item.setInfoDict(artist=artist)
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind("_")+1:url.rfind(".")])
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=True))
		
		# Return list of listitems
		return results

class Related(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		url = "http://metalvideo.com/relatedclips.php?vid=%(url)s" % plugin
		sourceCode = urlhandler.urlread(url, 28800) # TTL = 8 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		self.set_content("musicvideos")
		
		# Fetch and Return VideoItems
		return self.xml_scraper(sourceCode)
	
	def xml_scraper(self, sourceCode):
		# Create Speed vars
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Import XML Parser and Parse sourceObj
		import xml.etree.ElementTree as ElementTree
		tree = ElementTree.fromstring(sourceCode.replace("&","&amp;"))
		
		# Loop thought earch Show element
		for node in tree.getiterator("video"):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(node.findtext("title").encode("utf-8"))
			item.setThumbnailImage(node.findtext("thumb").encode("utf-8"))
			
			# Add url Param
			url = node.findtext("url").encode("utf-8")
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind("_")+1:url.rfind(".")], updatelisting="true")
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=True))
		
		# Return list of listitems
		return results

class VideoList(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		if "url" in plugin:
			# Fetch Sort Method and Crerate New Url
			urlString = {"0":"%sdate.html", "1":"%sartist.html", "2":"%srating.html", "3":"%sviews.html"}[plugin.getSetting("sort")]
			url = urlString % plugin["url"]
		else: url = urlhandler.search("http://www.metalvideo.com/search.php?keywords=%s"); self.cacheToDisc= True
		sourceCode = urlhandler.urlread(url, 28800) # TTL = 8 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		self.set_content("musicvideos")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		import CommonFunctions
		
		# Add Next Page if Exists   
		nextUrl = re.findall('<a href="(\S+?)">next \xc2\xbb</a>', sourceCode)
		if nextUrl: self.add_next_page(url={"url":"http://www.metalvideo.com/%s" % nextUrl[0]})
		
		# Iterate the list of videos
		searchUrl = re.compile('<a href="(\S+?)">')
		searchImg = re.compile('<img src="(\S+?)"')
		searchSong = re.compile('<span class="song_name">(.+?)</span>')
		searchArtist = re.compile('<span class="artist_name">(.+?)</span>')
		for htmlSegment in CommonFunctions.parseDOM(sourceCode, "li", {"class":"video"}):
			# Convert String Encoding
			htmlSegment = htmlSegment.encode("utf8")
			artist = searchArtist.findall(htmlSegment)[0]
			url = searchUrl.findall(htmlSegment)[0]
			
			# Create listitem of Data
			item = localListitem()
			item.setLabel("%s - %s" % (artist, searchSong.findall(htmlSegment)[0]))
			item.setInfoDict(artist=artist)
			item.setParamDict(action="PlayVideo", url=url)
			
			# Set Thumbnail Image
			image = searchImg.findall(htmlSegment)
			if image: item.setThumbnailImage(image[0])
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind("_")+1:url.rfind(".")])
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=True))
			
		# Return list of listitems
		return results

class PlayVideo(listitem.PlayMedia):
	@plugin.error_handler
	def resolve(self):
		# Set TTL
		if plugin["url"].endswith("randomizer.php"): TTL=0
		else: TTL=604800 # TTL = 1 Week
		
		# Fetch Page Source
		sourceCode = urlhandler.urlread(plugin["url"], TTL) # TTL = 8 Hours
		from xbmcutil import videoResolver
		
		# Look for Youtube Video First
		videoId = [part for part in re.findall('src="(http://www.youtube.com/embed/\S+?)"|file:\s+\'(\S+?)\'', sourceCode)[0] if part][0]
		if "www.metalvideo.com" in videoId: return {"url":videoId}
		else: return videoResolver.youtube_com().decode(videoId)
