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
from xbmcutil import listitem, urlhandler, plugin
import parsers

class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Add Youtube and Vimeo Channels
		self.add_youtube_videos(u"UUnavGPxEijftXneFxk28srA", label=plugin.getuni(16100))
		
		# Create urlhandler and Fetch Channel Page
		if "url" in plugin: url = "http://www.earthtouchnews.com/videos/%s/" % plugin["url"]
		else: url = u"http://www.earthtouchnews.com/videos/shows/"
		with urlhandler.urlopen(url, 604800) as sourceObj: # TTL = 1 Week
			return parsers.ShowParser().parse(sourceObj)

class Cat(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch SourceCode of Site
		url = u"http://www.earthtouchnews.com/videos/shows/"
		sourceCode = urlhandler.urlread(url, 604800, stripEntity=False) # TTL = 1 Week
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode) 
	
	def regex_scraper(self, sourceCode):
		# Create Speedup vars
		import re
		localListitem = listitem.ListItem
		
		# Fetch Video Information from Page Source
		for url in re.findall('<li><a class="" href="/videos/(\S+?)/">', sourceCode):		
		# Create listitem of Data
			item = localListitem()
			item.setLabel(url.replace("-", " ").title())
			item.setParamDict(url=url)
			
			# Store Listitem data
			yield item.getListitemTuple(False)

class Videos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		with urlhandler.urlopen(plugin["url"], 14400) as sourceObj: # TTL = 4 Hours
			return parsers.EpisodeParser().parse(sourceObj)