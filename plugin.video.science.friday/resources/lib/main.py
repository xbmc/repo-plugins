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

BASEURL = u"http://www.sciencefriday.com%s"
class Initialize(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		_plugin = plugin
		url = BASEURL % u"/about/about-science-friday.html"
		sourceCode = urlhandler.urlread(url, 604800) # TTL = 1 Week
		
		# Add Extra Items
		self.icon = icon = _plugin.getIcon()
		self.add_youtube_videos("UUDjGU4DP3b-eGxrsipCvoVQ")
		self.add_item(_plugin.getuni(30101), thumbnail=(icon,0), url={"action":"Recent", "url":"/video/index.html#page/full-width-list/1", "type":"video"})
		self.add_item(_plugin.getuni(30102), thumbnail=(icon,0), url={"action":"Recent", "url":"/audio/index.html#page/full-width-list/1", "type":"audio"})
		
		# Fetch and Return VideoItems
		return self.regex_scraper(sourceCode)
	
	def regex_scraper(self, sourceCode):
		# Create Speed vars
		localListitem = listitem.ListItem
		_plugin = plugin
		icon = self.icon
		import re
		
		# Deside on content type to show be default
		if _plugin.getSetting("defaultview") == u"0": # Video
			menuItem = _plugin.getuni(30103)
			localType = u"video-list"
			contextType = u"segment-list"
		
		else: # Audio
			menuItem = _plugin.getuni(30104)
			localType = u"segment-list"
			contextType = u"video-list"
		
		# Loop each topic
		for url, title in re.findall('<li><a\shref="(/topics/\S+?\.html)">(.+?)</a></li>', sourceCode):
			# Create listitem of Data For Video
			item = localListitem()
			item.setLabel(title)
			item.setThumb(icon)
			item.setParamDict(action="ContentLister", url=u"%s#page/bytopic/1" % url, type=localType)
			item.addContextMenuItem(menuItem, "XBMC.Container.Update", action="ContentLister", url=u"%s#page/bytopic/1" % url, type=contextType)
			yield item.getListitemTuple(False)

class ContentLister(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		_plugin = plugin
		# Add link to Alternitve Listing
		if _plugin["type"] == u"video-list": self.add_item(_plugin.getuni(30103), thumbnail=(_plugin.getIcon(),0), url={"action":"ContentLister", "updatelisting":"true", "url":_plugin["url"], "type":"segment-list"})
		else: self.add_item(_plugin.getuni(30104), thumbnail=(_plugin.getIcon(),0), url={"action":"ContentLister", "updatelisting":"true", "url":_plugin["url"], "type":"video-list"})
		
		# Fetch Video Content
		url = BASEURL % _plugin["url"]
		with urlhandler.urlopen(url, 14400) as sourceObj: # TTL = 4 Hours
			return parsers.VideosParser().parse(sourceObj, _plugin["type"])

class Recent(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		# Fetch Video Content
		url = BASEURL % plugin["url"]
		with urlhandler.urlopen(url, 14400) as sourceObj: # TTL = 4 Hours
			return parsers.RecentParser().parse(sourceObj)

class PlayVideo(listitem.PlaySource):
	@plugin.error_handler
	def resolve(self):
		# Create url for oembed api
		url = BASEURL % plugin["url"]
		sourceCode = urlhandler.urlread(url, 14400, stripEntity=False)# TTL = 4 Hours
		
		# Search for Internal Video Source url
		if u"video-permalink-player" in sourceCode and u"video-permalink-player" in sourceCode and (u"data-videosrc" in sourceCode or u"data-flashvideosrc" in sourceCode):
			import re
			plugin.debug("Found Internal Link")
			for part1, part2 in re.findall('data-videosrc="(\S*?)"|data-flashvideosrc="(\S*?)"', sourceCode):
				if part1: return part1
				elif part2: return part2
			return url[0]
		else:
			# Atempt to Find External Video Source
			return self.sourceParse(sourceCode)

class PlayAudio(listitem.PlayMedia):
	@plugin.error_handler
	def resolve(self):
		# Create url for oembed api
		url = BASEURL % plugin["url"]
		sourceCode = urlhandler.urlread(url, 14400, stripEntity=False)# TTL = 4 Hours
		import re
		
		# Search sourceCode for audo file
		stitcher = re.findall('<a\sclass="stitcher-ll"\shref="(http://app\.stitcher\.com\S+?)"\starget="_blank">', sourceCode)[0]
		return plugin.parse_qs(stitcher[stitcher.find(u"?")+1:])[u"url"]