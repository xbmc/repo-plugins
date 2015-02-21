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

BaseURL = u"http://www.watchmojo.com%s"
class CategorysParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.watchmojo.com/
	"""
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		self.section = 0
		
		# Proceed with parsing
		self.extracat = "SubCat" if plugin.getSettingBool("extracat") else "Videos"
		self.reset_lists()
		self.results = []
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return self.results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = self.extracat
		self.idList = []
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if not attrs: return
		section = self.section
		
		# Find Each Category Bock
		if section == 0:
			if tag == u"li":
				for key, value in attrs:
					if key == u"class" and value == u"off":
						self.section = 1
						break
				
			elif tag == u"div":
				for key, value in attrs:
					if key == u"id" and value == u"bar_main":
						raise plugin.ParserError
		
		# Find Each Part within Section Block
		elif section >= 1:
			if section == 1 and tag == u"a":
				for key, value in attrs:
					if key == u"href":
						self.item.urlParams["url"] = value
						self.section = 101 # Title
						url = value[:-2]
						image = url[url.rfind(u"/")+1:].replace(u" ",u"-") + u".png"
						self.item.setThumb(image, 1)
						break
			
			elif section == 2 and tag == u"a":
				for key, value in attrs:
					if key == u"href":
						self.idList.append(value[value.find(u"/", 8)+1:][:-2])
						break
	
	def handle_data(self, data):
		# Fetch Category Title when within Section 2
		if self.section == 101: # Title
			title = data.strip()
			self.item.setLabel(title)
			self.item.urlParams["title"] = title
			self.section = 2
	
	def handle_endtag(self, tag):
		# Search for each end tag
		if self.section >= 1 and tag == u"ul":
			self.section = 0
			self.item.urlParams["idlist"] = u",".join(self.idList)
			self.results.append(self.item.getListitemTuple())
			self.reset_lists()

class ThemesParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.watchmojo.com/video/theme/
	"""
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		self.section = 0
		
		# Proceed with parsing
		self.reset_lists()
		self.results = []
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return self.results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "Videos"
		self.title = None
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		section = self.section
		
		# Find Each Category Bock
		if section == 0 and tag == u"div":
			for key, value in attrs:
				if key == u"class" and value == u"theme_box":
					self.section = 1
					break
				elif key == u"id" and value == u"grid_small":
					raise plugin.ParserError
		
		# Find Each Part within Section Block
		elif section >= 1:
			if tag == u"img":
				for key, value in attrs:
					if key == u"src":
						self.item.setThumb(BaseURL % value)
						break
			
			elif tag == u"a":
				varhref = carclass = None
				for key, value in attrs:
					if key == u"href": varhref = value
					elif key == u"class" and value == u"theme": carclass = True
				
				if varhref and carclass:
					self.item.urlParams["url"] = varhref
					self.section = 101 # Title
			
			elif tag == u"span":
				self.section = 102 # Title with Video Count
	
	def handle_data(self, data):
		# Fetch HTML Tag Data
		if self.section == 101: # Title
			self.title = data
			self.section = 1
		elif self.section == 102: # Title with Video Count
			self.item.setLabel(u"%s (%s)" % (self.title, data[:data.find(u" ")]))
			self.results.append(self.item.getListitemTuple())
			self.reset_lists()
			self.section = 0

class VideosParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.watchmojo.com/video/id/11529/
	"""
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		self.section = 0
		
		# Proceed with parsing
		self.reset_lists()
		self.results = []
		try:
			if encoding: self.feed(html.decode(encoding).replace(u'_blank"',u''))
			else: self.feed(html.replace(u'_blank"',u''))
		except plugin.ParserError: pass
		
		# Return Results
		return self.results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "PlayVideo"
		self.item.setVideoFlags(False)
		self.item.setAudioFlags()
	
	def handle_starttag(self, tag, attrs):
		# Quck ref
		section = self.section
		
		# Find Each Category Bock
		if section == 0:
			if tag == u"a":
				varhref = varclass = None
				for key, value in attrs:
					if key == u"href": varhref = value
					elif key == u"class" and value == u"grid_image": varclass = True
				
				if varhref and varclass:
					self.item.urlParams["url"] = varhref
					self.section = 1
				
			elif tag == u"div":
				for key, value in attrs:
					if key == u"id" and value == u"next":
						self.section = -1
						break
		
		# Find Each Part within Section Block
		elif section >= 1:
			# Fetch image url
			if tag == u"img":
				for key, value in attrs:
					if key == u"src":
						self.item.setThumb(BaseURL % value)
						break
			
			# Fetch Date
			elif tag == u"span":
				for key, value in attrs:
					if key == u"class" and value == u"adate":
						self.section = 101 # Date
						break
			
			# Fetch Title
			elif tag == u"a":
				for key, value in attrs:
					if key == u"class" and value == u"title":
						self.section = 102 # Title
						break
			
			# Fetch Plot
			elif tag == u"br":
				self.section = 103 # Plot
		
		# Find Next Page
		elif section == -1:
			if tag == u"a":
				for key, value in attrs:
					if key == u"href" and value[:7] == u"/video/":
						self.item.add_next_page(url={"url":value})
						raise plugin.ParserError
			else:
				raise plugin.ParserError
	
	def handle_data(self, data):
		# Fetch Category Title when within Section 2 or 3
		section = self.section
		if section == 101: # Date
			self.item.setDate(data, "%B %d, %Y")
			self.section = 1
		elif section == 102: # Title
			self.item.setLabel(data)
			self.section == 1
		elif section == 103: # Plot
			if data.startswith(u"hosted by"): self.section = 1
			else: 
				self.item.infoLabels["plot"] = data.strip()
				self.section = 1
	
	def handle_endtag(self, tag):
		# Search for each end tag
		if self.section >= 1 and tag == u"div":
			self.section = 0
			self.results.append(self.item.getListitemTuple(True))
			self.reset_lists()
