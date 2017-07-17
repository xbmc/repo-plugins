# -*- coding: utf-8 -*-
import requests
import re
import os
import sys
import routing
import logging
import xbmcaddon
from resources.lib import kodilogging
from resources.lib.kodiutils import translate
from xbmcgui import Dialog,ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory


ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()

GLOBAL_FANART = os.path.join(ADDON.getAddonInfo('path'),'resources','images','fanart.jpg')
GLOBAL_NEWSPAPPER_ICON = os.path.join(ADDON.getAddonInfo('path'),'resources','images','newspapericon.png')
BANCA_SAPO_URL = "http://24.sapo.pt/jornais"


@plugin.route('/')
def categories():
	try:
		req = requests.get(BANCA_SAPO_URL).text
	except:
		Dialog().ok(translate(32000), translate(32001))
		sys.exit(0)

	categories_regex = re.findall('<a href="/jornais/(.+?)" class="\[  \]">(.+?)</a>',req)
	for uri,category in categories_regex:
		liz = ListItem(category)
		liz.setArt({"thumb":GLOBAL_NEWSPAPPER_ICON, "fanart": GLOBAL_FANART})
		addDirectoryItem(plugin.handle, plugin.url_for(show_category, uri), liz, True)
	endOfDirectory(plugin.handle)


@plugin.route('/category/<category_id>')
def show_category(category_id):
	try:
		req = requests.get('{}/{}'.format(BANCA_SAPO_URL, category_id)).text
	except:
		Dialog().ok(translate(32000), translate(32001))
		sys.exit(0)
	match = re.findall('data-original-src="(.+?)".+?data-share-url=.+?title="(.+?)".+?source data-srcset="(.+?)" srcset', req, re.DOTALL)
	for cover, newspapper, thumb in match:
		if thumb.startswith('//'): thumb = '{}{}'.format('http:', thumb) 
		liz = ListItem(newspapper)
		liz.setArt({"thumb":thumb, "fanart": GLOBAL_FANART})
		addDirectoryItem(plugin.handle, cover, liz)
	endOfDirectory(plugin.handle)

def run():
	plugin.run()
