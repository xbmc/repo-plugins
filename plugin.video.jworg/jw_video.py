"""
VIDEO RELATED FUNCTION
"""

import xbmc
import xbmcplugin
import xbmcgui

import re
import urllib

import jw_load
import jw_config


# show available video categories
def showVideoFilter(language):
	
	url = jw_config.const[language]["video_path"];
	print "JWORG url for vdeo filters: " + url
	html = jw_load.loadUrl(url)

	regexp_video_filters = '<option data-priority.* value="([^"]+)">([^<]+)</option>'
	filters = re.findall(regexp_video_filters, html) 

	# Output video filter list
	for video_filter in filters:
		title = video_filter[1].replace("&amp;","&")
		listItem = xbmcgui.ListItem( title )	
		params = {"content_type" : "video", "mode": "open_video_page", "start" : 0, "video_filter" : video_filter[0]} 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(handle=jw_config.pluginPid, url=url, listitem=listItem, isFolder=True )  
	
	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)


# show available video pages
def showVideoIndex(language, start, video_filter):

	url = jw_config.const[language]["video_path"] + "/?start=" + str(start) + "&videoFilter=" + video_filter
	print "JWORG ShowVideoIndex url: " + url

	html = jw_load.loadUrl (url)

	# Grep video titles
	regexp_video_title = 'data-onpagetitle="([^"]+)"'
	videos = re.findall(regexp_video_title, html)  

	# Grep poster of video
	regexp_video_poster = 'data-img-size-md=["\']([^"\']+)["\']'
	posters = re.findall(regexp_video_poster, html)

	# Grep url of json wich contain data on different version of the video [240,360, etc..]
	regexp_video_json = '.*[^"] data-jsonurl="([^"]+)".*'
	video_json = re.findall(regexp_video_json, html)

	# Grep video pages "NEXT" link
	regexp_video_next_page = '<a class="iconNext.*start=([0-9]+).*title="([^""]+)"'
	next_link = re.findall(regexp_video_next_page, html)

	count = 0
	# Output video list 
	for title in videos:
		listItem = xbmcgui.ListItem(
			label=title, 
			thumbnailImage= posters[count]
		)

		print "JWORG title: " + title
		json_url = video_json[count]
		print "JWORG json_url: " + json_url
		params = {"content_type" : "video", "mode" : "open_json_video", "json_url": json_url} 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(
			handle=jw_config.pluginPid, 
			url=url, 
			listitem=listItem, 
			isFolder=True 
		)  
		count = count + 1

	# Output next page link
	try: 
		next_start =  next_link[0][0]
		title = jw_config.t(30001);
		listItem = xbmcgui.ListItem(title)
		params = {"content_type" : "video", "mode": "open_video_page", "start" : next_start, "video_filter" : video_filter} 
		url = jw_config.plugin_name + '?' + urllib.urlencode(params)
		xbmcplugin.addDirectoryItem(handle=jw_config.pluginPid, url=url, listitem=listItem, isFolder=True )  
	except:
		pass

	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)



	

# show available resolutions for a video (ed eventually other related titles, like interviews, etc.)	
def showVideoJsonUrl(language, json_url):

	json_url = "http://www.jw.org" + json_url
	json = jw_load.loadJsonFromUrl(json_url)

	if json is None :
		string = jw_config.t(30008) + " "
		xbmcgui.Dialog().ok("jworg browser", string)
		return

	language_code = jw_config.const[language]["lang_code"]

	# Case: "Bible from Japan" Video
	# No speak, so no language, so only one "" entry suitable for every language
	if len(json["languages"]) == 0:
		language_code = ""
 	
	for mp4 in json["files"][language_code]["MP4"]:
		url = mp4["file"]["url"]

		res = mp4["label"]
		title = "[" + res + "] - " + mp4["title"]
		title = title.replace("&quot;", '"')

		listItem = xbmcgui.ListItem(label=title)
		listItem.setInfo(type='Video', infoLabels={'Title': mp4["title"] })

		xbmcplugin.addDirectoryItem(
			handle=jw_config.pluginPid, 
			url=url, 
			listitem=listItem, 
			isFolder=False )  

	xbmcplugin.endOfDirectory(handle=jw_config.pluginPid)

