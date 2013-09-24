"""
AUDIO BIBLE RELATED FUNCTION
"""
import xbmc
import xbmcgui
import xbmcplugin

import urllib
import re

import jw_config
import jw_load

# List of available audio services
def showAudioTypeIndex():
	
	# 1. Books of the bible
	listItem = xbmcgui.ListItem( jw_config.t(30010) )	
	params = {"content_type" : "audio", "mode": "open_bible_index"} 
	url = jw_config.plugin_name + '?' + urllib.urlencode(params)
	xbmcplugin.addDirectoryItem(handle=jw_config.pluginPid, url=url, listitem=listItem, isFolder=True )  
	
	# 2. Music and  songs
	listItem = xbmcgui.ListItem( jw_config.t(30011) )	
	params = {"content_type" : "audio", "mode": "open_music_index", "start" : 0} 
	url = jw_config.plugin_name + '?' + urllib.urlencode(params)
	xbmcplugin.addDirectoryItem(handle=jw_config.pluginPid, url=url, listitem=listItem, isFolder=True )  
	
	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)
	
# List of bible books
def showAudioBibleIndex(language):
	
	bible_index_url = jw_config.const[language]["bible_index_audio"]
	html = jw_load.loadUrl(bible_index_url) 
	
	# Grep book names
	regexp_book_names = '<a>([^<]+)</a>'
	book_names = re.findall(regexp_book_names, html)  	

	book_num = 0
	for book in book_names:
		book_num = book_num + 1
		listItem = xbmcgui.ListItem( book_names[book_num -1] )	
		params = {"content_type" : "audio", "mode": "open_bible_book_index",
					"book_num" : book_num} 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)	
		xbmcplugin.addDirectoryItem(handle=jw_config.pluginPid, url=url, listitem=listItem, isFolder=True )  

	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)

# List of chapter of a specific book, playable
def showAudioBibleBookJson(language, book_num):
	print "JWORG: audio bible book num: " + book_num
	json_url = jw_config.const[language]["bible_audio_json"] + "&booknum=" + book_num
	json = jw_load.loadJsonFromUrl(json_url)
	lang_code = jw_config.const[language]["lang_code"]

	for mp3 in json["files"][lang_code]["MP3"]:

		# Skip 'zip' files
		if mp3["mimetype"] != "audio/mpeg":
			continue;

		url = mp3["file"]["url"]
		title = mp3["title"]

		listItem = xbmcgui.ListItem(label=title)
		listItem.setInfo(type='Video', infoLabels={'Title': title })

		xbmcplugin.addDirectoryItem(
			handle=jw_config.pluginPid, 
			url=url, 
			listitem=listItem, 
			isFolder=False )  

	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)
