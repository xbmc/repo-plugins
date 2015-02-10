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
from xbmcutil import listitem, urlhandler, plugin

class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = u"http://enemyterritory.sectornetwork.com/data/playlist_MySQL.php?t=all&v=all&s=DESC&289"
		sourceObj = urlhandler.urlopen(url, 14400) # TTL = 4 Hours
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_date, self.sort_method_video_title)
		self.set_content("episodes")
		
		# Fetch and Return VideoItems
		return self.xml_scraper(sourceObj)
	
	def xml_scraper(self, sourceObj):
		# Create Speed vars
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		
		# Import XML Parser and Parse sourceObj
		import xml.etree.ElementTree as ElementTree
		tree = ElementTree.parse(sourceObj).getroot()
		ns = "http://xspf.org/ns/0/"
		sourceObj.close()
		
		# Loop thought earch Show element
		for node in tree.getiterator("{%s}track" % ns):
			# Create listitem of Data
			item = localListitem()
			item.setAudioInfo()
			item.setQualityIcon(False)
			item.setLabel(node.findtext("{%s}title" % ns))
			item.setThumbnailImage(node.findtext("{%s}image" % ns))
			item.setParamDict(url=node.findtext("{%s}location" % ns), action="system.direct")
			
			# Add Date Info
			date = node.findtext("{%s}creator" % ns).replace("\n"," ")
			item.setDateInfo(date[date.rfind(" ")+1:], "%m/%d/%Y")
			
			# Store Listitem data
			additem(item.getListitemTuple(True))
		
		# Return list of listitems
		return results