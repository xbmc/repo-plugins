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

BASEURL = u"http://www.watchmojo.com"
class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = u"%s/video/theme/" % BASEURL
		sourceCode = urlhandler.urlread(url, 2678400) # TTL = 1 Month
		videoItems = parsers.CategorysParser().parse(sourceCode)
		
		# Add Extra Items
		icon = (plugin.getIcon(),0)
		self.add_youtube_channel("watchmojo")
		self.add_item(u"-Latest Videos", thumbnail=icon, url={"action":"Videos", "url":"/video/cat/home/1"})
		self.add_item(u"-Video Themes", thumbnail=icon, url={"action":"Themes", "url":"/video/theme/"})
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_video_title)
		self.set_content("files")
		
		# Return List of Video Listitems
		return videoItems

class Themes(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = BASEURL + plugin["url"]
		sourceCode = urlhandler.urlread(url, 604800) # TTL = 1 Week
		videoItems = parsers.ThemesParser().parse(sourceCode)
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_video_title)
		self.set_content("files")
		
		# Return List of Video Listitems
		return videoItems

class SubCat(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = u"%s/video/theme/" % BASEURL
		sourceCode = urlhandler.urlread(url, 2678400) # TTL = 1 Month
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_video_title)
		self.set_content("files")
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		results = []
		additem = results.append
		localListitem = listitem.ListItem
		import re
		
		# Add Current Category
		self.add_item(label=u"-%s" % plugin["title"], url={"action":"Videos", "url":plugin["url"]})
		
		for catID in plugin["idlist"].split(u","):
			# Create listitem of Data
			item = localListitem()
			
			# Fetch Title and Set url & action
			url = u"/video/id/%s/1" % catID
			item.setLabel(re.findall('<a href="%s">(.+?)</a>' % url, sourceCode)[0])
			item.setParamDict(action="Videos", url=url)
			
			# Store Listitem data
			additem(item.getListitemTuple(isPlayable=False))
			
		# Return list of listitems
		return results

class Videos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = BASEURL + plugin["url"].replace(u" ",u"%20")
		sourceCode = urlhandler.urlread(url, 28800) # TTL = 8 Hours
		videoItems = parsers.VideosParser().parse(sourceCode)
		
		# Set Content Properties
		self.set_sort_methods(self.sort_method_date, self.sort_method_video_title)
		self.set_content("episodes")
		
		# Return List of Video Listitems
		return videoItems

class PlayVideo(listitem.PlayMedia):
	@plugin.error_handler
	def resolve(self):
		# Create url for oembed api
		url = BASEURL + plugin["url"]
		sourceCode = urlhandler.urlread(url)
		import re
		
		# Search sourceCode
		test = re.findall("<param name=\"flashvars\" value='(.+?)'>", sourceCode)[0]
		values = plugin.get_params(test)
		if values["type"] == "rtmp": return {"url":"%s/mp4:%s" % (values["streamer"], values["file"])}
		else: return {"url":values["file"]}
