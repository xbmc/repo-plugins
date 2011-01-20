# -*- coding: utf-8 -*-
import os
import urllib
import urllib2
import xbmcgui
import xbmcplugin
import xbmcaddon

from xml.dom.minidom import parse, parseString

__settings__ = xbmcaddon.Addon(id='plugin.video.svtplay')
__language__ = __settings__.getLocalizedString

SETTINGS_HIGHEST_BITRATE = [320, 850, 1400, 2400][int(__settings__.getSetting("highest_bitrate"))]
SETTINGS_HIGHEST_BITRATE_DEBUG = [320, 850, 1400, 2400][int(__settings__.getSetting("highest_bitrate_debug"))]
SETTINGS_MAX_ITEMS_PER_PAGE = [20, 50, 100, 200][int(__settings__.getSetting("list_size"))]
SETTINGS_DEBUG = __settings__.getSetting("debug")
SETTINGS_CONTEXT_MENU =__settings__.getSetting("context_menu")
SETTINGS_COMMAND = __settings__.getSetting("command")

TEXT_NEXT_PAGE = __language__(30200)

MODE_DEVICECONFIG = "deviceconfig"
MODE_TITLE_LIST = "title"
MODE_TEASER_LIST = "teaser"
MODE_VIDEO_LIST = "video"
MODE_SEARCH_TITLE = "searchtitle"
MODE_SEARCH_VIDEO = "searchfull"
MODE_SEARCH_CLIP = "searchsample"
MODE_DEBUG = "debug"

BASE_URL_TEASER = "http://xml.svtplay.se/v1/teaser/list/"
BASE_URL_TITLE = "http://xml.svtplay.se/v1/title/list/"
BASE_URL_VIDEO = "http://xml.svtplay.se/v1/video/list/"
BASE_URL_SEARCH_TITLE = "http://xml.svtplay.se/v1/title/search/"
BASE_URL_SEARCH_VIDEO = "http://xml.svtplay.se/v1/video/search/"

END_URL_SEARCH_VIDEO = "expression=full"
END_URL_SEARCH_CLIP = "expression=sample"

NS_MEDIA = "http://search.yahoo.com/mrss/"
NS_PLAYOPML = "http://xml.svtplay.se/ns/playopml"
NS_PLAYRSS = "http://xml.svtplay.se/ns/playrss"
NS_OPENSEARCH = "http://a9.com/-/spec/opensearch/1.1/"

def deviceconfiguration(node=None, target="", path=""):
	
	if node is None:
		node = load_xml("http://svtplay.se/mobil/deviceconfiguration.xml").documentElement.getElementsByTagName("body")[0]
		
	for outline in get_child_outlines(node):

		title = outline.getAttribute("text").encode('utf-8')		
		next_path = path + title + "/"
		
		if target == path:

			type = outline.getAttribute("type")

			if path + title == "Karusellen" \
			or path + title == "Hjälpmeny" \
			or not (type == "rss" or type == "menu"):
				continue

			thumbnail = outline.getAttributeNS(NS_PLAYOPML, "thumbnail")
			ids = outline.getAttributeNS(NS_PLAYOPML, "contentNodeIds")
			xml_url = outline.getAttribute("xmlUrl")
			
			if ids:
				params = { "mode": MODE_TITLE_LIST, "ids": ids }
			elif xml_url:
				if xml_url.startswith(BASE_URL_SEARCH_TITLE ):
					params = { "mode": MODE_SEARCH_TITLE, "url": xml_url }
				elif xml_url.startswith(BASE_URL_SEARCH_VIDEO) and xml_url.endswith(END_URL_SEARCH_VIDEO):
					params = { "mode": MODE_SEARCH_VIDEO, "url": xml_url }
				elif xml_url.startswith(BASE_URL_SEARCH_VIDEO) and xml_url.endswith(END_URL_SEARCH_CLIP):
					params = { "mode": MODE_SEARCH_CLIP, "url": xml_url }
				elif xml_url.startswith(BASE_URL_TEASER):
					params = { "mode": MODE_TEASER_LIST, "url": xml_url }
				elif xml_url.startswith(BASE_URL_TITLE):
					params = { "mode": MODE_TITLE_LIST, "url": xml_url }
				elif xml_url.startswith(BASE_URL_VIDEO):
					params = { "mode": MODE_VIDEO_LIST, "url": xml_url }
				else:
					xbmc.log("unknown url: " + xml_url)
			else:
				params = { "mode": MODE_DEVICECONFIG, "path": next_path }

			add_directory_item(title, params, thumbnail)

		else:
			if target.startswith(next_path):
				deviceconfiguration(outline, target, next_path)

def title_list(ids="", url="", offset=1, list_size=0):

	if ids:
		url = BASE_URL_TITLE + ids

	doc = load_xml(get_offset_url(url, offset))

	for item in doc.getElementsByTagName("item"):

		if list_size < SETTINGS_MAX_ITEMS_PER_PAGE:

			title = get_node_value(item, "title")
		
			thumb = None
			thumbnail_nodes = item.getElementsByTagNameNS(NS_MEDIA, "thumbnail")
		
			if thumbnail_nodes:
				thumb = thumbnail_nodes[0].getAttribute("url")
		
			id = get_node_value(item, "titleId", NS_PLAYRSS)

			params = { "mode": MODE_VIDEO_LIST, "ids": id }
		
			list_size += 1
			offset += 1

			add_directory_item(title, params, thumb)

	pager(doc, ids, url, offset, list_size, MODE_TITLE_LIST, title_list)
	
def video_list(ids="", url="", offset=1, list_size=0):

	if ids:
		url = BASE_URL_VIDEO + ids

	doc = load_xml(get_offset_url(url, offset))
		
	for item in doc.getElementsByTagName("item"):
		
		if list_size < SETTINGS_MAX_ITEMS_PER_PAGE:
		
			media = get_media_content(item)
			thumb = get_media_thumbnail(item)
			title = get_node_value(media, "title", NS_MEDIA)

			params = { "url": media.getAttribute("url") }
			
			thumbnail = None
			
			if thumb:
				thumbnail = thumb.getAttribute("url")

			list_size += 1
			offset += 1
			#Check if live stream and if debug is enabled
			if media.getAttribute("expression") == "nonstop":
				params = { "url": media.getAttribute("url"), "live": "true"}
			elif SETTINGS_DEBUG:
				media_debug = get_media_content(item, SETTINGS_HIGHEST_BITRATE_DEBUG)
				params = { "url": media.getAttribute("url"), "url_debug": media_debug.getAttribute("url")}

			add_directory_item(title, params, thumbnail, False)

	pager(doc, ids, url, offset, list_size, MODE_VIDEO_LIST, video_list)

def teaser_list(ids="", url="", offset=1, list_size=0):

	if ids:
		url = BASE_URL_TEASER + ids

	doc = load_xml(get_offset_url(url, offset))
	
	for item in doc.getElementsByTagName("item"):
		
		if list_size < SETTINGS_MAX_ITEMS_PER_PAGE:
		
			media = get_media_content(item)
			thumb = get_media_thumbnail(item)
			title = get_node_value(item, "title")
			id = get_node_value(item, "titleId", NS_PLAYRSS)

			params = { "mode": MODE_VIDEO_LIST, "ids": id }
			
			list_size += 1
			offset += 1

			add_directory_item(title, params)

	pager(doc, ids, url, offset, list_size, MODE_TEASER_LIST, teaser_list)

def pager(doc, ids, url, offset, list_size, mode, callback):

	total_results = int(get_node_value(doc, "totalResults", NS_OPENSEARCH))

	if total_results > offset and list_size < SETTINGS_MAX_ITEMS_PER_PAGE:
		callback(ids, url, offset, list_size)
	elif total_results > offset:
		params = { "mode": mode, "ids": ids, "url": url, "offset": offset }
		add_directory_item(TEXT_NEXT_PAGE, params)

def get_child_outlines(node):
	for child in node.childNodes:
		if child.nodeType == child.ELEMENT_NODE and child.nodeName == "outline":
			yield child

def get_node_value(parent, name, ns=""):
	if ns:
		return parent.getElementsByTagNameNS(ns, name)[0].childNodes[0].data
	else:
		return parent.getElementsByTagName(name)[0].childNodes[0].data

def get_offset_url(url, offset):
	if offset == 0:
		return url

	if url.find("?") == -1:
		return url + "?start=" + str(offset)
	else:
		return url + "&start=" + str(offset)

def get_media_thumbnail(node):

	content_list = node.getElementsByTagNameNS(NS_MEDIA, "content");

	for c in content_list:
		if c.getAttribute("type") == "image/jpeg":
			return c

	return None
	
def get_media_content(node, settings_bitrate = SETTINGS_HIGHEST_BITRATE):
 
	group = node.getElementsByTagNameNS(NS_MEDIA, "group")
	
	if group:
		content_list = group[0].getElementsByTagNameNS(NS_MEDIA, "content");
	else:
		content_list = node.getElementsByTagNameNS(NS_MEDIA, "content");
 
	content = None
 
	for c in content_list:
	
		if not c.getAttribute("bitrate"):
			continue
	
		bitrate = float(c.getAttribute("bitrate"))
		type = c.getAttribute("type")

		if type == 'application/vnd.apple.mpegurl':
			continue
		
		if (not content and bitrate <= settings_bitrate) or (content and bitrate > float(content.getAttribute("bitrate")) and bitrate <= settings_bitrate):
			content = c

	# probably a live stream, check framerate instead
	if not content:
			
		for c in content_list:
		
			if not c.getAttribute("framerate"):
				continue
		
			framerate = float(c.getAttribute("framerate"))
			type = c.getAttribute("type")

			if type == 'application/vnd.apple.mpegurl':
				continue
			
			if not content or framerate > float(content.getAttribute("framerate")):
				content = c

	# hopefully we never get here, but some old streams that does't report biterate has been spotted
	if not content:
		for c in content_list:
			if c.getAttribute("medium") == "video":
				content = c
				
	return content
	
def add_directory_item(name, params={}, thumbnail=None, isFolder=True):

	li = xbmcgui.ListItem(name)

	if not thumbnail is None:
		li.setThumbnailImage(thumbnail)
	
	if isFolder == True:
		url = sys.argv[0] + '?' + urllib.urlencode(params)
	else:
		url = params["url"]
		li.setInfo(type="Video", infoLabels={ "Title": name })
		#Check if it's a live stream or if debug is enabled
		if params.has_key('live'):
			li.setProperty("IsLive", "true")
		elif params.has_key('url_debug'):
			cm = []
			cm_url = sys.argv[0] + '?' + "url=" + params["url_debug"] + "&mode=debug" + "&name=" + urllib.quote_plus(name.encode('utf_8'))
			cm.append((SETTINGS_CONTEXT_MENU , "XBMC.RunPlugin(%s)" % (cm_url)))
			li.addContextMenuItems( cm, replaceItems=False )

	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=isFolder)

def parameters_string_to_dict(str):

	params = {}

	if str:

		pairs = str[1:].split("&")

		for pair in pairs:

			split = pair.split('=')

			if (len(split)) == 2:
				params[split[0]] = split[1]
	
	return params

def search(mode,url):
	searchString = unikeyboard(__settings__.getSetting( "latestSearch" ), "" )
	if searchString == "":
		xbmcgui.Dialog().ok( __language__( 30301 ), __language__( 30302 ) )
	elif searchString:
		latestSearch = __settings__.setSetting( "latestSearch", searchString )
		dialogProgress = xbmcgui.DialogProgress()
		dialogProgress.create( "", __language__( 30303 ) , searchString)
		#The XBMC onscreen keyboard outputs utf-8 and this need to be encoded to unicode
		encodedSearchString = urllib.quote_plus(searchString.decode("utf_8").encode("raw_unicode_escape"))
		url = url + "?q=" + encodedSearchString

		if mode == MODE_SEARCH_TITLE:
			title_list("", url)
		if mode == MODE_SEARCH_VIDEO or mode == MODE_SEARCH_CLIP:
			video_list("", url)
	return

def debug(url, name):
	from unicodedata import normalize
		
	if url:
		name = normalize('NFKD', name.decode("unicode_escape")).encode('ASCII', 'ignore').lower()
		name = name.replace("\\", "-")
		name = name.replace("/","-")
		name = name.replace(" ",".")
		name = name.replace(":",".")
		name = name.replace("?","")
		name = name.replace("&","")
		command = None
		try:
			command = SETTINGS_COMMAND % (url, name)
			if (sys.platform == 'win32'):
				cmd = "System.Exec"
				xbmc.executebuiltin("%s(\\\"%s\\\")" % (cmd, command))
			elif (sys.platform.startswith('linux')):
				os.system("%s" % (command))
			elif (sys.platform.startswith('darwin')):
				os.system("\"%s\"" % (command))
			else:
				pass;
		except:
			pass

	return None

def unikeyboard(default, message):
	keyboard = xbmc.Keyboard(default, message)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		return keyboard.getText()
	else:
		return None

def load_xml(url):
	try:
		req = urllib2.Request(url)
		response = urllib2.urlopen(req)
		xml = response.read()
		response.close()
	
		return parseString(xml)
	except:
		xbmc.log("unable to load url: " + url)

params = parameters_string_to_dict(sys.argv[2])

mode = params.get("mode", None)
ids = params.get("ids",  "")
offset = int(params.get("offset",  "1"))
path = urllib.unquote_plus(params.get("path", ""))
url = urllib.unquote_plus(params.get("url",  ""))
name = urllib.unquote_plus(params.get("name",  ""))

if not sys.argv[2] or not mode:
	deviceconfiguration()
elif mode == MODE_DEVICECONFIG:
	deviceconfiguration(None, path)
elif mode == MODE_TEASER_LIST:
	teaser_list(ids, url)
elif mode == MODE_TITLE_LIST:
	title_list(ids, url, offset)
elif mode == MODE_VIDEO_LIST:
	video_list(ids, url, offset)
elif mode == MODE_SEARCH_TITLE or mode == MODE_SEARCH_VIDEO or mode == MODE_SEARCH_CLIP:
	search(mode,url)
elif mode == MODE_DEBUG:
	debug(url, name)

xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=True, cacheToDisc=True)