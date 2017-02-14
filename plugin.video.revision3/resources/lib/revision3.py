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

import kodiutils
import urllib
import os
import routing
import xbmcaddon
import xbmcvfs
import sys
import xbmc
import xbmcplugin
from xbmcgui import ListItem

ADDON = xbmcaddon.Addon() 


def build_tvshow_item(show):
	#Create listitem
	liz = ListItem(show["name"])
	#Listitem infolabels
	infolabels = { "title": show["name"], "originaltitle": show["name"] }
	if "summary" in show.keys():
		infolabels["plot"] = show["summary"]
	if "tagline" in show.keys():
		infolabels["tagline"] = show["tagline"]
	if "debut" in show.keys():
		infolabels["premiered"] = show["debut"]
	#Art
	art = {}
	if "images" in show.keys():
		images = show["images"]
		if "logo" in images.keys():
			art["icon"] = images["logo"]; art["thumb"] = images["logo"]; art["poster"] = images["logo"]
		if "promo" in images.keys():
			art["fanart"] = images["promo"]
		else:
			art["fanart"] = os.path.join( ADDON.getAddonInfo( 'path' ), 'resources', 'fanart.jpg' )
		if "banner" in images.keys():
			art["banner"] = images["banner"]

	liz.setInfo( type="Video", infoLabels=infolabels)
	liz.setArt(art)
	liz.setUniqueIDs({"revision3id":show["id"]})
	return liz

def build_episode_item(episode, show_fanart=None):
	#create episode listitem
	episode_title = episode["name"] if episode["name"] else "None"
	liz = ListItem(episode["name"])
	#infolabels
	infolabels = { "title": episode["name"] }
	if "summary" in episode.keys(): infolabels["plot"] = episode["summary"]
	if "number" in episode.keys() and episode["number"].isdigit(): infolabels["episode"] = int(episode["number"])
	if "published" in episode.keys(): 
		try: 
			infolabels["aired"] = episode['published'].rsplit('T')[0]
			infolabels["date"] = episode['published'].rsplit('T')[0].replace("-",".")
			infolabels["year"] = int(episode['published'].rsplit('T')[0].split("-")[0])
		except: xbmc.log(msg='[Revision3] could not get date information', level=xbmc.LOGERROR)
		
	if "show" in episode.keys() and "name" in episode["show"].keys(): infolabels["tvshowtitle"] = episode["show"]["name"]
	if "duration" in episode.keys() and episode["duration"].isdigit(): infolabels["duration"] = int(episode["duration"])
			
	#Art
	art = {}
	if "images" in episode.keys():
		if "medium" in episode["images"].keys():
			art["thumb"] = episode["images"]["medium"]
			art["icon"] = episode["images"]["medium"]
			art["poster"] = episode["images"]["medium"]
	if show_fanart: art["fanart"] = urllib.unquote(show_fanart)
	liz.setInfo( type="Video", infoLabels=infolabels)
	liz.setArt(art)

	#Videos
	url = ""
	if "media" in episode.keys():
		media_urls = []
		video_info = {}
		if "hd720p30" in episode["media"].keys(): media_urls.append(episode["media"]["hd720p30"]["url"])
		if "large" in episode["media"].keys(): media_urls.append(episode["media"]["large"]["url"])
		if "small" in episode["media"].keys(): media_urls.append(episode["media"]["small"]["url"])
		#Parse user preference
		if len(media_urls) > 0:
			if kodiutils.get_setting_as_int("format") == 0: url = media_urls[0]; video_info['width'] = 1280; video_info['height'] = 720
			if kodiutils.get_setting_as_int("format") == 1: url = media_urls[1] if len(media_urls) > 1 else media_urls[-1]; video_info['width'] = 854; video_info['height'] = 480
			if kodiutils.get_setting_as_int("format") == 2: url = media_urls[-1]; video_info['width'] = 854; video_info['height'] = 480
	
	#context menu items
	cm = []
	cm.append((kodiutils.get_string(32063), 'XBMC.Action(Info)'))
	

	if url:
		if kodiutils.get_setting_as_bool("download") and kodiutils.get_setting("downloadPath") and xbmcvfs.exists(kodiutils.get_setting("downloadPath")):
			cm.append((kodiutils.get_string(32062), 'XBMC.RunPlugin(plugin://%s/download/%s/%s)' % (ADDON.getAddonInfo("id"),urllib.quote(episode_title, safe=''),urllib.quote(url, safe='')) ))
		liz.setPath("plugin://%s/play/%s" % (ADDON.getAddonInfo("id"),urllib.quote(url, safe='')) )
		liz.setProperty('IsPlayable', 'true')
		liz.addStreamInfo('video', video_info)
		liz.addContextMenuItems(cm, replaceItems=False)
		return liz
	else:
		return None