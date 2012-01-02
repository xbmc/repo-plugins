
import xbmc, xbmcgui, xbmcplugin, urllib2, urllib, re, string, sys, os, traceback, xbmcaddon, xbmcvfs

plugin =  'Revision3'
__author__ = 'stacked <stacked.xbmc@gmail.com>'
__url__ = 'http://code.google.com/p/plugin/'
__date__ = '01-02-2012'
__version__ = '2.0.1'
settings = xbmcaddon.Addon(id='plugin.video.revision3')
dbg = False
dbglevel = 3
next_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'next.png' )
more_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'more.png' )
downloads_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'downloads.png' )
old_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'old.png' )
current_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'current.png' )
search_thumb = os.path.join( settings.getAddonInfo( 'path' ), 'resources', 'media', 'search.png' )

import CommonFunctions
common = CommonFunctions.CommonFunctions()
common.plugin = plugin

import SimpleDownloader as downloader
downloader = downloader.SimpleDownloader()

def open_url(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8')
	content = urllib2.urlopen(req)
	data = content.read()
	content.close()
	return data

def build_main_directory(url):
	path = url
	html = open_url(url)
	shows = common.parseDOM(html, "ul", attrs = { "id": "shows" })[0]
	url_name = re.compile('<h3><a href="(.+?)">(.+?)</a></h3>').findall(shows)
	image = re.compile('class="thumbnail"><img src="(.+?)" /></a>').findall(shows)
	plot = common.parseDOM(shows, "p", attrs = { "class": "description" })
	if settings.getSetting('folder') == 'true' and settings.getSetting( 'downloadPath' ) and path == 'http://revision3.com/shows/':
		url = settings.getSetting("downloadPath")
		listitem = xbmcgui.ListItem( label = "[ Downloads ]" , iconImage = downloads_thumb, thumbnailImage = downloads_thumb )
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = url, listitem = listitem, isFolder = True)
	if path == 'http://revision3.com/shows/':
		listitem = xbmcgui.ListItem(label = '[ Recently Released ]', iconImage = current_thumb, thumbnailImage = current_thumb)
		u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus('Recently Released') + "&url=" + urllib.quote_plus('http://revision3.com/episodes/page?&hideArrows=1&type=recent&page=1')
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = True)
		listitem = xbmcgui.ListItem(label = '[ Archived Shows ]', iconImage = old_thumb, thumbnailImage = old_thumb)
		u = sys.argv[0] + "?mode=3&url=" + urllib.quote_plus('http://revision3.com/shows/archive')
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = True)
		listitem = xbmcgui.ListItem(label = '[ Search ]', iconImage = search_thumb, thumbnailImage = search_thumb)
		u = sys.argv[0] + "?mode=4&url=" + urllib.quote_plus('search')
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = True)
	count = 0
	for url, name in url_name:
		fanart = url.replace('/','')
		url = 'http://revision3.com' + url + '/episodes'
		listitem = xbmcgui.ListItem(label = name, iconImage = image[count].replace('160x160','200x200'), thumbnailImage = image[count].replace('160x160','200x200'))
		listitem.setProperty('fanart_image',settings.getSetting(fanart))
		listitem.setInfo( type = "Video", infoLabels = { "Title": name, "Studio": 'Revision3', "Plot": plot[count] } )
		u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus(name) + "&url=" + urllib.quote_plus(url)
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = True)
		count += 1
	xbmcplugin.addSortMethod( handle = int(sys.argv[ 1 ]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def build_sub_directory(url, name):
	saveurl = url
	studio = name
	#html = common.fetchPage({"link": url})['content']
	html = open_url(url)
	ret = common.parseDOM(html, "div", attrs = { "id": "main-episodes" })
	pageLoad = common.parseDOM(ret, "a", ret = "onclick")
	if len(ret) == 0:
		ret = common.parseDOM(html, "div", attrs = { "id": "all-episodes" })
		pageLoad = common.parseDOM(ret, "a", ret = "onclick")
	if len(ret) == 0:
		ret = common.parseDOM(html, "ul", attrs = { "class": "episode-grid" })
		pageLoad = common.parseDOM(html, "a", ret = "onclick")
	current = common.parseDOM(html, "span", attrs = { "class": "active" })
	episodes = common.parseDOM(ret, "li", attrs = { "class": "episode item" })
	try:
		img = common.parseDOM(episodes[0], "img", ret = "src")[0]
		downloads = 'http://revision3.com/' + img.rsplit('/')[6] + '/' + img.rsplit('/')[6] + '_downloads'
		#fresult = common.fetchPage({"link": downloads})['content']
		fresult = open_url(downloads)
		data = re.compile( '<a href="(.+?)" target="_blank">1920x1200</a>' ).findall(fresult)
		if len(data) > 1:
			fanart = data[1]
		else:
			fanart = data[0]
		settings.setSetting(img.rsplit('/')[6], fanart)
		if studio == 'Recently Released':
			fanart = ''
	except:
		fanart = ''
	try:
		child = common.parseDOM(html, "div", attrs = { "id": "child-episodes" })
		label = common.parseDOM(html, "a", attrs = { "href": "#child-episodes" })[0]
		childshow = common.parseDOM(child, "a", attrs = { "class": "thumbnail" }, ret = "href" )[0].rsplit('/')[1]
		csaveurl = 'http://revision3.com/' + childshow + '/episodePage?type=recent&limit=15&hideShow=1&hideArrows=1&page=1'
		listitem = xbmcgui.ListItem( label = '[ ' + label + ' ]', iconImage = more_thumb, thumbnailImage = more_thumb )
		listitem.setProperty('fanart_image',fanart)
		u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus(studio) + "&url=" + urllib.quote_plus(csaveurl)
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = True)
	except:
		pass
	try:
		strs = 'http://revision3.com' + pageLoad[-1:][0].rsplit('\'')[1]
		params = common.getParameters(strs)
		saveurl = strs.rstrip('&page=' + params['page']) + '&page=' + str( int(current[0]) + 1 )
		if int(params['page']) > int(current[0]):
			next = True
		else:
			next = False
	except:
		next = False
	for data in episodes:
		thumb = common.parseDOM(data, "img", ret = "src")[0].replace('small.thumb','medium.thumb')
		plot = clean(common.parseDOM(data, "img", ret = "alt")[0])
		name = clean(common.stripTags(common.parseDOM(data, "a")[1]))
		cut = common.parseDOM(data, "a")[1]
		try:
			studio = clean(common.parseDOM(cut, "strong")[0])
		except:
			pass
		name = name.replace(studio + '   ','')
		url = 'http://revision3.com' + common.parseDOM(data, "a", attrs = { "class": "thumbnail" }, ret = "href")[0]
		try:
			episode = name.rsplit(' ')[1]
			date = name.rsplit(' ')[3].rsplit('/')[1] + '.'  + name.rsplit(' ')[3].rsplit('/')[0] + '.' + name.rsplit(' ')[3].rsplit('/')[2]
		except:
			episode = '0'
			date = '00.00.0000'
		duration = name[-6:].rstrip(')').replace('(','')
		listitem = xbmcgui.ListItem(label = plot, iconImage = thumb, thumbnailImage = thumb)
		listitem.setProperty('fanart_image',fanart)
		listitem.setInfo( type = "Video", infoLabels = { "Title": plot, "Director": plugin, "Studio": studio, "Plot": plot, "Episode": int(episode), "Date": date, "Duration": duration } )
		u = sys.argv[0] + "?mode=2&name=" + urllib.quote_plus(plot) + "&url=" + urllib.quote_plus(url) + "&plot=" + urllib.quote_plus(plot) + "&studio=" + urllib.quote_plus(studio) + "&episode=" + urllib.quote_plus(episode) + "&thumb=" + urllib.quote_plus(thumb)
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = False)
	if next == True:
		listitem = xbmcgui.ListItem( label = 'Next Page (' + str( int(current[0]) + 1 ) + ')' , iconImage = next_thumb, thumbnailImage = next_thumb )
		listitem.setProperty('fanart_image',fanart)
		u = sys.argv[0] + "?mode=1&name=" + urllib.quote_plus(studio) + "&url=" + urllib.quote_plus(saveurl)
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = True)	
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_EPISODE )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def build_search_directory(url):
	if url == 'search':
		search = common.getUserInput("Enter search term", "").replace(' ','+')
		url = 'http://revision3.com/search/page?type=video&q=' + search + '&limit=10&page=1'
	html = open_url(url)
	current = common.parseDOM(html, "span", attrs = { "class": "active" })
	pageLoad = common.parseDOM(html, "a", ret = "onclick")
	try:
		strs = 'http://revision3.com' + pageLoad[-1:][0].rsplit('\'')[1]
		params = common.getParameters(strs)
		saveurl = strs.rstrip('&page=' + params['page']) + '&page=' + str( int(current[0]) + 1 )
		if int(params['page']) > int(current[0]):
			next = True
		else:
			next = False
	except:
		next = False
	episodes = common.parseDOM(html, "li", attrs = { "class": "video" })
	if len(episodes) == 0:
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( plugin , settings.getLocalizedString( 30009 ) + '\n' + settings.getLocalizedString( 30010 ) )
		return
	for data in episodes:
		thumb = common.parseDOM(data, "img", ret = "src")[0]
		url = common.parseDOM(data, "a", attrs = { "class": "thumbnail" }, ret = "href" )[0]
		url = clean(url.replace('http://www.videosurf.com/webui/inc/go.php?redirect=','')).replace('&client_id=revision3','')
		title = clean(common.parseDOM(data, "a", attrs = { "class": "title" })[0])
		plot = clean(common.stripTags(common.parseDOM(data, "div", attrs = { "class": "description" })[0]))
		try:
			studio = title.rsplit(' - ')[1]
		except:
			studio = ''
		listitem = xbmcgui.ListItem(label = title, iconImage = thumb, thumbnailImage = thumb)
		listitem.setInfo( type = "Video", infoLabels = { "Title": title, "Director": plugin, "Studio": studio, "Plot": plot } )
		u = sys.argv[0] + "?mode=2&name=" + urllib.quote_plus(title) + "&url=" + urllib.quote_plus(url) + "&plot=" + urllib.quote_plus(plot) + "&studio=" + urllib.quote_plus(studio) + "&episode=" + urllib.quote_plus('0') + "&thumb=" + urllib.quote_plus(thumb)
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = False)
	if next == True:
		listitem = xbmcgui.ListItem( label = 'Next Page (' + str( int(current[0]) + 1 ) + ')' , iconImage = next_thumb, thumbnailImage = next_thumb )
		u = sys.argv[0] + "?mode=4&name=" + urllib.quote_plus(studio) + "&url=" + urllib.quote_plus(saveurl)
		ok = xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = listitem, isFolder = True)	
	xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED )
	xbmcplugin.endOfDirectory(int(sys.argv[1]))

def clean(name):
	remove = [('&amp;','&'), ('&quot;','"'), ('&#039;','\''), ('\r\n',''), ('&apos;','\''), ('&#150;','-'), ('%3A',':'), ('%2F','/')]
	for trash, crap in remove:
		name = name.replace(trash,crap)
	return name

def get_video(url, name, plot, studio, episode, thumb):
	#result = common.fetchPage({"link": url})['content']
	result = open_url(url)
	list = ['MP4','Quicktime','Xvid','WMV']
	durl = {}
	for type in list:
		content = common.parseDOM(result, "div", attrs = { "id": "action-panels-download-" + type })
		videos = common.parseDOM(content, "a", attrs = { "class": "sizename" })
		links = common.parseDOM(content, "a", attrs = { "class": "sizename" }, ret="href")
		count = 0
		for add in videos:
			code = type + ':' + add
			durl[code] = links[count]
			count += 1
	dictList = [] 
	for key, value in durl.iteritems():
		dictList.append(key)
	quality = settings.getSetting('type')
	try:
		purl = durl[quality]
		ret = None
	except:
		dialog = xbmcgui.Dialog()
		ret = dialog.select('Video Type', dictList)
		purl = durl[dictList[ret]]
	if ret != -1:
		if settings.getSetting('download') == 'true':
			params = { "videoid": str(episode), "video_url": purl, "Title": name }
			downloader.downloadVideo(params)
		else:
			#thumb = xbmc.getInfoImage( 'ListItem.Thumb' )
			listitem = xbmcgui.ListItem(label = name , iconImage = 'DefaultVideo.png', thumbnailImage = thumb)
			listitem.setInfo( type = "Video", infoLabels={ "Title": name, "Director": plugin, "Studio": studio, "Plot": plot, "Episode": int(episode)  } )
			xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(purl, listitem)	

params = common.getParameters(sys.argv[2])
url = None
name = None
mode = None
plot = None
studio = None
episode = None
thumb = None

try:
	url = urllib.unquote_plus(params["url"])
except:
	pass
try:
	name = urllib.unquote_plus(params["name"])
except:
	pass
try:
	mode = int(params["mode"])
except:
	pass
try:
	plot = urllib.unquote_plus(params["plot"])
except:
	pass
try:
	studio = urllib.unquote_plus(params["studio"])
except:
	pass
try:
	episode = int(params["episode"])
except:
	pass
try:
	thumb = urllib.unquote_plus(params["thumb"])
except:
	pass

if mode == None:
	url = 'http://revision3.com/shows/'
	build_main_directory(url)
elif mode == 1:
	build_sub_directory(url, name)
elif mode == 2:
	get_video(url, name, plot, studio, episode, thumb)
elif mode == 3:
	build_main_directory(url)
elif mode == 4:
	build_search_directory(url)
