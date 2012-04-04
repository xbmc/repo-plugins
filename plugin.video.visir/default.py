# coding: utf-8
#!/usr/bin/env python

# Vísir - VefTV
# Author:  Haukur H. Þórsson (haukurhaf.net)
# Play videos from the video section at Visir.is - a local media company in Iceland.
# Inspired by the Sarpur video plugin by Dagur.
# Limitations in this version:
# - Live broadcasts from Stod2 are not supported yet.
# - The plugin does not support paging - it only loads the first 18 videos in each category.

import urllib, urllib2, re, xbmcaddon, xbmcplugin, xbmcgui, xbmc
from datetime import datetime, timedelta
from scraper import *

# Plugin constants 
__addonid__   = "plugin.video.visir"
__addon__     = xbmcaddon.Addon(id=__addonid__)
__language__  = __addon__.getLocalizedString

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
action_key = None
action_value = None
name = None

def showCategories():
	categories = getRootCategories()
	
	if isLiveStreamPlaying():
		addMenuItem(__language__(32200).encode('utf8'), 'livestream', '')
		
	for category in categories:
		addMenuItem(category["name"], 'category', category["id"])

def showCategory(category):
	categories = getSubCategories(category)
	if not categories:
		showVideos(category+',,,1')
			
	for category in categories:
		addMenuItem(category["name"], 'videos', category["id"] + ',' + category["subid"] + ',' + category["type"] + ',1')

def showVideos(category):
	videos = getVideos(category)
	if not videos:
		showDialog(__language__(32100).encode('utf8'))

	for video in videos:
		addMenuItem(video["name"], 'play', video["fileid"], video["thumbnail"])
		
	cat = category.split(',')[0]
	subcat = category.split(',')[1]
	type = category.split(',')[2]
	pageno = category.split(',')[3]		
		
	addMenuItem(__language__(32300).encode('utf8'), 'videos', cat + ',' + subcat + ',' + type + ',' + str(int(pageno)+1))

def play(file):
	file = getVideoUrl(file)
	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(file)

def playLiveStream():	
	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play('http://utsending.visir.is:1935/live/vlc.sdp/playlist.m3u8')

def getVideoUrl(fileid):
	html = fetchPage("http://m3.visir.is/sjonvarp/myndband/bara-slod?itemid=" + fileid)
	return html

def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]

	return param

def addMenuItem(name, action_key, action_value, iconimage='DefaultFolder.png'):
	is_folder = True
	if action_key == 'play' or action_key == 'livestream':
		is_folder = False
	u=sys.argv[0]+"?action_key="+urllib.quote_plus(action_key)+"&action_value="+str(action_value)+"&name="+urllib.quote_plus(name)
	liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage='')
	liz.setInfo(type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=is_folder)

def showDialog(message):
	dialog = xbmcgui.Dialog()
	dialog.ok('Vísir - VefTV', message)        
              
params=get_params()
try:
	action_key = urllib.unquote_plus(params["action_key"])
	action_value = urllib.unquote_plus(params["action_value"])
	name = urllib.unquote_plus(params["name"])
except:
	pass

if action_key is None:
	showCategories()
elif action_key == 'category':
	showCategory(action_value)
elif action_key == 'videos':
	showVideos(action_value)
elif action_key == 'play':
	play(action_value)
elif action_key == 'livestream':
	playLiveStream()
        
xbmcplugin.endOfDirectory(int(sys.argv[1]))