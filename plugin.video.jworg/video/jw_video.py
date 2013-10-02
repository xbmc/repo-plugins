# -*- coding: UTF-8 -*-
"""
VIDEO RELATED FUNCTIONS
"""

import xbmcplugin
import xbmcgui

import re
import urllib

import jw_common
import jw_config


# show available video categories
def showVideoFilter():
	
	language 	= jw_config.language
	url 		= jw_config.const[language]["video_path"] 
	html 		= jw_common.loadUrl(url)

	regexp_video_filters = '<option data-priority.* value="([^"]+)">([^<]+)</option>'
	filters = re.findall(regexp_video_filters, html) 

	# Output video filter list
	for video_filter in filters:
		title = jw_common.cleanUpText( video_filter[1] ) 
		listItem = xbmcgui.ListItem( title )	
		params = {
			"content_type"  : "video", 
			"mode" 			: "open_video_index", 
			"start" 		: 0, 
			"video_filter"  : video_filter[0]
		} 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(
			handle		= jw_config.pluginPid, 
			url			= url, 
			listitem	= listItem, 
			isFolder	= True 
		)  
	
	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)


# show available video pages
def showVideoIndex(start, video_filter):

	language 	= jw_config.language
	url 		= jw_config.const[language]["video_path"] + "/?start=" + str(start) + "&videoFilter=" + video_filter  + "&sortBy=" + jw_config.video_sorting
	html 		= jw_common.loadUrl (url)

	# Grep video titles
	regexp_video_title = 'data-onpagetitle="([^"]+)"'
	videos = re.findall(regexp_video_title, html)  

	# Grep poster of video
	regexp_video_poster = 'data-img-size-md=["\']([^"\']+)["\']'
	posters = re.findall(regexp_video_poster, html)

	# Grep url of json wich contain data on different version of the video [240,360, etc..]
	regexp_video_json = '.*[^"] data-jsonurl="([^"]+)".*'
	video_json = re.findall(regexp_video_json, html)

	count = 0
	# Output video list 
	for title in videos:
		listItem = xbmcgui.ListItem(
			label 			= title, 
			thumbnailImage 	= posters[count]
		)

		json_url = video_json[count]
		params = { 
			"content_type" 	: "video", 
			"mode" 			: "open_json_video", 
			"json_url"		: json_url,
			"thumb" 		: posters[count]
		} 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(
			handle=jw_config.pluginPid, 
			url=url, 
			listitem=listItem, 
			isFolder=True 
		)  
		count = count + 1

	jw_common.setNextPageLink(html, "open_video_index", "video", "video_filter", video_filter)

	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)
	jw_common.setThumbnailView()


# show available resolutions for a video (ed eventually other related titles, like interviews, etc.)	
def showVideoJsonUrl(json_url, thumb):

	language 	= jw_config.language
	json_url 	= "http://www.jw.org" + json_url
	json 		= jw_common.loadJsonFromUrl(json_url)

	if json is None :
		string = jw_common.t(30008) + " "
		xbmcgui.Dialog().ok("jworg browser", string)
		return

	language_code = jw_config.const[language]["lang_code"]

	# Case: "Bible from Japan" Video
	# No speak, so no language, so only one "" entry suitable for every language
	if len(json["languages"]) == 0:
		language_code = ""
 	
	for mp4 in json["files"][language_code]["MP4"]:

		url 				= mp4["file"]["url"]
		res 				= mp4["label"]
		mp4_title_cleaned 	= jw_common.cleanUpText (mp4["title"])
		title 				= "[" + res + "] - " + mp4_title_cleaned

		listItem = xbmcgui.ListItem(
			label 			= title,
			thumbnailImage	= thumb
		)
		listItem.setInfo(
			type 		= 'Video', 
			infoLabels 	= {'Title': mp4_title_cleaned}
		)
		xbmcplugin.addDirectoryItem(
			handle		= jw_config.pluginPid, 
			url			= url, 
			listitem	= listItem, 
			isFolder	= False 
		)  

	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)

