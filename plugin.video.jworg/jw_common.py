import re
import urllib
import urllib2
import json

import jw_config

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon


# Translation util
def t(string_number):
	plugin = xbmcaddon.Addon("plugin.video.jworg")
	return plugin.getLocalizedString(string_number)


def cleanUpText(text):
	text = text.replace("&amp;","&")
	text = text.replace("&#039;", "'")
	text = text.replace("&quot;", '"')
	text = text.replace("&nbsp;", ' ')
	text = text.strip()
	return text

def removeHtml(text):
	clean = re.sub("<([^>]*)>", "", text)
	return clean

"""
VISUAL HELPER
"""
# Grep "NEXT" link and add to current directory
# param_name and param_value is used to pass one additional param when adding directory item
def setNextPageLink(html, mode, type, param_name = None, param_value = None):

	regexp_video_next_page = '<a class="iconNext.*start=([0-9]+).*title="([^""]+)"'
	next_link = re.findall(regexp_video_next_page, html)

	if next_link == []:
		return 

	next_start  = next_link[0][0]
	title 		= t(30001)
	listItem 	= xbmcgui.ListItem(title)
	params 		= {
		"content_type" 	: type, 
		"mode" 			: mode, 
		"start" 		: next_start 
	} 
	# Video browser needs "video_filter" param
	if param_name is not None :
		params[param_name] = param_value

	url = jw_config.plugin_name + '?' + urllib.urlencode(params)

	xbmcplugin.addDirectoryItem(
		handle		= jw_config.plugin_pid, 
		url			= url, 
		listitem	= listItem, 
		isFolder	= True 
	)  

def setThumbnailView() :
	if jw_config.skin_used == 'skin.confluence': 
		xbmc.executebuiltin('Container.SetViewMode(500)') 

def setDefaultView() :
	xbmc.executebuiltin('Container.SetViewMode(50)') 

"""
REMOTE CONTENT LOAD 
"""
def loadNotCachedUrl(url):
	response = urllib2.urlopen (url)
	html = response.read()
	return html		

def loadUrl (url, month_cache = False ):
	html = ""
	try :
		if month_cache == True :
			html = jw_config.cache_month.cacheFunction(loadNotCachedUrl, url)	
		else :
			html = jw_config.cache.cacheFunction(loadNotCachedUrl, url)	
	except:
		pass 
	return html	


def loadNotCachedJsonFromUrl(url, ajax):
	data = ""
	try:
		if ajax == True :
			request = urllib2.Request(url, headers=
			{
				"Accept" 			: "application/json, text/javascript,",
				"Host"				: "wol.jw.org",
				"X-Requested-With"	: "XMLHttpRequest",
			})
		else :
			request = urllib2.Request(url)

		response = urllib2.urlopen(request).read()
		data = json.loads(response)

	except urllib2.URLError, e: 
		xbmc.log ("JWORG url error", xbmc.LOGERROR)
		for arg in e.args :
			print arg
		pass
		
	except urllib2.HTTPError, e:
		xbmc.log ("JWORG http error", xbmc.LOGERROR)
		xbmc.log (e.code, xbmc.LOGERROR)
		xbmc.log (e.read(), xbmc.LOGERROR)
		pass

	# other exception give exceptions

	return data


def loadJsonFromUrl (url, ajax, month_cache = False ):

	if month_cache == True :
		data = jw_config.cache_month.cacheFunction(loadNotCachedJsonFromUrl, url, ajax)	
	else :
		data = jw_config.cache.cacheFunction(loadNotCachedJsonFromUrl, url, ajax)	
	return data


"""
URL HELPER
"""
def getUrl(language):
	return jw_config.main_url + jw_config.const[language]["url_lang_code"]  + "/" 


"""
AUDIO HELPER
"""
def playMp3(url):
	item = xbmcgui.ListItem(path=url)
	xbmcplugin.setResolvedUrl(handle=jw_config.plugin_pid, succeeded=True, listitem=item)