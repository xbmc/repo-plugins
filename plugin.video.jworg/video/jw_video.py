# -*- coding: UTF-8 -*-
"""
VIDEO RELATED FUNCTIONS
"""

import xbmc
import xbmcplugin
import xbmcgui

import re
import urllib

import jw_common
import jw_config


# show available video categories
def showVideoFilter():
	
	language 	= jw_config.language
	# jw_common.getUrl(language) ends with "/" it's something like "http://www.jw.org/it/"
	url 		= jw_common.getUrl(language) + jw_config.const[language]["video_path"] 
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
			handle		= jw_config.plugin_pid, 
			url			= url, 
			listitem	= listItem, 
			isFolder	= True 
		)  
	
	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)


# show available video pages
def showVideoIndex(start, video_filter):

	language 	= jw_config.language
	url 		= jw_common.getUrl(language) + jw_config.const[language]["video_path"] + "/?start=" + str(start) + "&videoFilter=" + video_filter  + "&sortBy=" + jw_config.video_sorting
	html 		= jw_common.loadUrl (url)
	max_resolution	= xbmcplugin.getSetting(jw_config.plugin_pid, "max_resolution")

	# Grep video titles
	regexp_video_title = 'data-onpagetitle="([^"]+)"'
	videos = re.findall(regexp_video_title, html)  

	# Grep poster of video
	regexp_video_poster = 'data-img-size-md=["\']([^"\']+)["\']'
	posters = re.findall(regexp_video_poster, html)

	# Grep url of json wich contain data on different version of the video [240,360, etc..]
	regexp_video_json = '.*[^"] data-jsonurl="([^"]+)".*'
	video_json = re.findall(regexp_video_json, html)

	if video_json is None or video_json == [] :
		string = jw_common.t(30033) + " "
		xbmcgui.Dialog().ok("jworg browser", string)
		return

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
			handle=jw_config.plugin_pid, 
			url=url, 
			listitem=listItem, 
			isFolder=True 
		)  
		count = count + 1

	jw_common.setNextPageLink(html, "open_video_index", "video", "video_filter", video_filter)

	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)
	jw_common.setThumbnailView()



# show available resolutions for a video (ed eventually other related titles, like interviews, etc.)	
# v 0.4.0: if user choose a default max resolution, it will be used (or the highest under it if not
# available )
def showVideoJsonUrl(json_url, thumb):

	language 		= jw_config.language
	json_url 		= "http://www.jw.org" + json_url
	json 			= jw_common.loadJsonFromUrl(url = json_url,  ajax = False)
	max_resolution	= xbmcplugin.getSetting(jw_config.plugin_pid, "max_resolution")

	# json equals to [] when a cached json was empty
	if json is None or json == [] :
		string = jw_common.t(30033) + " "
		xbmcgui.Dialog().ok("jworg browser", string)
		return

	language_code = jw_config.const[language]["lang_code"]

	# Case: "Bible from Japan" Video
	# No speak, so no language, so only one "" entry suitable for every language
	if len(json["languages"]) == 0:
		language_code = ""
 	

	# Create in memory dict of dict with all available videos
	video_dict = {}
	for mp4 in json["files"][language_code]["MP4"]:
		res 				= mp4["label"]		
		url_to_play			= mp4["file"]["url"]
		mp4_title_cleaned 	= jw_common.cleanUpText (mp4["title"])
		title 				= "[" + res + "] - " + mp4_title_cleaned

		if res not in video_dict :
			video_dict[res] = {}

		video_dict[res].update({mp4_title_cleaned:  url_to_play})

	# Try do autodetect the video to play basaed on user setting of
	# default video resolution
	list_only = False;
	
	print "JWORG: max_resolution: '" + max_resolution + "'"

	if (max_resolution != "0" and max_resolution != "") or max_resolution is None :
	
		right_resoluction_dict = None
		max_resolution = max_resolution + "p"

		# If found default resolution video, I use this
		# else I use the latest added (because it's the the highest) res available
		if max_resolution in video_dict is not None :
			right_resoluction_dict = video_dict[max_resolution]
		else :
			max_resolution, right_resoluction_dict = video_dict.popitem()

		# If I've only one video at right res, I play It
		if len(right_resoluction_dict) == 1 :
	
			title, url_to_play = right_resoluction_dict.popitem() 				

			listItem = xbmcgui.ListItem(
				label 			=  title
			)
			listItem.setInfo(
				type 		= 'Video', 
				infoLabels 	= {'Title': mp4_title_cleaned}
			)

			xbmc.Player().play(item=url_to_play, listitem=listItem)

			return;
		# This is an error condition, could not verify never ...
		elif  len(right_resoluction_dict) == 0 :
			print "JWORG: NO  one video at res " + max_resolution
		# There are many video at the right res: enable listing of ONLY these
		else :
			list_only = max_resolution
	

	# Standard listing code
	for mp4 in json["files"][language_code]["MP4"]:

		url 				= mp4["file"]["url"]
		res 				= mp4["label"]
		mp4_title_cleaned 	= jw_common.cleanUpText (mp4["title"])
		title 				= "[" + res + "] - " + mp4_title_cleaned

		if (list_only is not False) and (res != max_resolution) : 
			# if user has choosen a res, and there are more than one video on this res
			# I skip every video of different resolution, but show a list
			# of all available video of this resolution
			continue;

		listItem = xbmcgui.ListItem(
			label 			= title,
			thumbnailImage	= thumb
		)
		listItem.setInfo(
			type 		= 'Video', 
			infoLabels 	= {'Title': mp4_title_cleaned}
		)
		listItem.setProperty("IsPlayable","true")

		xbmcplugin.addDirectoryItem(
			handle		= jw_config.plugin_pid, 
			url			= url, 
			listitem	= listItem, 
			isFolder	= False 
		) 


	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)

