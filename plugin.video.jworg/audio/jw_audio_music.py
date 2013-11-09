"""
AUDIO BIBLE RELATED FUNCTIONSS
"""
import xbmcgui
import xbmcplugin

import urllib
import re

import jw_config
import jw_common

# List of albums
def showMusicIndex(start):
	
	language 		= jw_config.language

	music_index_url = jw_common.getUrl(language)
	music_index_url = music_index_url + jw_config.const[language]["music_index"]
	music_index_url = music_index_url + "?start=" + start + "&sortBy=" + jw_config.audio_sorting
	
	html 			= jw_common.loadUrl(music_index_url) 
	
	# Grep compilation titles
	regexp_music_title = '"pubAdTitleBlock">([^<]+)<'
	music_title = re.findall(regexp_music_title, html)  	

	# Grep music json
	regexp_music_json = 'class="jsDownload" data-jsonurl="([^"]+MP3[^"]+)".*'
	music_json = re.findall(regexp_music_json, html)

	# Grep compilation image - [A-Z]+ discards ".prd_md" duplicated images
	regexp_music_thumb = 'data-img-size-md=["\']([^"\']+[A-Z]+_md\.jpg)["\']'
	music_thumb = re.findall(regexp_music_thumb, html)

	album_num = 0
	for album in music_title:
		listItem = xbmcgui.ListItem(
			label 			= music_title[album_num], 
			thumbnailImage  = music_thumb[album_num]
		)	
		params = {
			"content_type"  : "audio", 
			"mode" 			: "open_music_json", 
			"json_url" 		: music_json[album_num] 
		}
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)	
		xbmcplugin.addDirectoryItem(
			handle		= jw_config.plugin_pid, 
			url 		= url, 
			listitem 	= listItem, 
			isFolder	= True 
		)  
		album_num = album_num + 1

	jw_common.setNextPageLink(html, "open_music_index", "audio")

	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)
	jw_common.setThumbnailView()


