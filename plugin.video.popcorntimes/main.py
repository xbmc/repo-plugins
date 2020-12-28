# Video plugin for popcorntimes.tv
# Copyright (C) 2020  dh4rry
# Copyright (C) 2020  V10lator
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import base64, codecs
import requests
from bs4 import BeautifulSoup
import requests.sessions
import re
import xbmcgui
import xbmcaddon
import xbmc
from xbmcgui import ListItem
import xbmcplugin
from xbmcplugin import addDirectoryItem, endOfDirectory
try:
	from urllib import urlencode
	from urlparse import parse_qsl
except:
	from urllib.parse import urlencode, parse_qsl

# Plugin Info
ADDON_ID      = 'plugin.video.popcorntimes'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME    = REAL_SETTINGS.getAddonInfo('name')
SETTINGS_LOC  = REAL_SETTINGS.getAddonInfo('profile')
ADDON_PATH    = REAL_SETTINGS.getAddonInfo('path')
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
ICON          = REAL_SETTINGS.getAddonInfo('icon')
FANART        = REAL_SETTINGS.getAddonInfo('fanart')
LANGUAGE      = REAL_SETTINGS.getLocalizedString

_url = sys.argv[0]
_handle = int(sys.argv[1])

s = requests.Session()
base_url = "https://popcorntimes.tv"

def getStream(siteUrl):
	site = s.get(siteUrl)
	match = re.findall(r"PCTMLOC = \"(.*)\"", site.text)
	if len(match) < 1:
		dialog = xbmcgui.Dialog()
		soup = BeautifulSoup(site.text, "html.parser")
		sorry = soup.find('h3', text='Es tut uns leid...' )
		if sorry is None:
			dialog.notification(LANGUAGE(30000), LANGUAGE(30001), xbmcgui.NOTIFICATION_ERROR, 5000)	
		else:
			dialog.notification(LANGUAGE(30002), LANGUAGE(30003), xbmcgui.NOTIFICATION_WARNING, 5000)

	else:
		encoded = match[0]
		xbmc.log("encoded:" + encoded, level=xbmc.LOGINFO)
		return "https:" + base64.b64decode(codecs.decode(encoded, 'rot13')).decode("utf-8")


def root():
	listItem = ListItem(LANGUAGE(30004))
	listItem.setProperty('IsPlayable', 'false')
	listItem.setArt({'thumb':ICON,'fanart':FANART})
	addDirectoryItem(_handle, get_url(action='listing', url="/de/top-filme"), listItem, True)
	listItem = ListItem(LANGUAGE(30005))
	listItem.setProperty('IsPlayable', 'false')
	listItem.setArt({'thumb':ICON,'fanart':FANART})
	addDirectoryItem(_handle, get_url(action='listing', url="/de/neu"), listItem, True)
	listItem = ListItem(LANGUAGE(30006))
	listItem.setProperty('IsPlayable', 'false')
	listItem.setArt({'thumb':ICON,'fanart':FANART})
	addDirectoryItem(_handle, get_url(action='genre'), listItem, True)
	endOfDirectory(_handle)


def list_genre():
	req = s.get(base_url + "/de/genres")
	soup = BeautifulSoup(req.text, "html.parser")
	genres_h3 = soup.find("div", class_ = "pt-bordered-tiles").find_all("div", class_ = "pt-movie-tile")
	for h3 in genres_h3:
		link = h3.find("a")
		img = h3.find("img")
		listItem = ListItem(img['alt'])
		listItem.setProperty('IsPlayable', 'false')
		img = img['data-src']
		if img is None:
			img = ICON
		else:
			img = "https:" + img

		listItem.setArt({'thumb':ICON,'fanart':FANART,'poster':img})
		addDirectoryItem(_handle, get_url(action='listing', url=link.get("href")), listItem, True)

	endOfDirectory(_handle)


def list_movies(url):
	xbmcplugin.setContent(_handle, 'Movies')
	req = s.get(base_url + url)
	soup = BeautifulSoup(req.text, "html.parser")
	mov_divs = soup.find_all("div", class_ = "pt-movie-tile-full")
	for div in mov_divs:
		if div.find("a") is not None:
			img = div.find("a").find("img")
			title = img["alt"]

			if div.find("p", class_ = "pt-tile-desc") is not None:
				plot = div.find("p", class_ = "pt-tile-desc").text
			if div.find("p", attrs={'class': None}) is not None:
				plot = div.find("p", attrs={'class': None}).text

			pt_time = div.find("p", class_ = "pt-video-time")
			if pt_time is not None:
				year = pt_time.text.split('|',1)[0].strip()
				duration = pt_time.find("span").text.split(' ',1)[0].strip()
			try:
				year = int(year)
			except:
				year = None
			try:
				duration = int(duration) * 60
			except:
				duration = None
			img = div.find("a").find("img").get("data-src")
			if img is None:
				img = div.find("a").find("img").get("src")

			listItem = ListItem(title)
			listItem.setProperty('IsPlayable', 'true')
			listItem.setArt({ 'fanart':FANART,'poster': "https:" + img }),
			listItem.setInfo('video', {'title': title, 'plot': plot, 'year': year, 'duration': duration })
			mov_url = base_url + div.find("a").get("href")
			addDirectoryItem(_handle, get_url(action='play', url=mov_url), listItem, False)

	endOfDirectory(_handle)
	xbmcplugin.setContent(_handle, 'Movies')


def play(movie_url):
	title = movie_url
	liz = xbmcgui.ListItem( '')
	streamUrl = getStream(movie_url)
	if streamUrl: 
		fullurl = streamUrl.strip() + "|Referer=" + movie_url.strip()
		liz.setPath(fullurl)
		xbmcplugin.setResolvedUrl(_handle, True, liz)
	#else:
		#xbmcplugin.setResolvedUrl(_handle, False, liz)


def get_url(**kwargs):
	"""
	Create a URL for calling the plugin recursively from the given set of keyword arguments.
	:param kwargs: "argument=value" pairs
	:type kwargs: dict
	:return: plugin call URL
	:rtype: str
	"""
	return '{0}?{1}'.format(_url, urlencode(kwargs))


if __name__ == '__main__':
	# Parse a URL-encoded paramstring to the dictionary of
	# {<parameter>: <value>} elements
	paramstring = sys.argv[2][1:]
	params = dict(parse_qsl(paramstring))
	# Check the parameters passed to the plugin
	if params:
		if params['action'] == 'listing':
			# Display the list of videos in a provided category.
			list_movies(params['url'])
		elif params['action'] == 'play':
			# Play a video from a provided URL.
			play(params['url'])
		elif params['action'] == 'genre':
			list_genre()
		else:
			raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
	else:
		root()
