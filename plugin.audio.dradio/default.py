#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  Copyright 2013 escoand
#
#  This file is part of the dradio.de xbmc plugin.
#
#  This plugin is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This plugin is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this plugin.  If not, see <http://www.gnu.org/licenses/>.


from os.path import join
from sys import argv
from time import gmtime, strftime, strptime
from urllib import quote_plus, urlopen
from urlparse import parse_qs, urlparse
from xml.dom.minidom import parseString
from xbmc import translatePath
import xbmcaddon
from xbmcgui import Dialog, ListItem, lock, unlock
from xbmcplugin import addDirectoryItem, endOfDirectory

Addon = xbmcaddon.Addon("plugin.audio.dradio")

icons = {
	0: join(Addon.getAddonInfo('path'), 'icon.png'),
	1: join(Addon.getAddonInfo('path'), 'resources', 'media', 'drw.png'),
	3: join(Addon.getAddonInfo('path'), 'resources', 'media', 'drk.png'),
	4: join(Addon.getAddonInfo('path'), 'resources', 'media', 'dlf.png'),
}


def CONFIG():
	global article, playlist, sendungen, streams, themen
	
	# parse content
	dom = parseString(urlopen('http://www.dradio.de/aodflash/xml/config.xml').read())
	config = dom.getElementsByTagName('config')[0]
	hosturl = config.getElementsByTagName('hostUrl')[0].getAttribute('value')
	baseurl = config.getElementsByTagName('baseUrl')[0].getAttribute('value')
	services = config.getElementsByTagName('services')[0]
	sendungen = services.getElementsByTagName('urlListSendungen')[0].getAttribute('value')
	themen = services.getElementsByTagName('urlListThemen')[0].getAttribute('value')
	streams = config.getElementsByTagName('streamingUrls')[0]
	playlist = services.getElementsByTagName('urlPlaylist')[0].getAttribute('value')
	article = services.getElementsByTagName('urlArticleData')[0].getAttribute('value')
	
	# urls
	sendungen = (hosturl + baseurl + sendungen).replace('//', '/').replace(':/', '://')
	themen = (hosturl + baseurl + themen).replace('//', '/').replace(':/', '://')
	playlist = (hosturl + baseurl + playlist).replace('//', '/').replace(':/', '://')
	article = (hosturl + baseurl + article).replace('//', '/').replace(':/', '://')
	streams = {
		1: streams.getElementsByTagName('streamDLW')[0].getAttribute('value'),
		3: streams.getElementsByTagName('streamDLR')[0].getAttribute('value'),
		4: streams.getElementsByTagName('streamDLF')[0].getAttribute('value'),
	}


def INDEX():
	global icons
	
	# add items
	addDir(Addon.getLocalizedString(30001), icons[0], {
		'mode': 0,
		'station': 0,
	})
	addDir(Addon.getLocalizedString(30002), icons[4], {
		'mode': 0,
		'station': 4,
	})
	addDir(Addon.getLocalizedString(30003), icons[3], {
		'mode': 0,
		'station': 3,
	})
	addDir(Addon.getLocalizedString(30004), icons[1], {
		'mode': 0,
		'station': 1,
	})


def STATION():
	global mode, name, station, streams
	
	# add items
	#addDir(Addon.getLocalizedString(30101), params = {
	#	'mode': 10,
	#	'station': station,
	#})
	addDir(Addon.getLocalizedString(30102), params = {
		'mode': 20,
		'station': station,
	})
	addDir(Addon.getLocalizedString(30103), params = {
		'mode': 30,
		'station': station,
	})
	#addDir(Addon.getLocalizedString(30104), params = {
	#	'mode': 40,
	#	'station': station,
	#})
	if station > 0:
		addLink(Addon.getLocalizedString(30105), streams[station], icons[station], {
			'title': Addon.getLocalizedString(30105),
		})


def SEARCH():
	pass


def DAILYVIEW():
	global date, mode
	
	try:
		date = Dialog().numeric(1, Addon.getLocalizedString(30201)).replace(' ', '')
		date = strftime('%d.%m.%Y', strptime(date, '%d/%m/%Y'))
		mode = 90
	
		PLAYLIST()
	
	except:
		pass


def PROGRAM():
	global playlist, sendungen, station
	
	# parse content
	dom = parseString(urlopen(sendungen + '?drbm:station_id=' + str(station)).read())
	listing = dom.getElementsByTagName('broadcastings')[0]
	items = listing.getElementsByTagName('item')
	
	# add items
	for item in items:
		name = item.firstChild.data
		broadcast = item.getAttribute('id')
		addDir(name, params = {
			'mode': 90,
			'station': station,
			'broadcast': broadcast,
		})


def TOPICS():
	global playlist, station, themen
	
	# parse content
	dom = parseString(urlopen(themen + '?drbm:station_id=' + str(station)).read())
	listing = dom.getElementsByTagName('themen')[0]
	items = listing.getElementsByTagName('item')
	
	# add items
	for item in items:
		name = item.firstChild.data
		theme = item.getAttribute('id')
		addDir(name, params = {
			'mode': 90,
			'station': station,
			'theme': theme,
		})


def PLAYLIST():
	global article, broadcast, date, page, playlist, station, theme
	
	# generate url
	url = playlist + '?drau:station_id=' + str(station) + '&drau:page=' + str(page)
	if date != None:
		url = url + '&drau:from=' + str(date) + '&drau:to=' + str(date)
	if broadcast != None:
		url = url + '&drau:broadcast_id=' + str(broadcast)
	if theme != None:
		url = url + '&theme=' + str(theme)
	#print url
	
	# parse content
	dom = parseString(urlopen(url).read())
	listing = dom.getElementsByTagName('entries')[0]
	items = listing.getElementsByTagName('item')
	
	totalItems = items.length
	
	# add items
	for item in items:
		url = item.getAttribute('url')
		id = item.getElementsByTagName('article')[0].getAttribute('id')
		name = item.getElementsByTagName('title')[0].firstChild.data
		timestamp = item.getAttribute('timestamp')
		name = strftime('%d.%m. %H:%M', gmtime(int(timestamp))) + ' - ' + name
		
		# get optional data
		try:
			album = item.getElementsByTagName('sendung')[0].firstChild.data
		except:
			album = None
		try:
			artist = item.getElementsByTagName('author')[0].firstChild.data
		except:
			artist = None
		try:
			duration = item.getAttribute('duration')
		except:
			duration = None
		try:
			if id != None:
				image = parseString(urlopen(article + '?dram:article_id=' + id).read()) \
					.getElementsByTagName('article')[0].getElementsByTagName('image')[0] \
					.firstChild.data #.replace('_max_100x75_', '_max_440x330_')
			else:
				image = ''
		except:
			image = ''
		
		addLink(name, url, image, {
			'album': album,
			'artist': artist,
			'date': date,
			'duration': duration,
			'title': name,
		}, totalItems)
	
	# previous page
	if listing.getAttribute('page') and int(listing.getAttribute('page')) > 0:
		addDir(Addon.getLocalizedString(30301), params = {
			'mode': mode,
			'station': station,
			'page': int(page) - 1,
			'date': date,
			'broadcast': broadcast,
			'theme': theme,
		})
	
	# next page
	if page + 1 < int(listing.getAttribute('pages')):
		addDir(Addon.getLocalizedString(30302), params = {
			'mode': mode,
			'station': station,
			'page': int(page) + 1,
			'date': date,
			'broadcast': broadcast,
			'theme': theme,
		})


def getParam(name):
	global argv
	
	# parse parameters
	if len(argv) >= 3:
		params = parse_qs(urlparse(argv[2]).query)
		if params.has_key(name):
			return params[name][0]
	
	return None


def addDir(name, image = '', params = {}, totalItems = 0):
	name = name.encode('utf-8')
	url = argv[0] + '?'
	for key in params.keys():
		if params[key] != None:
			url = url + str(key) + '=' + str(params[key]) + '&'
	item = ListItem(name, iconImage = image, thumbnailImage = image)
	return addDirectoryItem(int(sys.argv[1]), url, item, True, totalItems)


def addLink(name, url, image = '', info = {}, totalItems = 0):
	name = name.encode('utf-8')
	item = ListItem(name, iconImage = image, thumbnailImage = image)
	item.setProperty('mimetype', 'audio/mpeg')
	item.setInfo('music', info)
	return addDirectoryItem(int(argv[1]), url, item, False, totalItems)


# get parameters
mode = getParam('mode')
if mode != None:
	mode = int(mode)
name = getParam('name')
station = getParam('station')
if station != None:
	station = int(station)
page = getParam('page')
if page != None:
	page = int(page)
else:
	page = 0
date = getParam('date')
if date != None:
	date = int(date)
broadcast = getParam('broadcast')
theme = getParam('theme')

#print mode, station, page, date, broadcast, theme


# get config
CONFIG()


# do handling
if mode == None:
	INDEX()
elif mode == 0:
	STATION()
elif mode == 10:
	SEARCH()
elif mode == 20:
	DAILYVIEW()
elif mode == 30:
	PROGRAM()
elif mode == 40:
	TOPICS()
elif mode == 90:
	PLAYLIST()


# end menu
endOfDirectory(int(argv[1]))
