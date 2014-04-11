"""
AUDIO DRAMAS RELATED FUNCTIONS
"""

import jw_config
import jw_common

import re
import urllib

import xbmcgui
import xbmcplugin


# List of dramas
def showDramaIndex(start):
	
	language 		= jw_config.language

	drama_index_url = jw_common.getUrl(language) 
	drama_index_url = drama_index_url + jw_config.const[language]["dramas_index"] 
	drama_index_url = drama_index_url + "?start=" + start + "&sortBy=" + jw_config.audio_sorting
	
	html 			= jw_common.loadUrl(drama_index_url) 
	
	# Grep drama titles
	regexp_dramas_titles = '"pubAdTitleBlock">([^<]+)<'
	drama_titles = re.findall(regexp_dramas_titles, html)  	
	
	# Grep drama json
	regexp_drama_json = 'class="jsDownload" data-jsonurl="([^"]+MP3[^"]+)".*'
	drama_json = re.findall(regexp_drama_json, html)

	# Grep drama  image - [^\'.]+ discards ".prd_md" duplicated images
	regexp_drama_thumb = 'data-img-size-md=\'(http://assets.jw.org/assets/[^\'.]+_md\.jpg)\''
	drama_thumb = re.findall(regexp_drama_thumb, html)

	drama_num = 0
	for drama in drama_titles:

		title = jw_common.cleanUpText(drama_titles[drama_num])

		listItem = xbmcgui.ListItem(
			label 			= title,
			thumbnailImage  = drama_thumb[drama_num]
		)	
		params = {
			"content_type"  : "audio", 
			"mode" 			: "open_drama_json",
			"json_url" 		: drama_json[drama_num] 
		}
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)	
		xbmcplugin.addDirectoryItem(
			handle		= jw_config.plugin_pid, 
			url 		= url, 
			listitem 	= listItem, 
			isFolder	= False 
		)  
		drama_num = drama_num + 1

	jw_common.setNextPageLink(html, "open_drama_index", "audio")

	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)
	jw_common.setThumbnailView()

