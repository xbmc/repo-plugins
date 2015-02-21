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
			# Check for required section
			if self.divcount: self.divcount += 1
			else:
				for key, value in attrs:
					if key == u"id" and value == u"menu_div":
						self.divcount = 1
						break
		
		# Fetch Each Cartoon
		elif self.divcount == 2:
			# Fetch url
			if tag == u"a":
				varHref = varStyle = False
				for key, value in attrs:
					if key == u"href": varHref = value
					elif key == u"style": varStyle = True
				
				if varHref and varStyle:
					self.item.urlParams["url"] = varHref
					self.section = 101
			
			# Fetch image
			elif tag == u"img":
				for key, value in attrs:
					if key == u"src":
						self.item.setThumb(BASEURL % value)
						break
	
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
			if nextUrl: listitem.ListItem.add_next_page(url={"url":nextUrl[0]})
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "system.source"
		self.item.setVideoFlags(False)
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		elif tag == u"table":
			# Check for required section
			if self.divcount: self.divcount += 1
			else:
				# Convert Attributes to a Dictionary
				attrs = dict(attrs)
				if u"align" in attrs and u"border" in attrs and u"id" not in attrs and u"width" not in attrs and attrs[u"align"] == u"center" and attrs[u"border"] == u"0":
					self.divcount = 1
		
		# Fetch Each Cartoon
		elif self.divcount >= 3:
			# Check for Url
			if tag == u"a":
				varHref = carClass = None
				for key, value in attrs:
					if key == u"href": varHref = value
					elif key == u"class" and value == u"cartoons1": carClass = True
				
				if varHref and carClass:
					self.item.urlParams["url"] = BASEURL % varHref
					self.section = 101
			
			# Fetch image
			elif tag == u"img":
				for key, value in attrs:
					if key == u"src":
						self.item.setThumb(BASEURL % value)
						break
			
			# Fetch Plot
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
		if nextUrl: listitem.ListItem.add_next_page(url={"url":nextUrl[0]})
		
		# Parse HTML
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "system.source"
		self.item.setVideoFlags(False)
		self.title = ""
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if self.divcount == 0: raise plugin.ParserError
		elif self.divcount == None and tag == u"div":
			# Check for required section
			for key, value in attrs:
				if key == u"id" and value == u"userltblue":
					self.divcount = 1
					break
		
		# Fetch video info Block
		elif self.divcount >= 1:
			# Check for Table Section
			if tag == u"td":
				for key, value in attrs:
					if key == u"align" and value == u"center":
						self.divcount = 2
						break
			
			# Check for url section
			elif self.divcount == 2:
				# Fetch url
				if tag == u"a":
					for key, value in attrs:
						if key == u"href":
							self.item.urlParams["url"] = BASEURL % value
							self.section = 101
							break
				
				# Fetch image url
				elif tag == u"img":
					for key, value in attrs:
						if key == u"src":
							self.item.setThumb(value)
							break
	
	def handle_data(self, data):
		# When within selected section fetch Data
		if self.section == 101: # Title
			if u"views" in data.lower():
				data = data.strip()
				self.item.setCount(int(data[:data.find(u" ")].replace(u",",u"")))
			else:
				self.title = "%s %s" % (self.title, data.strip())
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if self.divcount == 1 and tag == u"div":
			self.divcount = 0
		elif self.divcount == 2 and tag == u"td":
			self.divcount = 1
			self.section = 0
			self.item.setLabel(self.title.replace(u'"',u"").strip())
			self.append(self.item.getListitemTuple(True))
			self.reset_lists()
