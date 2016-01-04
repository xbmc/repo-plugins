#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import json
import urllib
import urllib2
import socket
import re
import xml.etree.ElementTree as ET
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import os
import traceback
from StringIO import StringIO 
import gzip 

#'Base settings'
#'Start of the plugin functionality is at the end of the file'
addon = xbmcaddon.Addon()
addonID = 'plugin.video.srf_podcast_ch'
pluginhandle = int(sys.argv[1])
socket.setdefaulttimeout(30)
translation = addon.getLocalizedString
xbmcplugin.setPluginCategory(pluginhandle,"News")
xbmcplugin.setContent(pluginhandle,"tvshows")
addon_work_folder = xbmc.translatePath("special://profile/addon_data/"+addonID)
if not os.path.isdir(addon_work_folder):
    os.mkdir(addon_work_folder)
FavoritesFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".favorites")
showSubtitles = addon.getSetting("showSubtitles") == "true"
forceViewMode = addon.getSetting("forceView") == "true"
viewModeShows = str(addon.getSetting("viewIDShows"))
numberOfEpisodesPerPage = str(addon.getSetting("numberOfShowsPerPage"))

#'this method list all SRF-channel when SRF-Podcast was selected in the main menu'
def chooseChannel():
    addChannel('srf', 'SRF', 'listTvShows')
    addChannel('rts', 'RTS', 'listTvShows')
    addChannel('rsi', 'RSI', 'listTvShows')
    addChannel('rtr', 'RTR', 'listTvShows')
    xbmcplugin.endOfDirectory(handle=pluginhandle, succeeded=True)

#'this method list all TV shows from SRF when SRF-Podcast was selected in the main menu'
def listTvShows(channel):
	url = 'http://il.srf.ch/integrationlayer/1.0/ue/' + channel + '/tv/assetGroup/editorialPlayerAlphabetical.json'
	response = json.load(open_srf_url(url))
	shows =  response["AssetGroups"]["Show"]
	title = ''
	desc = ''
	picture = ''
	page = 1
	mode = 'listEpisodes'
	for show in shows:
		try:
			title = show['title']
		except:
			title = 'No Title'
		try:
			desc = show['description']
		except:
			desc = 'No Description'
		try:
			picture = show['Image']['ImageRepresentations']['ImageRepresentation'][0]['url']
		except:
			picture = ''
		addShow(title, show['id'], mode, desc, picture,page,channel)
		
	xbmcplugin.addSortMethod(pluginhandle,1)
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode:
		xbmc.executebuiltin('Container.SetViewMode('+viewModeShows+')')

#'this method list all episodes of the selected show'
def listEpisodes(channel,showid,showbackground,page):
	url = 'http://il.srf.ch/integrationlayer/1.0/ue/' + channel + '/assetSet/listByAssetGroup/'+showid+'.json?pageNumber='+str(page)+"&pageSize="+str(numberOfEpisodesPerPage)
	response = json.load(open_srf_url(url))
	maxpage = response["AssetSets"]["@maxPageNumber"]
	show =  response["AssetSets"]["AssetSet"]
		
	for episode in show:
		title = episode['title']
		url = ''
		desc = ''
		picture = '' 
		pubdate = episode['publishedDate']
		
		try:
			desc = episode['Assets']['Video'][0]['AssetMetadatas']['AssetMetadata'][0]['description']
		except:
			desc = 'No Description'
		try:
			picture = episode['Assets']['Video'][0]['Image']['ImageRepresentations']['ImageRepresentation'][0]['url']
		except:
			# no picture
			picture = ''
		try:
			length = int(episode['Assets']['Video'][0]['duration']) / 1000 / 60
		except:
			length = 0
		try:
			url = episode['Assets']['Video'][0]['id']
		except:
			url = 'no url'
		addLink(title, url, 'playepisode', desc, picture, length, pubdate,showbackground,channel)

	# check if another page is available
	page = int(page)
	maxpage = int(maxpage)
	if page < maxpage:
		page = page + 1
		addnextpage(addon.getLocalizedString(33001), showid, 'listEpisodes', '', showbackground,page,channel)
	
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode:
		xbmc.executebuiltin('Container.SetViewMode('+viewModeShows+')')
    
	#'this method plays the selected episode'    
def playepisode(channel,episodeid):
	besturl = ''
	downloadflag = 0
	
	try:
		url = 'http://il.srf.ch/integrationlayer/1.0/ue/' + channel + '/video/play/'+episodeid+'.json'
		response = json.load(open_srf_url(url))
		urls =  response["Video"]["Playlists"]["Playlist"]["@protocol=HTTP-HDS"]["url"]
		besturl = ''
		if urls.__len__() > 1:
			for tempurl in urls:
				if tempurl['@quality'] == 'HD':
					besturl = tempurl['text']
		else:
			besturl = urls[0]['text']
		downloadflag = 1
	except:
		print "not for download"

	if downloadflag == 0:
		try:
			url = 'http://il.srf.ch/integrationlayer/1.0/ue/' + channel + '/video/play/'+episodeid+'.json'
			response = json.load(urllib2.urlopen(url))
			urls =  response["Video"]["Playlists"]['Playlist'][1]['url']
			besturl = ''
			if urls.__len__() > 1:
				for tempurl in urls:
					if tempurl['@quality'] == 'HD':
						besturl = tempurl['text']
			else:
				besturl = urls[0]['text']
			
			downloadflag = 0
		except:
			print "not for download"  
	listitem = xbmcgui.ListItem(path=besturl)
	xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

#'helper method to create a network-item in the list
def addChannel(id, name, mode):
    ok = True
    directoryurl = sys.argv[0]+"?channel="+urllib.quote_plus(id)+"&mode="+str(mode)
    liz = xbmcgui.ListItem(name)
    ok = xbmcplugin.addDirectoryItem(pluginhandle, url=directoryurl, listitem=liz, isFolder=True)
    return ok
	
#'helper method to create a folder with subitems'
def addShow(name, url, mode, desc, iconimage,page,channel):
    ok = True
    directoryurl = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&showbackground="+urllib.quote_plus(iconimage)+"&page="+str(page)+"&channel="+str(channel)
    liz = xbmcgui.ListItem(name)
    liz.setIconImage("DefaultFolder.png")
    liz.setThumbnailImage(iconimage)
    liz.setLabel2(desc)
    liz.setArt({'poster' : iconimage , 'banner' : iconimage, 'fanart' : iconimage, 'thumb' : iconimage})
    liz.setInfo(type="Video", infoLabels={"title": name, "plot": desc, "plotoutline": desc})
    xbmcplugin.setContent(pluginhandle, 'tvshows')
    ok = xbmcplugin.addDirectoryItem(pluginhandle, url=directoryurl, listitem=liz, isFolder=True)
    return ok

	#'helper method to create a folder with subitems'
def addnextpage(name, url, mode, desc, showbackground,page,channel):
	ok = True
	directoryurl = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&showbackground="+urllib.quote_plus(showbackground)+"&page="+str(page)+"&channel="+str(channel)
	liz = xbmcgui.ListItem(name)
	liz.setLabel2(desc)
	#liz.setArt({'poster' : '' , 'banner' : '', 'fanart' : showbackground, 'thumb' : ''})
	liz.setInfo(type="Video", infoLabels={"title": name, "plot": desc, "plotoutline": desc})
	xbmcplugin.setContent(pluginhandle, 'episodes')
	ok = xbmcplugin.addDirectoryItem(pluginhandle, url=directoryurl, listitem=liz, isFolder=True)
	return ok
    
#'helper method to create an item in the list'
def addLink(name, url, mode, desc, iconurl, length, pubdate, showbackground,channel):
	ok = True
	linkurl = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&channel="+str(channel)
	liz = xbmcgui.ListItem(name)
	liz.setIconImage('')
	liz.setThumbnailImage(iconurl)
	liz.setLabel2(desc)
	liz.setArt({'poster' : iconurl , 'banner' : iconurl, 'fanart' : showbackground, 'thumb' : iconurl})
	liz.setInfo(type='Video', infoLabels={"Title": name, "Duration": length, "Plot": desc, "Aired" : pubdate})
	liz.setProperty('IsPlayable', 'true')
	xbmcplugin.setContent(pluginhandle,'episodes')
	ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=linkurl, listitem=liz)
	return ok

#'helper method to retrieve parameters in a dict from the arguments given to this plugin by xbmc'
def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

def open_srf_url(urlstring):
    request = urllib2.Request(urlstring) 
    request.add_header('Accept-encoding', 'gzip') 
    response = ''
    try:
        response = urllib2.urlopen(urlstring) 
        if response.info().get('Content-Encoding') == 'gzip': 
            buf = StringIO( response.read()) 
            f = gzip.GzipFile(fileobj=buf) 
            response = f.read()
    except Exception as e:
        print traceback.format_exc()
        dialog = xbmcgui.Dialog().ok('xStream Error',str(e.__class__.__name__),str(e))
    
    return response

#'Start'
#'What to do... if nothing is given we start with the index'
params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode', '')
url = params.get('url', '')
channel = params.get('channel', '')
showbackground = urllib.unquote_plus(params.get('showbackground', ''))
page = params.get('page', '')

#mode = urllib.unquote_plus(params.get('mode', ''))
#url = urllib.unquote_plus(params.get('url', ''))
#name = urllib.unquote_plus(params.get('name', ''))

if mode == 'chooseChannel':
    chooseChannel()
elif mode == 'listTvShows':
    listTvShows(channel)
elif mode == 'listEpisodes':
    listEpisodes(channel,url,showbackground,page)
elif mode == 'playepisode':
    playepisode(channel,url)
else:
    chooseChannel() 
    