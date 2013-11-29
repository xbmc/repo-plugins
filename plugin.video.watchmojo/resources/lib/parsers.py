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
import HTMLParser
from xbmcutil import listitem, plugin

class CategorysParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.watchmojo.com/
	"""
	def parse(self, html):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		self.section = 0
		
		# Proceed with parsing
		self.reset_lists()
		self.results = []
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return self.results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "SubCat"
		self.idList = []
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if attrs: attrs = dict(attrs)
		else: return
		section = self.section
		
		# Find Each Category Bock
		if section == 0:
			if tag == "li" and "class" in attrs and attrs["class"] == "off":
				self.section = 1
			elif tag == "div" and "id" in attrs and attrs["id"] == "bar_main":
				raise plugin.ParserError
		
		# Find Each Part within Section Block
		elif section >= 1:
			if section == 1 and tag == "a" and "href" in attrs:
				url = attrs["href"]
				self.item.urlParams["url"] = url
				self.section = 101 # Title
				url = url[:-2]
				image = url[url.rfind("/")+1:].replace(" ","-") + ".png"
				self.item.setThumbnailImage(image, 1)
			elif section == 2 and tag == "a" and "href" in attrs:
				url = attrs["href"]
				self.idList.append(url[url.find("/", 8)+1:][:-2])
	
	def handle_data(self, data):
		# Fetch Category Title when within Section 2
		if self.section == 101: # Title
			self.item.setLabel(data)
			self.section = 2
	
	def handle_endtag(self, tag):
		# Search for each end tag
		if self.section >= 1 and tag == "ul":
			self.section = 0
			self.item.urlParams["idlist"] = ",".join(self.idList)
			self.results.append(self.item.getListitemTuple())
			self.reset_lists()

class ThemesParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.watchmojo.com/video/theme/
	"""
	def parse(self, html):
		""" Parses SourceCode and Scrape Categorys """

		# Class Vars
		self.section = 0
		
		# Proceed with parsing
		self.reset_lists()
		self.results = []
		try: self.feed(html)
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
		if attrs: attrs = dict(attrs)
		section = self.section
		
		# Find Each Category Bock
		if section == 0 and tag == "div":
			if "class" in attrs and attrs["class"] == "theme_box":
				self.section = 1
			elif "id" in attrs and attrs["id"] == "grid_small":
				raise plugin.ParserError
		
		# Find Each Part within Section Block
		elif section >= 1:
			if tag == "img" and "src" in attrs:
				self.item.setThumbnailImage(attrs["src"])
			elif tag == "a" and "class" in attrs and attrs["class"] == "theme":
				self.item.urlParams["url"] = attrs["href"]
				self.section = 101 # Title
			elif tag == "span":
				self.section = 102 # Title with Video Count
	
	def handle_data(self, data):
		# Fetch HTML Tag Data
		if self.section == 101: # Title
			self.title = data
			self.section = 1
		elif self.section == 102: # Title with Video Count
			self.item.setLabel("%s (%s)" % (self.title, data[:data.find(" ")]))
			self.results.append(self.item.getListitemTuple())
			self.reset_lists()
			self.section = 0

class VideosParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.watchmojo.com/video/id/11529/
	"""
	def parse(self, html):
		""" Parses SourceCode and Scrape Categorys """

		# Class Vars
		self.section = 0
		
		# Proceed with parsing
		self.reset_lists()
		self.results = []
		try: self.feed(html.replace('_blank"',''))
		except plugin.ParserError: pass
		
		# Return Results
		return self.results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "PlayVideo"
		self.item.setQualityIcon(False)
		self.item.setAudioInfo()
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if attrs: attrs = dict(attrs)
		section = self.section
		
		# Find Each Category Bock
		if section == 0:
			if tag == "a" and "href" in attrs and "class" in attrs and attrs["class"] == "grid_image":
				self.item.urlParams["url"] = attrs["href"]
				self.section = 1
			elif tag == "div" and "id" in attrs and attrs["id"] == "next":
				self.section = -1
		
		# Find Each Part within Section Block
		elif section >= 1:
			if tag == "img" and "src" in attrs:
				self.item.setThumbnailImage(attrs["src"])
			elif tag == "span" and "class" in attrs and attrs["class"] == "adate":
				self.section = 101 # Date
			elif tag == "a" and "class" in attrs and attrs["class"] == "title":
				self.section = 102 # Title
			elif tag == "br":
				self.section = 103 # Plot
		
		# Find Next Page
		elif section == -1:
			if tag == "a" and "href" in attrs and attrs["href"].startswith("/video/"):
				self.results.append(self.item.add_next_page(url={"url":attrs["href"]}))
				raise plugin.ParserError
			else:
				raise plugin.ParserError
	
	def handle_data(self, data):
		# Fetch Category Title when within Section 2 or 3
		section = self.section
		if section == 101: # Date
			self.item.setDateInfo(data, "%B %d, %Y")
			self.section = 1
		elif section == 102: # Title
			self.item.setLabel(data)
			self.section == 1
		elif section == 103: # Plot
			if data.startswith("hosted by"): self.section = 1
			else: 
				self.item.infoLabels["plot"] = data.strip()
				self.section = 1
	
	def handle_endtag(self, tag):
		# Search for each end tag
		if self.section >= 1 and tag == "div":
			self.section = 0
			self.results.append(self.item.getListitemTuple(True))
			self.reset_lists()
