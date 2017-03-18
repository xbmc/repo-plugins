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
	def parse(self, urlobject, encoding="utf8", showmode=False):
		return self.fromstring(urlobject.read(), encoding, showmode)
	
	def fromstring(self, html, encoding="utf8", showmode=False):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		self.section = 0
		self.mode_value = "owl-demo5" if showmode else "owl-demo4"
		
		# Proceed with parsing
		self.reset_lists()
		self.results = []
		try:
			if encoding: self.feed(html.decode(encoding))
			else: self.feed(html)
		except EOFError:
			pass
		
		# Return Results
		return self.results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "Videos"
	
	def handle_starttag(self, tag, attrs):
		# Convert Attributes to a Dictionary
		if not attrs: return

		if self.section == 0:
			if tag == "div":
				for key, value in attrs:
					if key == u"id" and value == self.mode_value:
						self.section = 1
						break

		else:
			if tag == "div":
				self.section += 1

			elif self.section == 2:
				if tag == "a":
					for key, value in attrs:
						if key == u"href":
							url = value
							if "www.watchmojo.com" in url:
								url = url[url.find("www.watchmojo.com")+17:]
							self.item.urlParams["url"] = url

							title = url[url.rfind("/") + 1:].title()
							if self.mode_value == "owl-demo5" and title.startswith("Wm"):
								title = "WM %s" % title[2:].title()
							self.item.setLabel(title)
							break

				elif tag == "img":
					for key, value in attrs:
						if key == u"src":
							self.item.setThumb(BaseURL % value)
							break
	
	def handle_endtag(self, tag):
		# Search for each end tag
		if tag == u"div" and self.section >= 1:
			self.section -= 1
			if self.section == 1:
				self.results.append(self.item.getListitemTuple())
				self.reset_lists()
			elif self.section == 0:
				raise EOFError


class VideosParser(HTMLParser.HTMLParser):
	"""
	Parses channel categorys, i.e http://www.watchmojo.com/video/id/11529/
	"""
	def parse(self, urlobject, encoding="utf8", related_mode=False):
		return self.fromstring(urlobject.read(), encoding, related_mode)
	
	def fromstring(self, html, encoding="utf8", related_mode=False):
		""" Parses SourceCode and Scrape Categorys """
		
		# Class Vars
		self.section = 0
		self.data_section = ""
		self.relatd_mode = related_mode
		
		# Proceed with parsing
		self.reset_lists()
		self.results = []
		try:
			if encoding: self.feed(html.decode(encoding).replace(u'_blank"',u''))
			else: self.feed(html.replace(u'_blank"',u''))
		except EOFError:
			pass
		
		# Return Results
		return self.results
	
	def reset_lists(self):
		# Reset List for Next Run
		self.item = listitem.ListItem()
		self.item.urlParams["action"] = "PlayVideo"
		self.item.setVideoFlags(False)
		self.item.setAudioFlags()
	
	def handle_starttag(self, tag, attrs):
		if not attrs:
			return

		if self.section == 0:
			if self.relatd_mode and tag == "section":
				for key, value in attrs:
					if key == u"class" and value == "darkgrey darkrelated":
						self.section = 1
						break

			elif not self.relatd_mode and tag == "div":
				for key, value in attrs:
					if key == u"class" and value == "line mainline":
						self.section = 1
						break

		elif self.section == 1:
			if tag == "div":
				for key, value in attrs:
					if key == u"class":
						if value == "item":
							self.section = 2
							break
						elif value == "cat-next":
							self.data_section = "next"

			elif tag == "a" and self.data_section == "next":
				for key, value in attrs:
					if key == u"href":
						self.item.add_next_page({"url": value})
						raise EOFError

		elif self.section >= 2:
			if tag == "div":
				self.section += 1

				for key, value in attrs:
					if key == "class":
						if value == "hptitle" or value == "hpdate":
							self.data_section = value

			elif tag == "a":
				for key, value in attrs:
					if key == "href":
						url = value[:-1]
						videoid = url[url.rfind("/") + 1:]

						if not self.relatd_mode:
							self.item.addRelatedContext(videoid=videoid, action="Videos", related="true")

						self.item.urlParams["videoid"] = videoid
						break

			if tag == "img":
				_src = _alt = _play = None
				for key, value in attrs:
					if key == "src":
						_src = value

					elif key == "alt":
						_alt = True

					elif key == "class" and value == "hpplay":
						_play = True

				if _src and _alt is True:
					if not _src.startswith("http"):
						_src = BaseURL % _src
					self.item.setThumb(_src.replace(" ", "%20"))

				elif _play is True:
					self.data_section = "time"

	def handle_data(self, data):
		if self.data_section == "hptitle":
			self.data_section = ""
			title = data.strip()
			self.item.setLabel(title)

		elif self.data_section == "hpdate":
			self.data_section = ""
			data = data.strip()

			# Calculate date format
			date_fragment = data.split(" ")[0]
			if len(date_fragment) == 3 and not date_fragment.lower() == "may":
				date_format = "%b %d, %Y"
			else:
				date_format = "%B %d, %Y"

			self.item.setDate(data, date_format)

		elif self.data_section == "time":
			self.data_section = ""
			data = data.strip()
			if data:
				data = data.replace(";", ":").replace("!", "")
				data = ":".join(data.split(":")[:2])
				self.item.setDuration(data)

	def handle_endtag(self, tag):
		# Search for each end tag
		if tag == u"div" and self.section >= 2:
			self.section -= 1
			if self.section == 1:
				self.results.append(self.item.getListitemTuple(True))
				self.reset_lists()
		elif tag == u"section" and self.section >= 1 and self.relatd_mode is True:
			raise EOFError
