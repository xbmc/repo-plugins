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
import parsers

BASEURL = u"http://www.toonjet.com/%s"
class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = BASEURL % "about/"
		sourceObj = urlhandler.urlopen(url, 604800) # TTL = 1 Week
		videoItems = parsers.CartoonsParser().parse(sourceObj)
		sourceObj.close()
		
		# Add Extra Items
		icon = (plugin.getIcon(),0)
		self.add_youtube_channel("ToonJetOfficial", hasPlaylist=False, hasHD=False)
		self.add_item(u"-%s" % plugin.getuni(30101), thumbnail=icon, url={"action":"Featured", "url":"featured.php?sortby=views&order=DESC&count=64"})
		self.add_item(u"-%s" % plugin.getuni(30102), thumbnail=icon, url={"action":"Featured", "url":"featured.php?sortby=rated&order=DESC&count=64"})
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_video_title)
		self.set_content("files")
		
		# Return List of Video Listitems
		return videoItems

class Cartoons(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = BASEURL % plugin["url"]
		sourceObj = urlhandler.urlopen(url, 14400) # TTL = 4 Hours
		videoItems = parsers.VideoParser().parse(sourceObj)
		sourceObj.close()
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_video_title)
		self.set_content("episodes")
		
		# Return List of Video Listitems
		return videoItems

class Featured(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = BASEURL % plugin["url"]
		sourceObj = urlhandler.urlopen(url, 14400) # TTL = 4 Hours
		videoItems = parsers.FeaturedParser().parse(sourceObj)
		sourceObj.close()
		
		# Set Content Properties
		if "sortby=views" in plugin["url"]: self.set_sort_methods(self.sort_method_program_count, self.sort_method_unsorted)
		else: self.set_sort_methods(self.sort_method_unsorted)
		self.set_content("episodes")
		
		# Return List of Video Listitems
		return videoItems