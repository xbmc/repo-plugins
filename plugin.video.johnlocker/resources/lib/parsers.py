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
	""" Parses Categories from http://johnlocker.com/us """
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		self.section = None
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try:
			if isinstance(html, unicode): self.feed(html)
			else: self.feed(html.decode(encoding))
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "ListVideos"
	
	def handle_starttag(self, tag, attrs):
		# If not attrs exist then i dont need to proceed
		if attrs:
			# Find show-block elements and all div sub elements
			if tag == u"li":
				# Check for required section
				for key, value in attrs:
					if key == u"class" and value[:17] == u"cat-item cat-item":
						self.section = 1
						break
			
			# When within show-block fetch show data
			elif tag == u"a" and self.section == 1:
				# Fetch url
				for key, value in attrs:
					if key == u"href":
						self.item.urlParams[u"url"] = value
						self.section = 101
						break
	
	def handle_data(self, data):
		# Fetch Category Title
		if self.section == 101: # title
			# Fetch Title
			self.item.setLabel(data)
			self.section = 0
			
			# End Directory item and reset
			self.append(self.item.getListitemTuple(False))
			self.reset_lists()
	
	def handle_endtag(self, tag):
		# End parsing when at end of required data block
		if tag == "ul" and self.section == 0:
			raise plugin.ParserError

class VideoParser(HTMLParser.HTMLParser):
	""" Parses video from http://johnlocker.com/category/science-tech/ """
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """

		# Class Vars
		self.section = 0
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try:
			if isinstance(html, unicode): self.feed(html)
			else: self.feed(html.decode(encoding))
		except plugin.ParserError: pass
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "system.source"
		self.item.setVideoFlags(None)
		self.item.setAudioFlags()
		self.Thumb = None
		self.url = None
	
	def handle_starttag(self, tag, attrs):
		# If not attrs exist then i dont need to proceed
		if attrs:
			# Find show-block elements and all div sub elements
			if tag == u"main":
				for key, value in attrs:
					if key == u"itemprop" and value == u"mainContentOfPage":
						self.section = 1
						break
			
			# Check for article section to indecate the required section
			elif tag == u"article" and self.section == 1:
				self.section = 2
				self.reset_lists()
			
			# When within required section search for video data
			elif self.section == 2:
				# Check for Image Url
				if tag == u"img":
					for key, value in attrs:
						if key == u"src":
							self.Thumb = value
							break
				
				# Check for Youtube Video Url
				if tag == u"iframe":
					varsrc = varclass = None
					for key, value in attrs:
						if key == u"class" and value == u"youtube-player": varclass = True
						elif key == u"src": varsrc = value
					
					if varsrc and varclass:
						self.item.urlParams["sourcetype"] = "urlchecker"
						self.url = varsrc
					
						# If video link is not a playlist. I.E Plan Video, then set image to the youtube image
						if not u"/embed/videoseries" in varsrc: self.Thumb = u"http://img.youtube.com/vi/%s/0.jpg" % varsrc[varsrc.rfind(u"/")+1:varsrc.find(u"?")]
				
				# Check for Title
				elif tag == u"a":
					varrel = varhref = None
					for key, value in attrs:
						if key == u"rel" and value == u"bookmark": varrel = True
						elif key == u"href": varhref = value
					
					if varrel and varhref:
						if not self.url: self.url = varhref
						self.section = 101
				
				# Check for date
				elif tag == u"time":
					vardatetime = varclass = None
					for key, value in attrs:
						if key == u"class" and value == u"entry-date updated": varclass = True
						elif key == u"datetime": vardatetime = value
					
					if vardatetime and varclass:
						date = vardatetime[:vardatetime.find(u"T")]
						self.item.setDate(date, "%Y-%m-%d")
				
				# Check for Views
				elif tag == u"span":
					for key, value in attrs:
						if key == u"class" and value == u"entry-view":
							self.section = 102
							break
	
	def handle_data(self, data):
		# Fetch Episode Count
		if self.section == 101: # title
			self.item.setLabel(data)
			self.section = 2
		
		# Fetch Video View count
		elif self.section == 102: # Views
			self.item.setCount(data[:data.find(u" ")])
			self.section = 2
	
	def handle_endtag(self, tag):
		# Check for the end article to mark end of section
		if tag == "article" and self.section == 2:
			self.section = 1
			self.item.setThumb(self.Thumb)
			self.item.urlParams["url"] = self.url
			self.append(self.item.getListitemTuple(True))
		
		elif tag == "main" and self.section == 1:
			raise plugin.ParserError
