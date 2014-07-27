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

BASEURL = u"http://www.toonjet.com/%s"
class CartoonsParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.toonjet.com/about/
	"""
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		self.divcount = None
		self.section = 0
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "Cartoons"
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		elif tag == u"div":
			# Convert Attributes to a Dictionary
			attrs = dict(attrs)
			
			# Check for required section
			if self.divcount: self.divcount += 1
			elif u"id" in attrs and attrs[u"id"] == u"menu_div": self.divcount = 1
		
		# Fetch Each Cartoon
		elif self.divcount == 2:
			# Convert Attributes to a Dictionary
			attrs = dict(attrs)
			
			# Check for Url
			if tag == u"a" and u"href" in attrs and u"style" in attrs:
				self.item.urlParams["url"] = attrs[u"href"]
				self.section = 101
			elif tag == u"img" and u"src" in attrs:
				self.item.setThumbnailImage(BASEURL % attrs[u"src"])
	
	def handle_data(self, data):
		# When within selected section fetch data
		if self.section == 101: # Title
			self.item.setLabel(data.strip())
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if self.divcount and tag == u"div":
			self.divcount -= 1
			
			# When at closeing tag for show-block, save fetched data
			if self.divcount == 1:
				if self.item.urlParams["url"] == u"featured/":
					self.reset_lists()
				else:
					self.append(self.item.getListitemTuple(False))
					self.reset_lists()

class VideoParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.toonjet.com/cartoons/TomandJerry/
	"""
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Decode html if needed
		if encoding: html = html.decode(encoding)
		
		# Class Vars
		self.divcount = None
		self.section = 0
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		
		# Parse HTML
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Add Next page
		import re
		nextUrls = re.findall('<a href="(cartoons/\S+?)" class="cartoons">More...</a>|<a href="(cartoons/\S+?)">Next >></a>', html)
		if nextUrls:
			nextUrl = [url for url in nextUrls[0] if url]
			if nextUrl: results.append(listitem.ListItem.add_next_page(url={"url":nextUrl[0]}))
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "system.source"
		self.item.setQualityIcon(False)
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		elif tag == u"table":
			# Convert Attributes to a Dictionary
			attrs = dict(attrs)
			
			# Check for required section
			if self.divcount: self.divcount += 1
			elif u"align" in attrs and u"border" in attrs and u"id" not in attrs and u"width" not in attrs and attrs[u"align"] == u"center" and attrs[u"border"] == u"0":
				self.divcount = 1
		
		# Fetch Each Cartoon
		elif self.divcount >= 3:
			# Convert Attributes to a Dictionary
			attrs = dict(attrs)
			
			# Check for Url
			if tag == u"a" and u"href" in attrs and u"class" in attrs and attrs[u"class"] == u"cartoons1":
				self.item.urlParams["url"] = BASEURL % attrs[u"href"]
				self.section = 101
			elif tag == u"img" and u"src" in attrs:
				self.item.setThumbnailImage(BASEURL % attrs[u"src"])
			elif tag == u"h5":
				self.section = 102
	
	def handle_data(self, data):
		# When within selected section fetch Data
		if self.section == 101: # Title
			self.item.setLabel(data.strip())
			self.section = 0
		elif self.section == 102: # Plot
			self.item.infoLabels["plot"] = data.strip()
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if self.divcount and tag == u"table":
			self.divcount -= 1
			
			# When at closeing tag for show-block, save fetched data
			if self.divcount == 2:
				self.append(self.item.getListitemTuple(True))
				self.reset_lists()

class FeaturedParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.toonjet.com/featured/
	"""
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Decode html if needed
		if encoding: html = html.decode(encoding)
		
		# Class Vars
		self.divcount = None
		self.section = 0
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		
		# Add Next page
		import re
		nextUrl = re.findall('<a href="(featured.php\?\S+?)">Next >></a>', html)
		if nextUrl: results.append(listitem.ListItem.add_next_page(url={"url":nextUrl[0]}))
		
		# Parse HTML
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "system.source"
		self.item.setQualityIcon(False)
		self.title = ""
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		elif self.divcount == None and tag == u"div":
			# Convert Attributes to a Dictionary
			attrs = dict(attrs)
			
			# Check for required section
			if u"id" in attrs and attrs[u"id"] == u"userltblue": self.divcount = 1
			
		# Fetch video info Block
		elif self.divcount >= 1:
			# Convert Attributes to a Dictionary
			attrs = dict(attrs)
			
			# Check for Table Section
			if tag == u"td" and u"align" in attrs and attrs[u"align"] == u"center": self.divcount = 2
			elif self.divcount == 2:
				# Check for Url
				if tag == u"a" and u"href" in attrs:
					self.item.urlParams["url"] = BASEURL % attrs[u"href"]
					self.section = 101
				elif tag == u"img" and u"src" in attrs:
					self.item.setThumbnailImage(attrs[u"src"])
	
	def handle_data(self, data):
		# When within selected section fetch Data
		if self.section == 101: # Title
			if u"views" in data.lower():
				data = data.strip()
				self.item.infoLabels["count"] = int(data[:data.find(u" ")].replace(u",",u""))
			else:
				self.title = "%s %s" % (self.title, data.strip())
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if self.divcount == 1 and tag == u"div":
			self.divcount = 0
		elif self.divcount == 2 and tag == u"td":
			self.divcount = 1
			self.section = 0
			self.item.setLabel(self.title.replace(u'"',u""))
			self.append(self.item.getListitemTuple(True))
			self.reset_lists()
