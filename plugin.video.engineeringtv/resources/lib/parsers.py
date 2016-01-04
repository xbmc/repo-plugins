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

class subCategories(HTMLParser.HTMLParser):
	"""
		Parses available shows withen categorys, i.e from http://www.engineeringtv.com/pages/all.videos
	"""
	
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Show """
		
		# Class Vars
		self.divcount = None
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except plugin.ParserError:
			pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.title = None
		self.href = None
		self.base = 0
	
	def handle_starttag(self, tag, attrs):
		# Serch for each data segment
		if tag == "div":
			if self.divcount is None:
				for key, value in attrs:
					if key == u"id" and value == u"magnify_main_area":
						self.divcount = 1
						break
			
			else:
				self.divcount += 1
				for key, value in attrs:
					if key == u"class" and value == u"mvp_page_title_expressive clearfix":
						self.base = self.divcount
						break
		
		# Fetch Video Group Url ID
		elif tag == u"a" and self.divcount == (self.base + 1):
			for key, value in attrs:
				if key == u"href":
					self.href = value[value.rfind("/")+1:]
					break
	
	def handle_data(self, data):
		# Fetch Title
		if self.base: self.title = data.strip()
	
	def handle_endtag(self, tag):
		# Decrement div count on div end tag
		if tag == "div" and self.divcount >= 0:
			self.divcount -= 1
			if self.divcount == 0: raise plugin.ParserError
			elif self.divcount == (self.base - 1):
				self.append((self.title, self.href))
				self.reset_lists()

class VideoParser(HTMLParser.HTMLParser):
	"""
		Parses available episods for current show, i.e from http://www.engineeringtv.com/playlist.mason/Only-Engineering-TV-Videos
	"""
	
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Episodes """
		
		# Class Vars
		self.divcount = None
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except plugin.ParserError:
			pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.setAudioFlags()
		#self.item.setVideoFlags(False)
		self.item.urlParams["action"] = "PlayVideo"
	
	def handle_starttag(self, tag, attrs):
		# Check for required section
		if self.divcount is None:
			# Fetch Next page if Exists
			if tag == u"a":
				varClass = False
				for key, value in attrs:
					if key == u"class" and value == u"mvp-pagenum-next mvp-pagenum-pagelink": varClass = True
					elif varClass is True and key == u"href" and value:
						self.item.add_next_page(url={"url":value})
						break
			
			# Search for required section
			elif tag == u"div":
				for key, value in attrs:
					if key == u"class" and value == u"clearfix mvp_grid_row_first":
						self.divcount = 2
						break
		
		# Increment div counter
		elif tag == u"div": self.divcount += 1
		
		# Fetch Title, Url and Image
		elif tag == u"a" and self.divcount == 5:
			varUrl = varTitle = varImg = None
			for key, value in attrs:
				if key == u"href" and value: varUrl = value[value.rfind("/video/"):]
				elif key == u"title" and value: varTitle = value
				elif key == u"style" and value:
					# Strip Out image url
					value = value[value.find(u"url(")+5:]
					varImg = value[:value.find(u"');")]
			
			# Add Video item with info
			if varUrl and varTitle and varImg:
				# Create listitem of Data
				item = self.item
				item.urlParams["url"] = varUrl
				item.setLabel(varTitle)
				item.setThumb(varImg)
				
				# Add Context item to link to related videos
				item.addRelatedContext(url=varUrl)
				
				# Append listitem to reset
				self.append(self.item.getListitemTuple(True))
				self.reset_lists()
	
	def handle_endtag(self, tag):
		# Decrement div count on div end tag
		if tag == "div" and self.divcount is not None:
			self.divcount -= 1
			if self.divcount == 0:
				raise plugin.ParserError

class RelatedParser(HTMLParser.HTMLParser):
	"""
		Parses available episods for current show, i.e from http://www.engineeringtv.com/video/PXI-based-NI-Semiconductor-Test
	"""
	
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Episodes """
		
		# Class Vars
		self.divcount = None
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except plugin.ParserError:
			pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.setAudioFlags()
		#self.item.setVideoFlags(False)
		self.item.urlParams["action"] = "PlayVideo"
	
	def handle_starttag(self, tag, attrs):
		# Check for required section
		if tag == u"div":
			if self.divcount is not None: self.divcount += 1
			else:
				for key, value in attrs:
					if key == u"id" and value == u"magnify_widget_playlist_wrapper_":
						self.divcount = 1
						break
		
		# Fetch Title, Url and Image
		elif tag == u"a" and self.divcount >= 4:
			for key, value in attrs:
				# Fetch Image Url
				if key == u"style" and value:
					# Strip Out image url
					value = value[value.find(u"url(")+5:]
					value = value[:value.find(u"');")]
					self.item.setThumb(value)
					break
				
				# Fetch Title
				elif key == u"title" and value:
					self.item.setLabel(value)
				
				# Fetch Url
				elif key == u"href" and value:
					self.item.urlParams["url"] = value
					
					# Add Context item to link to related videos
					self.item.addRelatedContext(url=value)
	
	def handle_endtag(self, tag):
		# Decrement div count on div end tag
		if tag == "div" and self.divcount is not None:
			self.divcount -= 1
			if self.divcount == 1:
				self.append(self.item.getListitemTuple(True))
				self.reset_lists()
			elif self.divcount == 0:
				raise plugin.ParserError
