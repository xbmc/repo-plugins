"""
	Copyright: (c) 2016 William Forde (willforde+kodi@gmail.com)
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
		_plugin = plugin
		# Add Extra Items
		icon = _plugin.getIcon()
		self.add_youtube_videos("UUDjGU4DP3b-eGxrsipCvoVQ")
		
		# Fetch Video Content
		url = BASEURL % "/explore/"
		with urlhandler.urlopen(url, 604800) as sourceObj: # :TTL = 1 Week
			return parsers.TopicsParser().parse(sourceObj)

class ContentLister(listitem.VirtualFS):
	@plugin.error_handler
	def scraper(self):
		_plugin = plugin
		if not "nextpagecount" in _plugin:
			# Add link to Alternitve Listing
			_url = _plugin.copy()
			_plugin["nextpagecount"] = 1
			_url["updatelisting"] = "true"
			_url["type"] = "segment" if _url["type"] == "video" else "video"
			if "topic" in _plugin:
				if _url["type"] == "video": self.add_item(_plugin.getuni(30104), thumbnail=(_plugin.getIcon(),0), url=_url)
				else: self.add_item(_plugin.getuni(30103), thumbnail=(_plugin.getIcon(),0), url=_url)
		
		# Fetch Video Content
		url = (BASEURL % "/wp-admin/admin-ajax.php?action=get_results&paged=%(nextpagecount)s&sfid=%(sfid)s&post_types=%(type)s") % _plugin
		if "topic" in _plugin: url += "&_sft_topic=%s" % _plugin["topic"]
		with urlhandler.urlopen(url, 14400) as sourceObj: # TTL = 4 Hours
			return parsers.ContentParser().parse(sourceObj)

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
		return plugin["audio"]