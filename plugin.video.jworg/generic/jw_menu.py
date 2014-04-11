"""
This file is for enabling use from video or audio or program shortcut
on confluence home page
"""
import jw_common
import jw_config

import xbmcgui
import xbmcplugin

import urllib

def showMenu() :
	listItem = xbmcgui.ListItem(
		label 			= jw_common.t(30046)
	)	
	params = { 
		"content_type" 		: "video"
	}
	url = jw_config.plugin_name + '?' + urllib.urlencode(params)
	xbmcplugin.addDirectoryItem(
		handle	 = jw_config.plugin_pid, 
		url 	 = url, 
		listitem = listItem, 
		isFolder = True 
	)  

	listItem = xbmcgui.ListItem(
		label 			= jw_common.t(30047)
	)	
	params = { 
		"content_type" 		: "audio", 
	}
	url = jw_config.plugin_name + '?' + urllib.urlencode(params)
	xbmcplugin.addDirectoryItem(
		handle	 = jw_config.plugin_pid, 
		url 	 = url, 
		listitem = listItem, 
		isFolder = True 
	)
	listItem = xbmcgui.ListItem(
		label 			= jw_common.t(30048)
	)	
	params = { 
		"content_type" 		: "executable", 
	}
	url = jw_config.plugin_name + '?' + urllib.urlencode(params)
	xbmcplugin.addDirectoryItem(
		handle	 = jw_config.plugin_pid, 
		url 	 = url, 
		listitem = listItem, 
		isFolder = True 
	)
	xbmcplugin.endOfDirectory(handle=jw_config.plugin_pid)

