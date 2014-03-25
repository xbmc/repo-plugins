"""
AUDIO BIBLE RELATED FUNCTION
"""
import xbmcgui
import xbmcplugin

from BeautifulSoup import BeautifulSoup 
import urllib
import re

import jw_config
import jw_common

	
# List of bible books
def showAudioBibleIndex():
	
	language 		= jw_config.language
	bible_index_url = jw_common.getUrl(language) + jw_config.const[language]["bible_index_audio"]
	html 			= jw_common.loadUrl(bible_index_url) 
	
	soup 		= BeautifulSoup(html)

	cover_div 	= soup.findAll('div',{"class": re.compile(r'\bcvr\b')})
	span 		= cover_div[0].findAll('span')
	img_url     = span[0].get('data-img-size-md');

	boxes 	= soup.findAll('li',{"class": re.compile(r'\bbookName\b')})

	book_num = 0
	for box in boxes :
		book_num = book_num +1
		
		anchors =box.findAll('a')

		book_name = anchors[0].contents[0]

		listItem 	= xbmcgui.ListItem(
			label 			= book_name,
			thumbnailImage  = img_url
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
			continue

		params = {
			"content_type"  : "audio", 
			"mode"          : "play_mp3", 
			"file_url"      : mp3["file"]["url"]
		}

		#url = mp3["file"]["url"]
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)    

		title = book_name + " - " + mp3["title"]

		listItem = xbmcgui.ListItem(
			label 			= title,
			thumbnailImage  = cover_url
		)
		
		listItem.setInfo(
			type 		= 'Music', 
			infoLabels 	= {'Title': title }
		)

		listItem.setProperty("IsPlayable","true")

		xbmcplugin.addDirectoryItem(
			handle		= jw_config.plugin_pid, 
			url			= url, 
			listitem	= listItem, 
			isFolder	= False 
		)  

	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)
