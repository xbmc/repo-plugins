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

class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = u"http://enemyterritory.sectornetwork.com/data/playlist_MySQL.php?t=all&v=all&s=DESC&289"
		sourceObj = urlhandler.urlopen(url, 14400) # TTL = 4 Hours
		
		# Fetch and Return VideoItems
		return self.xml_scraper(sourceObj)
	
	def xml_scraper(self, sourceObj):
		# Import XML Parser and Parse sourceObj
		import xml.etree.ElementTree as ElementTree
		tree = ElementTree.parse(sourceObj).getroot()
		ns = "http://xspf.org/ns/0/"
		sourceObj.close()
		
		# Loop thought earch Show element
		localListitem = listitem.ListItem
		for node in tree.getiterator("{%s}track" % ns):
			# Create listitem of Data
			item = localListitem()
			item.setAudioFlags()
			item.setVideoFlags(False)
			item.setLabel(node.findtext("{%s}title" % ns))
			item.setThumb(node.findtext("{%s}image" % ns))
			item.setParamDict(url=node.findtext("{%s}location" % ns), action="system.direct")
			
			# Add Date Info
			date = node.findtext("{%s}creator" % ns).replace("\n"," ")
			item.setDate(date[date.rfind(" ")+1:], "%m/%d/%Y")
			
			# Store Listitem data
			yield item.getListitemTuple(True)