"""
DRAMATICA BIBLE READING RELATED FUNCTIONS
"""
import jw_config
import jw_common

from BeautifulSoup import BeautifulSoup 
import re
import urllib

import xbmcplugin
import xbmcgui


# List of reading
def showDramaticReadingIndex(start):
	
	language 			= jw_config.language

	reading_index_url   = jw_common.getUrl(language)
	reading_index_url 	= reading_index_url + jw_config.const[language]["dramatic_reading_index"] 
	reading_index_url 	= reading_index_url + "?start=" + start  + "&sortBy=" + jw_config.audio_sorting
	
	html 				= jw_common.loadUrl(reading_index_url) 

	soup 			= BeautifulSoup(html)
	publications    = soup.findAll("div", { "class" : re.compile(r'\bPublication\b') })

	for publication in publications :
		title = publication.find('h3').contents[0].encode("utf-8");
		title = jw_common.cleanUpText(title);

		json_url = None
		try :
			json_url = publication.find("a", { "class" : "jsDownload" }).get('data-jsonurl')
		except :
			pass

		# placeholder if cover is missing
		cover_url = "http://assets.jw.org/themes/content-theme/images/thumbProduct_placeholder.jpg"
		try :
			cover_url = publication.findAll("img")[1].get('src')
		except :
			pass 

		listItem = xbmcgui.ListItem(
			label 			= title,
			thumbnailImage  = cover_url
		)	

		params = {
			"content_type"  : "audio", 
			"mode" 			: "open_music_json", 
			"json_url" 		: json_url
		}
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)	
		xbmcplugin.addDirectoryItem(
			handle		= jw_config.plugin_pid, 
			url 		= url, 
			listitem 	= listItem, 
			isFolder	= False 
		)

	jw_common.setNextPageLink(html, "open_dramatic_reading_index", "audio")

	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)
	jw_common.setThumbnailView()

