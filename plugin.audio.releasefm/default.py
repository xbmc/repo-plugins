#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  Copyright 2014 sorax
#
#  This file is part of the detektor.fm xbmc plugin.
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
from xbmcgui import Dialog, ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory

Addon = xbmcaddon.Addon("plugin.audio.releasefm")

icons = {
	0: join(Addon.getAddonInfo('path'), 'icon.png'),
	1: join(Addon.getAddonInfo('path'), 'resources', 'media', 'ReleaseFM.png'),

}


def CONFIG():
	global streams

	# urls
	streams = {
		1: 'http://www.releasefm.net/listen.pls',
	}


def INDEX():
	global icons, streams

	# add items
	addLink('[COLOR orange][B]Release FM[/B][/COLOR] [COLOR red] LIVE[/COLOR]', streams[1], icons[1], {
		'title': 'Release FM',
	})


def addLink(name, url, image = '', info = {}, totalItems = 0):
	name = name.encode('utf-8')
	item = ListItem(name, iconImage = image, thumbnailImage = image)
	item.setProperty('mimetype', 'audio/mpeg')
	item.setInfo('music', info)
	return addDirectoryItem(int(argv[1]), url, item, False, totalItems)


# get config
CONFIG()


# show index
INDEX()


# end menu
endOfDirectory(int(argv[1]))
