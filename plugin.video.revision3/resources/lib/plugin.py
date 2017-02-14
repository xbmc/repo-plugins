# -*- coding: utf-8 -*-
'''
    plugin.video.revision3
    Copyright (C) 2017 enen92,stacked
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
'''

import routing
import xbmcaddon
import xbmcvfs
import base64
import json
import os
import sys
import urllib
import xbmc
from resources.lib import kodiutils
from downloader import Downloader
from resources.lib.generalutils import get_page
from resources.lib.revision3 import build_tvshow_item, build_episode_item
from xbmcgui import ListItem, Dialog
from xbmcplugin import setResolvedUrl, addDirectoryItem, addDirectoryItems, endOfDirectory, setContent, addSortMethod, SORT_METHOD_UNSORTED, SORT_METHOD_LABEL, SORT_METHOD_EPISODE,SORT_METHOD_VIDEO_RUNTIME

ADDON = xbmcaddon.Addon()
plugin = routing.Plugin()
dialog = Dialog()

next_thumb = os.path.join( ADDON.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
downloads_thumb = os.path.join( ADDON.getAddonInfo( 'path' ), 'resources', 'media', 'downloads.png' )
archived_thumb = os.path.join( ADDON.getAddonInfo( 'path' ), 'resources', 'media', 'archived.png' )
recent_thumb = os.path.join( ADDON.getAddonInfo( 'path' ), 'resources', 'media', 'recent.png' )
featured_thumb = os.path.join( ADDON.getAddonInfo( 'path' ), 'resources', 'media', 'featured.png' )
play_thumb = os.path.join( ADDON.getAddonInfo( 'path' ), 'resources', 'media', 'play.png' )
fanart_bg = os.path.join( ADDON.getAddonInfo( 'path' ), 'resources', 'fanart.jpg' )
revision_icon = os.path.join( ADDON.getAddonInfo( 'path' ), 'resources', 'icon.png' )
BASE = 'http://revision3.com/api/'
KEY = base64.b64decode(ADDON.getLocalizedString(32025))

@plugin.route('/')
def index():
	#Build default menu items
	#0) Downloads folder
	if kodiutils.get_setting_as_bool("download") and kodiutils.get_setting_as_bool("folder") and kodiutils.get_setting("downloadPath") and xbmcvfs.exists(kodiutils.get_setting("downloadPath")):
		liz = ListItem("["+kodiutils.get_string(32012)+"]")
		liz.setInfo( type="Video", infoLabels={"plot":kodiutils.get_string(32012)})
		liz.setArt({"thumb":downloads_thumb, "fanart": fanart_bg})
		addDirectoryItem(plugin.handle, plugin.url_for(downloads), liz, True)
	
	#1) Most Recent
	liz = ListItem("["+kodiutils.get_string(32013)+"]")
	liz.setInfo( type="Video", infoLabels={"plot":kodiutils.get_string(32013)})
	liz.setArt({"thumb":recent_thumb, "fanart": fanart_bg})
	addDirectoryItem(plugin.handle, plugin.url_for(show_episodes, urllib.quote('%sgetEpisodes%s&grouping=latest' % (BASE, KEY), safe=''), 0, urllib.quote(fanart_bg, safe='')), liz, True)
	#2) Featured
	liz = ListItem("["+kodiutils.get_string(32023)+"]")
	liz.setInfo( type="Video", infoLabels={"plot":kodiutils.get_string(32023)}) 
	liz.setArt({"thumb":featured_thumb, "fanart": fanart_bg})
	addDirectoryItem(plugin.handle, plugin.url_for(show_episodes, urllib.quote('%sgetEpisodes%s&grouping=featured' % (BASE, KEY), safe=''), 0, urllib.quote(fanart_bg, safe='')), liz, True)
	#3) Archive shows
	liz = ListItem("["+kodiutils.get_string(32014)+"]")
	liz.setInfo( type="Video", infoLabels={"plot":kodiutils.get_string(32014)})
	liz.setArt({"thumb":archived_thumb, "fanart": fanart_bg})
	addDirectoryItem(plugin.handle, plugin.url_for(list_shows, urllib.quote("%sgetShows%s&grouping=archived" % (BASE,KEY), safe='')), liz, True)
	#List shows 
	list_shows(urllib.quote("%sgetShows%s" % (BASE,KEY), safe=''))
 

@plugin.route('/shows/<url>')
def list_shows(url):
	items = []
	url=urllib.unquote(url)
	data = get_page(url)
	if data["content"]:
		content = json.loads(data["content"])
		for show in content["shows"]:
			liz = build_tvshow_item(show)
			items.append((plugin.url_for(show_episodes, urllib.quote('%sgetEpisodes%s&show_id=%s' % (BASE, KEY, liz.getUniqueID("revision3id")), safe=''), 0,  urllib.quote(liz.getArt("fanart"), safe='') ), liz, True))

	if items:
		totalItems = len(items)
		addDirectoryItems(plugin.handle, items, totalItems=totalItems)
		for method in [SORT_METHOD_UNSORTED,SORT_METHOD_LABEL]:
			addSortMethod(plugin.handle, sortMethod=method ) 		
		setContent(plugin.handle, 'tvshows')
	endOfDirectory(plugin.handle)


@plugin.route('/show/<url>/<offset>/<show_fanart>')
def show_episodes(url,offset,show_fanart):
	items = []
	url = urllib.unquote(url)
	url_offset = url+'&offset='+str(offset)
	data = get_page(url_offset)
	total = 0

	if data["content"]:
		content = json.loads(data["content"])
		if "total" in content.keys(): total = content["total"]
		for episode in content["episodes"]:
			liz = build_episode_item(episode,show_fanart)
			if liz:
				items.append((liz.getPath(), liz, False))
	if items:
		totalItems = len(items)
		addDirectoryItems(plugin.handle, items, totalItems=totalItems)
		
		#sort methods
		for method in [SORT_METHOD_UNSORTED,SORT_METHOD_LABEL,SORT_METHOD_EPISODE,SORT_METHOD_VIDEO_RUNTIME]:
			addSortMethod(plugin.handle, sortMethod=method ) 
		
		#next page
		if total and (int(total) - ((int(offset) + 1) * 25)) > 0:
			liz = ListItem(kodiutils.get_string(32016) + " (" + str(int(offset)+2) + ")")
			liz.setInfo( type="Video", infoLabels={"plot":kodiutils.get_string(32016)})
			liz.setArt({"thumb":next_thumb, "fanart": fanart_bg})
			addDirectoryItem(plugin.handle, plugin.url_for(show_episodes, urllib.quote(url, safe=''), int(offset)+1,  urllib.quote(show_fanart, safe='')), liz, True)

		setContent(plugin.handle, 'episodes')
	endOfDirectory(plugin.handle)


@plugin.route('/play/<stream>')
def play(stream):
	stream = urllib.unquote(stream)
	liz = ListItem()
	liz.setPath(stream)
	setResolvedUrl(plugin.handle,True,liz)


@plugin.route('/download/<name>/<url>')
def download(name,url):
	file_name = urllib.unquote(name)
	file_url = urllib.unquote(url)
	dst_file = file_name + "." + file_url.split("/")[-1].split(".")[-1]
	#Download file
	downloader = Downloader()
	downloader.downloadall(os.path.join(kodiutils.get_setting("downloadPath"),dst_file),file_url,file_name)


@plugin.route('/downloads')
def downloads():
	if kodiutils.get_setting_as_bool("folder") and kodiutils.get_setting("downloadPath") and xbmcvfs.exists(kodiutils.get_setting("downloadPath")):
		dirs, files = xbmcvfs.listdir(kodiutils.get_setting("downloadPath"))
		if files:
			items = []
			for file_ in files:
				cm = []
				liz = ListItem(file_.split(".")[0])
				liz.setPath(os.path.join(kodiutils.get_setting("downloadPath"),file_))
				liz.setProperty('IsPlayable', 'true')
				cm.append((kodiutils.get_string(32055), 'XBMC.RunPlugin(plugin://%s/delete_file/%s)' % (ADDON.getAddonInfo("id"),urllib.quote(os.path.join(kodiutils.get_setting("downloadPath"),file_), safe='')) ))
				liz.addContextMenuItems(cm, replaceItems=False)
				items.append((liz.getPath(), liz, False))
			if items:
				addDirectoryItems(plugin.handle, items, totalItems=len(items))
	endOfDirectory(plugin.handle)

@plugin.route('/delete_file/<file_>')
def delete_file(file_):
	file_ = urllib.unquote(file_) 
	#check if the file is in the download folder
	if xbmcvfs.exists(os.path.join(kodiutils.get_setting("downloadPath"),file_.split("/")[-1])):
		xbmcvfs.delete(file_)
		dialog.notification(kodiutils.get_string(32058),kodiutils.get_string(32056),icon=revision_icon)
		xbmc.executebuiltin("Container.Refresh")
	else:
		dialog.notification(kodiutils.get_string(32058),kodiutils.get_string(32057),icon=revision_icon)


def run():
    plugin.run()