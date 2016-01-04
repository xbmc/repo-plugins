"""
	Copyright: (c) 2016 William Forde (willforde+kodi@gmail.com)
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
class TopicsParser(HTMLParser.HTMLParser):
	""" Parses Videos, i.e http://www.sciencefriday.com/explore/ """
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		self.divcount = None
		self.section = 0
		self.sfid = None
		
		# Deside on content type to show be default
		_plugin = plugin
		self.icon = icon = _plugin.getIcon()
		if _plugin.getSetting("defaultview") == u"0":
			self.addContent = self._context(_plugin.getuni(30103), "segment")
			self.type = "video"
		else:
			self.addContent = self._context(_plugin.getuni(30104), "video")
			self.type = "segment"
		
		# Proceed with parsing
		results = []
		self.reset_lists()
		self.append = results.append
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except EOFError: pass
		
		# Add Extra Items
		self.item.add_item(_plugin.getuni(30101), thumbnail=(icon,0), url={"action":"ContentLister", "sfid":self.sfid, "type":"video", "topic":""})
		self.item.add_item(_plugin.getuni(30102), thumbnail=(icon,0), url={"action":"ContentLister", "sfid":self.sfid, "type":"segment", "topic":""})
		
		# Return Results
		return results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "ContentLister"
	
	def handle_starttag(self, tag, attrs):
		# Search for sfid
		if tag == u"form" and self.divcount is None and not self.sfid:
			self.sfid = None
			for key, value in attrs:
				if key == u"data-sf-form-id":
					self.sfid = value
					self.divcount = 1
					break
		
		# Search for Select Statement
		elif tag == u"select" and self.divcount == 1:
			_class = _name = None
			for key, value in attrs:
				if key == u"class" and value == u"postform": _class = True
				elif key == u"name" and value.startswith(u"_sft_topic"): _name = True
			
			# If both are true then found required section
			if _class and _name: self.divcount = 2
		
		# Search for Topic id
		elif tag == u"option" and self.divcount == 2:
			_class = _value = _data = None
			for key, value in attrs:
				if key == u"class" and value.startswith(u"level-0 sf-item"): _class = True
				elif key == u"data-sf-cr": _data = True
				elif key == u"value": _value = value
			
			# When found append to listitem object
			if _class and _data and _value:
				self.section = 101
				self.divcount += 1
				self.addContent(_value)
				self.item.setThumb(self.icon)
				self.item.urlParams["sfid"] = self.sfid
				self.item.urlParams["type"] = self.type
				self.item.urlParams["topic"] = _value
	
	def handle_data(self, data):
		# Fetch Title
		if self.section == 101:
			self.item.setLabel(data.strip())
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrement div count on div end tag
		if self.divcount > 1:
			if tag == u"select": raise EOFError
			elif tag == u"option" and self.divcount == 3:
				self.append(self.item.getListitemTuple(False))
				self.reset_lists()
				self.divcount -=1
	
	def _context(self, title, type):
		def wrapper(topic):
			self.item.addContextMenuItem(title, "XBMC.Container.Update", action="ContentLister", sfid=self.sfid, topic=topic, type=type)
		return wrapper

class ContentParser(HTMLParser.HTMLParser):
	""" Parses Videos, i.e http://www.sciencefriday.com/wp-admin/admin-ajax.php?action=get_results&paged=1&sfid=1183&post_types=video&_sft_topic=earth-science """
	def parse(self, urlobject, encoding="utf8"):
		return self.fromstring(urlobject.read(), encoding)
	
	def fromstring(self, html, encoding="utf8"):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		_plugin = plugin
		self.nextUrl = _plugin.copy()
		self.contentVideo = "system.source" if _plugin["type"] == "video" else "PlayAudio"
		self.divcount = None
		self.section = 0
		self.icon = _plugin.getIcon()
		
		# Fetch Quality Setting from Youtube Addon
		if _plugin["type"] == u"video": self.isHD = _plugin.isYoutubeHD()
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
		self.img = self.icon
	
	def handle_starttag(self, tag, attrs):
		if self.divcount is None:
			if tag == u"article":
				self.divcount = 0
			elif tag == u"a":
				for key, value in attrs:
					if key == u"rel" and value == u"next":
						self.item.add_next_page(url=self.nextUrl)
				
		elif tag == u"div" and self.divcount >= 0:
			self.divcount += 1
			if self.divcount == 2:
				for key, value in attrs:
					if key == u"class":
						if value == u"cb-thumb-contain img-ratio-md":
							self.section = 1
						elif value == u"cb-desc":
							self.section = 2
		
		elif self.divcount == 1:
			if tag == u"a":
				_rel = _href = _audio = None
				for key, value in attrs:
					if key == u"href":
						_href = value
					elif key == u"rel" and value == u"bookmark":
						_rel = True
					elif key == u"title" and value == u"Listen":
						_audio = True
				
				if _rel and _href:
					self.section = 102
					self.item.urlParams["url"] = _href
				
				elif _audio and _href:
					self.item.urlParams["audio"] = _href
			
			elif tag == u"p":
				for key, value in attrs:
					if key == u"class" and value == u"run-time":
						self.section = 103
		
		elif tag == u"img" and self.section == 1:
			for key, value in attrs:
				if key == u"data-src":
					self.img = value
					self.section = 0
		
		elif tag == u"p" and self.section == 2:
			self.section = 101
	
	def handle_data(self, data):
		if self.section == 101:
			self.item.infoLabels["plot"] = data.strip()
			self.section = 0
		elif self.section == 102:
			self.item.setLabel(data.strip())
			self.section = 0
		elif self.section == 103:
			self.item.setDuration(data.strip())
			self.section = 0
	
	def handle_endtag(self, tag):
		# Decrement div count on div end tag
		if tag == u"div" and self.divcount > 0:
			self.divcount -= 1
		
		elif tag == u"article":
			self.divcount = None
			self.item.setThumb(self.img)
			self.append(self.item.getListitemTuple(True))
			self.reset_lists()
