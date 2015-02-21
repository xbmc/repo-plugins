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

BASEURL = u"http://www.awntv.com%s"
class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Add Extra Items
		_plugin = plugin
		_add_item = self.add_item
		icon = (plugin.getIcon(),0)
		_add_item(_plugin.getuni(32941), thumbnail=icon, url={"action":"Videos", "url":"/videos/latest"})
		_add_item(_plugin.getuni(30101), thumbnail=icon, url={"action":"Videos", "url":"/videos"})
		_add_item(_plugin.getuni(136), thumbnail=icon, url={"action":"Playlists", "url":"/playlists"})
		_add_item(u"%s FMX" % _plugin.getuni(19029), thumbnail=icon, url={"action":"PlaylistVids", "url":"/channels/fmx"})
		_add_item(u"%s VFS" % _plugin.getuni(19029), thumbnail=icon, url={"action":"PlaylistVids", "url":"/channels/vfs"})
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch Video Content
		with urlhandler.urlopen("http://www.awntv.com/categories/", 604800) as sourceObj: # TTL = 1 Week
			return parsers.Categories().parse(sourceObj)

class Videos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch Video Content
		url = BASEURL % plugin["url"]
		with urlhandler.urlopen(url, 14400) as sourceObj: # TTL = 4 Hours
			return parsers.VideosParser().parse(sourceObj)

class Playlists(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch Video Content
		url = BASEURL % plugin["url"]
		with urlhandler.urlopen(url, 604800) as sourceObj: # TTL = 1 Week
			return parsers.PlaylistsParser().parse(sourceObj)

class PlaylistVids(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Set Content Properties
		self.set_sort_methods(self.sort_method_unsorted)
		
		# Fetch Video Content
		url = BASEURL % plugin["url"]
		with urlhandler.urlopen(url, 14400) as sourceObj:# TTL = 4 Hours
			return parsers.PlaylistVidParser().parse(sourceObj)

class PlayVideo(listitem.PlaySource):
	@plugin.error_handler
	def resolve(self):
		# Create url for oembed api
		url = BASEURL % plugin["url"]
		sourceCode = urlhandler.urlread(url, 14400, stripEntity=False)# TTL = 4 Hours
		import re
		
		# Fetch jQuery data to check if video is internel or external
		jQueryData = re.findall('jQuery\.extend\(Drupal\.settings,\s+({.+?})\);', sourceCode)
		if jQueryData:
			import fastjson as json
			jsonData = json.loads(jQueryData[0])
			
			# Check for Internel Player
			if u"flowplayer" in jsonData:
				videoUrl = jsonData[u"flowplayer"][u"#native-player"][u"clip"][u"url"]
				return videoUrl
		
		# Atempt to Find External Video Source
		return self.sourceParse(sourceCode)
