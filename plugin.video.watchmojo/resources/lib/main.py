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

BASEURL = u"http://www.watchmojo.com"
class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Add Extra Items
		_plugin = plugin
		icon = (_plugin.getIcon(),0)
		self.add_youtube_videos("UUaWd5_7JhbQBe4dknZhsHJg")
		self.add_item(_plugin.getuni(32941), thumbnail=icon, url={"action":"Videos", "url":"/videos/1"})
		self.add_item(_plugin.getuni(30102), thumbnail=icon, url={"action":"Videos", "url":"/msmojo/"})
		self.add_item(_plugin.getuni(30101), thumbnail=icon, url={"action":"Shows"})

		# Fetch Video Content
		with urlhandler.urlopen(BASEURL, 604800) as sourceObj: # TTL = 1 Week
			return parsers.CategorysParser().parse(sourceObj)


class Shows(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		with urlhandler.urlopen(BASEURL, 14400) as sourceObj: # TTL = 4 Hours
			return parsers.CategorysParser().parse(sourceObj, showmode=True)


class Videos(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		if "videoid" in plugin:
			url = "http://www.watchmojo.com/video/id/%s/" % plugin["videoid"]
		else:
			url = BASEURL + plugin["url"].replace(u" ",u"%20")

		with urlhandler.urlopen(url, 14400) as sourceObj: # TTL = 4 Hours
			return parsers.VideosParser().parse(sourceObj, related_mode=True if "related" in plugin else False)


class PlayVideo(listitem.PlaySource):
	@plugin.error_handler
	def resolve(self):
		# Create url for oembed api
		url = "http://www.watchmojo.com/video/id/%s/" % plugin["videoid"]
		sourceCode = urlhandler.urlread(url, 14400, stripEntity=False)# TTL = 4 Hours
		import re

		# Search sourceCode for old style player
		search_str = '<source\s*src=["\'](.+?\.mp4)["\']\s+type=["\']video/mp4["\']\s*/>'
		videos = re.findall(search_str, sourceCode)
		if videos:
			return videos[0]

		# Attempt to find the video url using the videoResolver
		sources = self.videoResolver.VideoParser()
		sources.parse(sourceCode)
		return self.intResolver(sources.get_processed())
