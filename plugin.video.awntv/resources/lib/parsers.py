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

class Categories(HTMLParser.HTMLParser):
	"""
	Parses, http://www.awntv.com/categories
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
		self.item.urlParams["action"] = "Videos"
	
	def handle_starttag(self, tag, attrs):
		# Check for starting section
		if self.divcount == 0: raise plugin.ParserError
		elif tag == u"div":
			# Check for required section
			if self.divcount: self.divcount += 1
			else:
				for key, value in attrs:
					if key == u"class" and value[:36] == u"inside panels-flexible-region-inside":
						self.divcount = 1
						break
		
		# Check for Pane Title
		elif self.divcount == 2 and tag == u"h2":
			self.section = 101
		
		# Check for sub titles
		elif self.divcount == 7 and tag == u"a":
			# Search for Categorie url
			for key, value in attrs:
				if key == u"href":
					self.item.urlParams["url"] = value
					self.section = 102
					break
	
	def handle_data(self, data):
		# When within selected section fetch data
		if self.section == 101: # Main Title
			self.item.setLabel(u"[COLOR blue][B]%s[/B][/COLOR]" % data.strip())
			self.item.urlParams = {}
			self.section = 0
			self.append(self.item.getListitemTuple(False))
			self.reset_lists()
		elif self.section == 102: # Sub Title
			self.item.setLabel(data)
			self.section = 0
			self.append(self.item.getListitemTuple(False))
			self.reset_lists()
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if self.divcount and tag == u"div": self.divcount -= 1

class VideosParser(HTMLParser.HTMLParser):
	"""
	Parses, http://www.awntv.com/category/all-audiences
	"""
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Decode HTML if needed
		if encoding: html = html.decode(encoding)
		
		# Class Vars
		self.divcount = None
		self.section = 0
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		
		# Add next page if available
		import re
		try: listitem.ListItem.add_next_page({"url": re.findall('<a title="Go to next page" href="(/\S+?)">next', html)[0]})
		except IndexError: pass
		
		# Parse HTML
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "PlayVideo"
	
	def handle_starttag(self, tag, attrs):
		# Search for starting section
		if self.divcount == 0: raise plugin.ParserError
		elif self.divcount == None and tag == u"div":
			for key, value in attrs:
				if key == u"class" and value == u"view-content":
					self.divcount = 1
					break
		
		# Fetch Each Cartoon
		elif self.divcount == 1:
			# Increment counter to indicate episods block
			if tag == u"article": self.divcount = 2
			elif tag == u"div":
				for key, value in attrs:
					if key == u"class" and value == u"item-list":
						self.divcount = 0
						break
		
		elif self.divcount == 2:
			# Fetch Url and Title
			if tag == u"a":
				varHref = varTitle = None
				for key, value in attrs:
					if key == u"href": varHref = value
					elif key == u"title": varTitle = value
				
				# Set title and url when found
				if varHref and varTitle:
					self.item.addRelatedContext(action="PlaylistVids", url=varHref)
					self.item.urlParams["url"] = varHref
					self.item.setLabel(varTitle)
			
			# Fetch Image
			elif tag == u"img":
				for key, value in attrs:
					if key == u"src":
						self.item.setThumb(value)
			
			# Fetch Plot
			elif tag == u"div":
				attrs = [key for key, value in attrs]
				if u"class" in attrs and u"property" in attrs:
					self.section = 101
	
	def handle_data(self, data):
		# When within selected section fetch data
		if self.section == 101: # Plot
			self.item.infoLabels["plot"] = data
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if self.divcount and tag == u"article":
			self.divcount = 1
			self.append(self.item.getListitemTuple(True))
			self.reset_lists()

class PlaylistsParser(HTMLParser.HTMLParser):
	"""
	Parses, http://www.awntv.com/playlists
	"""
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Decode HTML if needed
		if encoding: html = html.decode(encoding)
		
		# Class Vars
		self.divcount = None
		self.section = 0
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		
		# Add next page if available
		import re
		try: listitem.ListItem.add_next_page({"url": re.findall('<a title="Go to next page" href="(/playlists\S+?)">next', html)[0]})
		except IndexError: pass
		
		# Parse HTML
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "PlaylistVids"
	
	def handle_starttag(self, tag, attrs):
		# Search for starting section
		if self.divcount == 0: raise plugin.ParserError
		elif tag == u"div":
			# Check for required section
			if self.divcount: self.divcount += 1
			else:
				for key, value in attrs:
					if key == u"class" and value == u"region-inner region-content-inner":
						self.divcount = 1
						break
		
		# Check for required section for url
		elif self.divcount >= 8:
			# Fetch divcount counter
			divcount = self.divcount
			# Check for url
			if divcount == 8 and tag == u"a":
				for key, value in attrs:
					if key == u"href":
						self.item.urlParams["url"] = value
						self.section = 101
						break
			
			# Check for required section for plot
			elif divcount == 9 and tag == u"p":
				self.section = 102
			
			# Check for img
			elif divcount == 11 and tag == u"img":
				# Fetch image url
				for key, value in attrs:
					if key == u"src":
						self.item.setThumb(value)
						break
	
	def handle_data(self, data):
		# When within selected section fetch data
		if self.section == 101: # Title
			self.item.setLabel(data)
			self.section = 0
		elif self.section == 102: # Plot
			self.item.infoLabels["plot"] = data
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == u"div" and self.divcount:
			self.divcount -= 1
			if self.divcount == 6:
				self.append(self.item.getListitemTuple(False))
				self.reset_lists()

class PlaylistVidParser(HTMLParser.HTMLParser):
	"""
	Parses, http://www.awntv.com/playlists/trailer-hitch-top-ten
	"""
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Decode HTML if needed
		if encoding: html = html.decode(encoding)
		
		# Class Vars
		self.divcount = None
		self.section = 0
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		
		# Add next page if available
		import re
		try: listitem.ListItem.add_next_page({"url": [url for url in re.findall('<a title="Go to next page" href="(/playlists\S+?)">next|<a title="Go to next page" href="(/channels\S+?)">next', html)[0] if url][0]})
		except IndexError: pass
		
		# Parse HTML
		try: self.feed(html)
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.title = ""
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "PlayVideo"
	
	def handle_starttag(self, tag, attrs):
		# Searc for starting section
		if self.divcount == 0: raise plugin.ParserError
		elif tag == u"div":
			# Check for required section
			if self.divcount: self.divcount += 1
			else:
				for key, value in attrs:
					if key == u"class" and (value[:25] == u"view view-related-content" or value[:19] == u"view view-playlists" or value[:18] == u"view view-channels"):
						self.divcount = 1
						break
		
		# Check for required section for url
		elif self.divcount == 4 and tag == u"a":
			# Fetch video url
			for key, value in attrs:
				if key == u"href":
					self.item.addRelatedContext(action="PlaylistVids", url=value)
					self.item.urlParams["url"] = value
					self.section = 101
					break
		
		# Check for image
		elif self.divcount == 5 and (tag == u"img" or tag == u"p"):
			#Check for img
			if tag == u"img":
				for key, value in attrs:
					if key == u"src":
						self.item.setThumb(value)
						break
			
			# Check for plot
			elif tag == u"p":
				self.section = 102
	
	def handle_data(self, data):
		# When within selected section fetch data
		if self.section == 101: # Title
			data = data.strip()
			if data: self.title += data
			else: self.section = 0
		elif self.section == 102: # Plot
			self.item.infoLabels["plot"] = data
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrease div counter on all closing div elements
		if tag == u"div" and self.divcount:
			self.divcount -= 1
			if self.divcount == 2:
				self.section = 0
				self.item.setLabel(self.title)
				self.append(self.item.getListitemTuple(True))
				self.reset_lists()
