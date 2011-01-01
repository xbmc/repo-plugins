import urllib, urllib2, re
import xbmcplugin, xbmcaddon, xbmcgui

# plugin definition
__plugin__ = "The Escapist"
__author__ = "Mike Cronce"
__version__ = "0.1.3"
__url__ = "http://code.google.com/p/xbmc-plugin-escapist/"
__svn__ = "http://xbmc-plugin-escapist.googlecode.com/svn/trunk/"
__svn_revision__ = "$Revision$"
__settings__ = xbmcaddon.Addon(id = 'plugin.video.escapistmagazine')

# constants
seriesIndexUrl = "http://www.escapistmagazine.com/videos/galleries"

# function definitions

def get_params():
	param = {}
	paramstring = sys.argv[2]
	if(len(paramstring) >= 2):
		params = sys.argv[2]
		cleanedparams = params.replace('?', '')
		if(params[len(params) - 1] == '/'):
			params = params[0:len(params) - 2]
		pairsOfParams = cleanedparams.split('&')
		for i in range(len(pairsOfParams)):
			splitParams = {}
			splitParams = pairsOfParams[i].split('=')
			if(len(splitParams) == 2):
				param[splitParams[0]] = splitParams[1]
	return param

def retrieveUrl(url, referer):
	req = urllib2.Request(url)
	req.add_header("User-Agent", "Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.3) Gecko/20100402 Namoroka/3.6.3")
	req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
	req.add_header("Accept-Language", "en-us,en;q=0.5")
	req.add_header("Accept-Encoding", "deflate")
	req.add_header("Accept-Charset", "ISO-8859-1,utf-8;q=0.7,*;q=0.7")
	if(referer != ""):
		req.add_header("Referer", referer)
	response = urllib2.urlopen(req)
	file = response.read()
	response.close()
	return file

def CATEGORIES():
	html = retrieveUrl(seriesIndexUrl, "")
	match = re.compile(
		'<div class=\'gallery_title\'><a href=\'([^\']+)\'>([^><]+)</a></div>' +
		'<a href=\'/rss/videos/list/[0-9]*\\.xml\' class=\'feedicon\' alt=\'\\2 : Latest Videos\' title=\'\\2 : Latest Videos\'>\\2 : Latest Videos</a>' +
		'<div class=\'gallery_description\'>[^><]*</div>' +
		'<div class=\'gallery_title_card\'><a href=\'\\1\'>' +
			'<img src=\'([^\']+)\' width=\'[0-9]+\' height=\'[0-9]+\'>'
		'</a></div>'
	).findall(html)
	for url, name, thumbnail in match:
		addDir(name, url, seriesIndexUrl, 1, thumbnail, len(match))

def INDEX(indexName, indexUrl, referer):
	i = indexUrl.find('?')
	if(i == -1):
		baseUrl = indexUrl
	else:
		baseUrl = indexUrl[:i]
	html = retrieveUrl(indexUrl, referer)
	videos = re.compile('<div class=\'filmstrip_video\'>' +
		'<a href=\'(' + baseUrl + '/[^\']+)\'><img src=\'([^\']+)\'></a>' +
		'<div class=\'title\'>([^><]+)</div>' +
		'<div class=\'date\'>Date: ([\\d]{1,2}/[\\d]{1,2}/[\\d]{4})</div>'
	).findall(html)
	page_icon = re.compile('<div id=\'video_banner\' style=\'background: url\\("([^"]*)"\\)').findall(html)
	if(len(page_icon) > 0):
		page_icon = page_icon[0]
	else:
		page_icon = None
	count = len(videos)
	np = re.compile('<a href=\'([^\']*)\' class=\'next_page\'>Next</a>').findall(html)
	pp = re.compile('<a href=\'([^\']*)\' class=\'prev_page\'>Prev</a>').findall(html)
	if(len(np) > 0):
		count = count + 1
		np = np[0]
	else:
		np = None
	if(len(pp) > 0):
		count = count + 1
		pgnum = re.compile('page=([0-9]*)').findall(pp[0])
		addDir("<<   Page " + pgnum[0], pp[0], indexUrl, 2, page_icon, count)
	for pageUrl, thumbnail, name, date in videos:
		addLink(name, date, pageUrl, indexUrl, thumbnail, count)
	if(np != None):
		pgnum = re.compile('page=([0-9]*)').findall(np)
		addDir("Page " + pgnum[0] + "   >>", np, indexUrl, 2, page_icon, count)

def PLAYVIDEO(url, referer):
	# retrieve page
	page = retrieveUrl(url, referer)
	# locate the JSON settings file
	match = re.compile('<meta [a-zA-Z]*="og:video" content="[^"]*\\?config=([^"]*)"(?: /)?>').findall(page)
	config_url = re.compile('([^?]*)\\?.*').findall(urllib.unquote(match[0]))[0] + "?player_version=2.5&playerId=player_api&host=escapistmagazine.com"
	# got it, now pull the video title
	name = re.compile('<title>The Escapist : Video Galleries : ([^<]*)</title>').findall(page)[0]
	# pull the JSON file now
	json = retrieveUrl(config_url, "")
	# parse out the video URL and eliminate the advertisement
	match = re.compile("\\{'url':'([^']*)\\.(mp4)',").findall(json)
	for url, ext in match:
		if(url.find("-ad-") == -1):
			video_url = url + '.' + ext
			break
	# cool, got it, now create and open the video
	liz = xbmcgui.ListItem(name, path = video_url)
	liz.setInfo(type = "Video", infoLabels = {"Title": name})
	liz.setProperty('isPlayable', 'true')
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)

def addDir(name, url, referer, mode, icon, count):
	ok = True
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&referer=" + urllib.quote_plus(referer) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
	liz = xbmcgui.ListItem(name, iconImage = icon, thumbnailImage = icon)
	liz.setInfo(type = "Video", infoLabels = {"Title": name})
	ok = xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, isFolder = True, totalItems = count)
	return ok

def addLink(name, date, url, referer, icon, count):
	ok = True
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&referer=" + urllib.quote_plus(referer) + "&mode=3&name=" + urllib.quote_plus(name)
	liz = xbmcgui.ListItem(name, iconImage = icon, thumbnailImage = icon)
	liz.setInfo(type = "Video", infoLabels = {"Title": name, "Date": date})
	liz.setProperty('isPlayable', 'true')
	ok = xbmcplugin.addDirectoryItem(int(sys.argv[1]), u, liz, isFolder = False, totalItems = count)
	return ok


############ int main(int argc, char** argv) {//LAWL ############

url = None
referer = ""
name = None
mode = None

params = get_params()

try:
	url = urllib.unquote_plus(params["url"])
except:
	pass

try:
	referer = urllib.unquote_plus(params["referer"])
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

if mode == None or mode == 0 or url == None or len(url) < 1:
	CATEGORIES()
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 1:
	INDEX(name, url, referer)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 2:
	INDEX(name, url, referer)
	xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing = True)
elif mode == 3:
	PLAYVIDEO(url, referer)

