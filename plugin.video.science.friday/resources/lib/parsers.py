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
import HTMLParser
from xbmcutil import listitem, plugin

BaseURL = u"http://www.sciencefriday.com%s"
class VideosParser(HTMLParser.HTMLParser):
	""" Parses Videos, i.e http://www.sciencefriday.com/topics/space.html#page/bytopic/1 """
	def parse(self, urlobject, contentType, encoding="utf8"):
		return self.fromstring(urlobject.read(), contentType, encoding)
	
	def fromstring(self, html, contentType, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		_plugin = plugin
		self.contentVideo = "PlayVideo" if "video" in contentType else "PlayAudio"
		self.contentType = contentType
		self.divcount = None
		self.section = 0
		
		# Fetch Quality Setting from Youtube Addon
		if _plugin["type"] == u"video-list": self.isHD = _plugin.isYoutubeHD()
		else: self.isHD = None
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except EOFError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = self.contentVideo
		self.item.setVideoFlags(self.isHD)
		self.item.setAudioFlags()
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		divcount = self.divcount
		if divcount == 0: raise EOFError
		elif tag == u"div":
			# Increment div counter when within show-block
			if divcount: self.divcount +=1
			else:
				# Check for required section
				for key, value in attrs:
					if key == u"id" and value == self.contentType:
						self.divcount = 1
						break
			
		# Fetch video info Block
		elif divcount == 3:
			# Check for Title, Plot and Date
			if tag == u"h4": self.section = 101
			elif tag == u"a" and self.section == 102:
				# Check for url and title
				for key, value in attrs:
					if key == u"href":
						self.item.urlParams["url"] = value
						self.section = 103
						break
		
		# Fetch Image Block
		elif divcount == 5 and tag == u"img":
			# Fetch video Image
			for key, value in attrs:
				if key == u"data-lazysrc":
					self.item.setThumb(BaseURL % value)
					break
	
	def handle_data(self, data):
		# When within selected section fetch Time
		if self.section == 101: # Date
			self.item.setDate(data, "%b. %d, %Y")
			self.section = 102
		elif self.section == 103: # Title
			self.item.setLabel(data)
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == u"div" and self.divcount:
			self.divcount -= 1
			
			# When at closeing tag for show-block, save fetched data
			if self.divcount == 1:
				self.append(self.item.getListitemTuple(True))
				self.reset_lists()

class RecentParser(HTMLParser.HTMLParser):
	""" Parses Recent Videos, i.e http://www.sciencefriday.com/video/index.html#page/full-width-list/1 """
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """

		# Class Vars
		_plugin = plugin
		self.divcount = None
		self.section = 0
		
		# Fetch Quality Setting from Youtube Addon
		if _plugin["type"] == "video":
			self.contentAction = "PlayVideo"
			self.isHD = _plugin.isYoutubeHD()
		else:
			self.contentAction = "PlayAudio"
			self.isHD = None
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except EOFError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = self.contentAction
		self.item.setVideoFlags(self.isHD)
		self.item.setAudioFlags()
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise EOFError
		elif tag == u"div":
			# Increment div counter when within show-block
			if self.divcount: self.divcount +=1
			else:
				# Check for required section
				for key, value in attrs:
					if key == u"id" and value == u"full-width-list":
						self.divcount = 1
						break
			
		# Fetch video info Block
		elif self.divcount == 4:
			# Check for Title, Plot and Date
			if tag == u"h4": self.section = 101
			elif tag == u"p": self.section = 102
			elif tag == u"a":
				# Check for url and title
				for key, value in attrs:
					if key == u"href":
						self.item.urlParams["url"] = value
						self.section = 103
						break
		
		# Fetch Image Block
		elif self.divcount == 5 and tag == u"img":
			# Fetch video Image
			for key, value in attrs:
				if key == u"data-lazysrc":
					self.item.setThumb(BaseURL % value)
					break
	
	def handle_data(self, data):
		# When within selected section fetch Time
		if self.section == 101: # Date
			self.item.setDate(data, "%b. %d, %Y")
			self.section = 0
		elif self.section == 102: # Plot
			self.item.infoLabels["plot"] = data.strip()
			self.section = 0
		elif self.section == 103: # Title
			self.item.setLabel(data)
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == u"div" and self.divcount:
			self.divcount -= 1
			
			# When at closeing tag for show-block, save fetched data
			if self.divcount == 1:
				self.append(self.item.getListitemTuple(True))
				self.reset_lists()
