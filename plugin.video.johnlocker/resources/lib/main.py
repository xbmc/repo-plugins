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
		# Add Option to view most recent videos
		self.add_recent(action="MostRecent")
		
		# Fetch Categories Content
		url = "http://johnlocker.com/us/"
		with urlhandler.urlopen(url, 604800) as sourceObj: # TTL = 1 Week
			return parsers.Categories().parse(sourceObj)

class ListVideos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = plugin["url"]
		with urlhandler.urlopen(url, 14400) as sourceObj: # TTL = 4 Hours
			return parsers.VideoParser().parse(sourceObj)

class MostRecent(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = u"http://feeds.feedburner.com/johnlockerv3"
		sourceObj = urlhandler.urlopen(url, 14400) # TTL = 4 Hours
		
		# Fetch and Return VideoItems
		return self.xml_scraper(sourceObj)
	
	def xml_scraper(self, sourceObj):
		# Import XML Parser and Parse sourceObj
		import xml.etree.ElementTree as ElementTree
		tree = ElementTree.parse(sourceObj).getroot()
		sourceObj.close()
		
		# Fetch strip_tags Method
		stripTags = plugin.strip_tags
		
		# Loop thought each Video item
		localListitem = listitem.ListItem
		for node in tree[0].findall("item"):
			# Create listitem of Data
			item = localListitem()
			item.setAudioFlags()
			item.setVideoFlags(None)
			
			# Fetch Title, Category, 
			item.setLabel(node.findtext("title"))
			item.setGenre(node.findall("category")[0].text)
			
			# Fetch Plot
			plot = stripTags(node.findtext("description"))
			item.setPlot(plot[:plot.find("The post")])
			
			# Fetch Video Page url
			item.setParamDict(url=node.findtext("comments"), action="system.source")
			
			# Fetch Published Date
			date = node.findtext("pubDate")
			item.setDate(date[:date.find("+")-1], "%a, %d %b %Y %H:%M:%S")
			
			# Store Listitem data
			yield item.getListitemTuple(True)