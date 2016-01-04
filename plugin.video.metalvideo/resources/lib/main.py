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
import re

class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch html source
		url = u"http://metalvideo.com/mobile/category.html"
		sourceCode = urlhandler.urlread(url, 604800, headers={"Cookie":"COOKIE_DEVICE=mobile"}, userAgent=2) # TTL = 1 Week
		
		# Add Extra Items
		_plugin = plugin
		_add_item = self.add_item
		self.icon = icon = _plugin.getIcon()
		_thumb = (icon,0)
		_add_item(label=_plugin.getuni(30104), thumbnail=_thumb, url={"action":"PlayVideo", "url":u"http://metalvideo.com/index.html"}, isPlayable=True)
		_add_item(label=_plugin.getuni(30105), thumbnail=_thumb, url={"action":"Watching", "url":u"http://metalvideo.com/index.html"}, isPlayable=False)
		_add_item(label=_plugin.getuni(30103), thumbnail=_thumb, url={"action":"PlayVideo", "url":u"http://metalvideo.com/randomizer.php"}, isPlayable=True)
		_add_item(label=_plugin.getuni(30102), thumbnail=_thumb, url={"action":"TopVideos", "url":u"http://metalvideo.com/topvideos.html"}, isPlayable=False)
		_add_item(label=_plugin.getuni(32941), thumbnail=("recent.png",2), url={"action":"NewVideos", "url":u"http://metalvideo.com/newvideos.html"}, isPlayable=False)
		self.add_search("VideoList", "http://metalvideo.com/search.php?keywords=%s")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Loop and display each Video
		icon = self.icon
		localListitem = listitem.ListItem
		for url, title, count in re.findall('<li class=""><a href="http://metalvideo.com/mobile/(\S+?)date.html">(.+?)</a>\s+<span class="category_count">(\d+)</span></li>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			item.setThumb(icon)
			item.setLabel(u"%s (%s)" % (title, count))
			item.setParamDict(action="VideoList", url=u"http://metalvideo.com/%s" % url)
			
			# Store Listitem data
			yield item.getListitemTuple(False)

class Watching(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		import parsers
		with urlhandler.urlopen(plugin["url"], 600) as sourceObj: # TTL = 10 Minutes
			return parsers.WatchingParser().parse(sourceObj)

class TopVideos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		sourceCode = urlhandler.urlread(self.regex_selector(), 14400) # TTL = 4 Hours
		self.cacheToDisc= True
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_program_count)
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_selector(self):
		_plugin = plugin
		# Fetch SourceCode
		url = _plugin["url"]
		sourceCode = urlhandler.urlread(url, 604800) # TTL = 1 Week
		
		# Fetch list of Top Video Category
		topLists = [part for part in re.findall('<option value="(\S+?)"\s*>\s*(.+?)\s*</option>', sourceCode) if not u"Select one" in part[1]]
		titleList = [part[1] for part in topLists]
		
		# Display list for Selection
		ret = _plugin.dialogSelect(_plugin.getuni(30101), titleList)
		if ret >= 0: return topLists[ret][0]
		else: raise _plugin.ScraperError(0, "User Has Quit the Top Display")
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		intCmd = int
		localListitem = listitem.ListItem
		
		# Iterate the list of videos
		for count, url, img, artist, track, views in re.findall('<tr>\s+<td align="center" class="row\d">(\d+).</td>\s+<td align="center" class="row\d" width="\d+"><a href="(\S+?)"><img src="(\S+?)" alt=".+?" class="tinythumb" width="\d+" height="\d+" align="left" border="1" /></a></td>\s+<td class="row\d">(.+?)</td>\s+<td class="row\d"><a href="\S+?">(.+?)</a></td>\s+<td class="row\d">([\d,]+)</td>\s+</tr>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(u"%s. %s - %s" % (count, artist, track))
			item.setThumb(img)
			item.setInfoDict(artist=[artist], count=intCmd(views.replace(u",",u"")))
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")])
			
			# Store Listitem data
			yield item.getListitemTuple(True)

class NewVideos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		sourceCode = urlhandler.urlread(plugin["url"], 14400) # TTL = 4 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Add Next Page if Exists   
		nextUrl = re.findall('<a href="(\S+?)">next \xc2\xbb</a>', sourceCode)
		if nextUrl: self.add_next_page(url={"url":u"http://www.metalvideo.com/%s" % nextUrl[0]})
		
		# Iterate the list of videos
		localListitem = listitem.ListItem
		for url, img, artist, track in re.findall('<tr><td align="center" class="\w+" width="\d+"><a href="(\S+?)"><img src="(\S+?)" alt=".+?"  class="tinythumb" width="\d+" height="\d+" align="left" border="1" /></a></td><td class="\w+" width="\w+">(.+?)<td class="\w+"><a href="\S+?">(.+?)</a></td><td class="\w+">.+?</td></tr>', sourceCode):
			# Create listitem of Data
			item = localListitem()
			
			# Create listitem of Data
			item = localListitem()
			item.setLabel(u"%s - %s" % (artist, track))
			item.setThumb(img)
			item.setInfoDict(artist=[artist])
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")])
			
			# Store Listitem data
			yield item.getListitemTuple(True)

class Related(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode
		url = u"http://metalvideo.com/relatedclips.php?vid=%(url)s" % plugin
		sourceObj = urlhandler.urlopen(url, 14400) # TTL = 4 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch and Return VideoItems
		return self.xml_scraper(sourceObj)
	
	def xml_scraper(self, sourceObj):
		# Import XML Parser and Parse sourceObj
		import xml.etree.ElementTree as ElementTree
		tree = ElementTree.fromstring(sourceObj.read().replace("&","&amp;"))
		sourceObj.close()
		
		# Loop through each Show element
		localListitem = listitem.ListItem
		for node in tree.getiterator(u"video"):
			# Create listitem of Data
			item = localListitem()
			item.setLabel(node.findtext(u"title"))
			item.setThumb(node.findtext(u"thumb"))
			
			# Add url Param
			url = node.findtext(u"url")
			item.setParamDict(action="PlayVideo", url=url)
			
			# Add Context item to link to related videos
			item.addRelatedContext(url=url[url.rfind(u"_")+1:url.rfind(u".")], updatelisting="true")
			
			# Store Listitem data
			yield item.getListitemTuple(True)

class VideoList(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		_plugin = plugin
		# Fetch Sort Method and Crerate New Url
		if u"search.php" in _plugin["url"]: url = _plugin["url"]
		else:
			urlString = {u"0":u"%sdate.html", u"1":u"%sartist.html", u"2":u"%srating.html", u"3":u"%sviews.html"}[_plugin.getSetting("sort")]
			url = urlString % _plugin["url"]
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch SourceObj
		import parsers
		with urlhandler.urlopen(url, 14400) as sourceObj: # TTL = 4 Hours
			return parsers.VideosParser().parse(sourceObj)

class PlayVideo(listitem.PlaySource):
	@plugin.error_handler
	def resolve(self):
		_plugin = plugin
		# When in party mode continuously play random video
		if "partymode" in _plugin:
			# Add Current path to playlist
			playlist = _plugin.xbmc.PlayList(1)
			playlist.add(_plugin.handleThree)
			
			# Return video url untouched
			return self.find_video(0) # TTL = 1 Week
		
		# When randomizer is selected start partymode
		elif _plugin["url"].endswith(u"randomizer.php"):
			# Clear Playlist first
			playlist = _plugin.xbmc.PlayList(1)
			playlist.clear()
			
			# Return Video Player url Twice to start party mode playlist
			return {"url":[self.find_video(0), _plugin.handleThree+"partymode=true"]}
		
		# Play Selected Video
		else:
			# Return video url untouched
			return self.find_video(57600) # TTL = 16 Hours
	
	def find_video(self, TTL=57600):
		# Fetch Page Source
		sourceCode = urlhandler.urlread(plugin["url"], TTL, stripEntity=False)
		
		# Look for Youtube Video First
		try: videoId = [part for part in re.findall('src="(http://www.youtube.com/embed/\S+?)"|file:\s+\'(\S+?)\'', sourceCode)[0] if part][0]
		except: return None
		else:
			if u"metalvideo.com" in videoId: return videoId
			elif u"youtube.com" in videoId: return self.sourceType(videoId, "youtube_com")
