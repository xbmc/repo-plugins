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
		# Add Youtube Channel
		self.add_youtube_videos(u"UUHBymwGdRxKPonsoD-VZ5dg")
		
		# Fetch Video Content
		url = u"http://www.quake-live.tv/data/playlist_MySQL.php?vf=&t=all&v=&s=DESC"
		sourceObj = urlhandler.urlopen(url, 14400) # TTL = 4 Hours
		
		# Fetch and Return VideoItems
		return self.xml_scraper(sourceObj)
	
	def xml_scraper(self, sourceObj):
		# Import XML Parser and Parse sourceObj
		import xml.etree.ElementTree as ElementTree
		tree = ElementTree.parse(sourceObj).getroot()
		ns = u"http://xspf.org/ns/0/"
		sourceObj.close()
		
		# Loop thought earch Show element
		localListitem = listitem.ListItem
		for node in tree.getiterator(u"{%s}track" % ns):
			# Create listitem of Data
			item = localListitem()
			item.setAudioFlags()
			item.setVideoFlags(False, aspect=1.78)
			item.setLabel(node.findtext(u"{%s}title" % ns).replace(u"\n",u""))
			item.setThumb(node.findtext(u"{%s}image" % ns))
			item.setParamDict(url=node.findtext(u"{%s}location" % ns), action="system.direct")
			
			# Add Date Info
			date = node.findtext(u"{%s}creator" % ns).replace(u"\n",u" ")
			item.setDate(date[date.rfind(u" ")+1:], "%m/%d/%y")
			
			# Store Listitem data
			yield item.getListitemTuple(True)