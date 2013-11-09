"""
AUDIO BIBLE RELATED FUNCTION
"""
import xbmcgui
import xbmcplugin

import urllib
import re

import jw_config
import jw_common

	
# List of bible books
def showAudioBibleIndex():
	
	language 		= jw_config.language
	bible_index_url = jw_common.getUrl(language) + jw_config.const[language]["bible_index_audio"]
	html 			= jw_common.loadUrl(bible_index_url) 
	
	# Grep book names
	regexp_book_names = '<a>([^<]+)</a>'
	book_names = re.findall(regexp_book_names, html)  	

	# Grep bible cover image
	regexp_cover = "data-img-size-md='([^']+)'"
	bible_cover = re.findall(regexp_cover, html)
	cover_img_url = bible_cover[0]

	book_num = 0
	for book in book_names:
		book_num = book_num + 1
		listItem 	= xbmcgui.ListItem(
			label 			= book_names[book_num -1] ,
			thumbnailImage  = cover_img_url
		)	
		params 		= {
			"content_type" 	: "audio", 
			"mode" 			: "open_bible_book_index",
			"book_num" 		: book_num
		} 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)	
		xbmcplugin.addDirectoryItem(
			handle		= jw_config.plugin_pid, 
			url			= url, 
			listitem	= listItem, 
			isFolder	= True 
		)  

	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)


# List of chapter of a specific book, playable
def showAudioBibleBookJson(book_num):

	lang_code 	= jw_config.const[jw_config.language]["lang_code"] 

	json_url 	= jw_config.app_url 
	json_url 	= json_url + lang_code 
	json_url 	= json_url + "_TRGCHlZRQVNYVrXF?output=json&pub=bi12&fileformat=MP3&alllangs=0&langwritten="
	json_url 	= json_url + lang_code 
	json_url 	= json_url + "&txtCMSLang="
	json_url 	= json_url + lang_code 
	json_url 	= json_url + "&booknum=" 
	json_url 	= json_url + book_num

	json 		= jw_common.loadJsonFromUrl(url = json_url, ajax = False)
	lang_code 	= lang_code
	book_name 	= json["pubName"]
	cover_url   = json["pubImage"]["url"]

	for mp3 in json["files"][lang_code]["MP3"]:

		# Skip 'zip' files
		if mp3["mimetype"] != "audio/mpeg":
			continue;

		url = mp3["file"]["url"]
		title = book_name + " - " + mp3["title"]

		listItem = xbmcgui.ListItem(
			label 			= title,
			thumbnailImage  = cover_url
		)
		
		listItem.setInfo(
			type 		= 'Music', 
			infoLabels 	= {'Title': title }
		)

		xbmcplugin.addDirectoryItem(
			handle		= jw_config.plugin_pid, 
			url			= url, 
			listitem	= listItem, 
			isFolder	= False 
		)  

	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)
