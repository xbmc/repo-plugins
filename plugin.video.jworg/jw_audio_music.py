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

# List of bible books
def showMusicIndex(language, start):
	
	music_index_url = jw_config.const[language]["music_index"] + "?start=" + start
	html = jw_load.loadUrl(music_index_url) 
	
	# Grep compilation titles
	regexp_music_titles = '"pubAdTitleBlock">([^<]+)<'
	music_titles = re.findall(regexp_music_titles, html)  	

	# Grep music json
	regexp_music_json = 'class="jsDownload" data-jsonurl="([^"]+MP3[^"]+)".*'
	music_json = re.findall(regexp_music_json, html)

	for music in music_json:
		print "JWORG music json: " + music

	book_num = 0
	for book in music_titles:
		listItem = xbmcgui.ListItem( music_titles[book_num] )	
		params = {"content_type" : "audio", "mode": "open_music_json", "json_url" : music_json[book_num] }
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)	
		xbmcplugin.addDirectoryItem(handle=jw_config.pluginPid, url=url, listitem=listItem, isFolder=True )  
		book_num = book_num + 1

	# Grep video pages "NEXT" link
	regexp_video_next_page = '<a class="iconNext.*start=([0-9]+).*title="([^""]+)"'
	next_link = re.findall(regexp_video_next_page, html)

	# Output next page link
	try: 
		next_start =  next_link[0][0]
		title = jw_config.t(30001);	
		listItem = xbmcgui.ListItem(title)
		params = {"content_type" : "audio", "mode": "open_music_index", "start" : next_start } 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(handle=jw_config.pluginPid, url=url, listitem=listItem, isFolder=True )  
	except:
		pass

	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)

# Track list
def showMusicJsonUrl(language, json_url):

	print "JWORG showMusicJsonUrl "+ json_url

	json_url = "http://www.jw.org" + json_url
	json = jw_load.loadJsonFromUrl(json_url)

	language_code = jw_config.const[language]["lang_code"]
	
	for mp3 in json["files"][language_code]["MP3"]:
		url = mp3["file"]["url"]
		title = mp3["title"]

		# Skip 'zip' files
		if mp3["mimetype"] != "audio/mpeg":
			continue;

		listItem = xbmcgui.ListItem(label=title)
		listItem.setInfo(type='Audio', infoLabels={'Title': mp3["title"] })

		xbmcplugin.addDirectoryItem(
			handle=jw_config.pluginPid, 
			url=url, 
			listitem=listItem, 
			isFolder=False )  

	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)