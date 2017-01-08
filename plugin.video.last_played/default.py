import os, time
import json
import urllib, urllib2
import xbmc
import xbmcaddon
import xbmcvfs

addon = xbmcaddon.Addon()
enable_debug = addon.getSetting('enable_debug')
if addon.getSetting('custom_path_enable') == "true" and addon.getSetting('custom_path') != "":
	txtpath = addon.getSetting('custom_path').decode("utf-8")
else:
	txtpath = xbmc.translatePath(addon.getAddonInfo('profile')).decode("utf-8")
	if not os.path.exists(txtpath):
		os.makedirs(txtpath)
txtfile = txtpath + "lastPlayed.json"
fivestar = addon.getSetting('fivestar')
enable_debug = addon.getSetting('enable_debug')
newline={}
lang = addon.getLocalizedString

# Builds JSON request with provided json data
def buildRequest(method, params, jsonrpc='2.0', rid='1'):
	request = { 'jsonrpc' : jsonrpc, 'method' : method, 'params' : params, 'id' : rid, }
	return request

# Checks JSON response and returns boolean result
def checkReponse(response):
	result = False
	if ( ('result' in response) and ('error' not in response) ):
		result = True
	return result

# Executes JSON request and returns the JSON response
def JSexecute(request):
	request_string = json.dumps(request)
	response = xbmc.executeJSONRPC(request_string)
	if ( response ):
		response = json.loads(response)
	return response

# Performs single JSON query and returns result boolean, data dictionary and error string
def JSquery(request):
	result = False
	data = {}
	error = ''
	if ( request ):
		response = JSexecute(request)
		if ( response ):
			result = checkReponse(response)
			if ( result ):
				data = response['result']
			else: error = response['error']
	return (result, data, error)

def send2fivestar(line):
	wid = line["id"]
	if line["type"]=="movie": typ="M"
	elif line["type"]=="episode": typ="S"
	else: typ="V"

	if typ=="M" and addon.getSetting('movies') != "true": return
	if typ=="S" and addon.getSetting('tv') != "true": return
	if typ=="V" and addon.getSetting('videos') != "true": return

	imdbId = ""
	tvdbId = ""
	orgTitle = ""
	showTitle = ""
	season = ""
	episode = ""
	if wid>0:
		if typ=="M":
			request = buildRequest('VideoLibrary.GetMovieDetails', {'movieid' : wid, 'properties' : ['imdbnumber', 'originaltitle']})
			result, data = JSquery(request)[:2]
			if ( result and 'moviedetails' in data ):
				imdbId = data['moviedetails']["imdbnumber"]
				orgTitle = data['moviedetails']["originaltitle"]
		elif typ=="S":
			request = buildRequest('VideoLibrary.GetEpisodeDetails', {'episodeid' : wid, 'properties' : ['tvshowid', 'season', 'episode']})
			result, data = JSquery(request)[:2]
			if ( result and 'episodedetails' in data ):
				season = data['episodedetails']["season"]
				episode = data['episodedetails']["episode"]
				request = buildRequest('VideoLibrary.GetTvShowDetails', {'tvshowid' : data['episodedetails']["tvshowid"], 'properties' : ['imdbnumber', 'originaltitle']})
				result, data = JSquery(request)[:2]
				if ( result and 'tvshowdetails' in data ):
					showTitle = data['tvshowdetails']["label"]
					orgTitle = data['tvshowdetails']["originaltitle"]
					tvdbId = data['tvshowdetails']["imdbnumber"]

	url = "http://www.5star-movies.com/WebService.asmx/kodiWatch?tmdbId="
	url = url + "&tvdbId=" + tvdbId
	url = url + "&imdbId=" + imdbId
	url = url + "&kodiId=" + str(wid)
	url = url + "&title=" + urllib.quote(line["title"].encode("utf-8"))
	url = url + "&orgtitle=" + urllib.quote(orgTitle.encode("utf-8"))
	url = url + "&year=" + str(line["year"])
	url = url + "&source=" + urllib.quote(line["source"].encode("utf-8"))
	url = url + "&type=" + typ
	url = url + "&usr=" + urllib.quote(addon.getSetting('TMDBusr'))
	url = url + "&pwd=" + addon.getSetting('TMDBpwd')
	url = url + "&link=" + urllib.quote(line["file"].encode("utf-8"))
	url = url + "&thumbnail=" + urllib.quote(line["thumbnail"].encode("utf-8"))
	url = url + "&fanart=" + urllib.quote(line["fanart"].encode("utf-8"))
	url = url + "&showtitle=" + urllib.quote(showTitle.encode("utf-8"))
	url = url + "&season=" + str(season)
	url = url + "&episode=" + str(episode)
	url = url + "&version=1.07"
	url = url + "&date=" + line["date"]

	request = urllib2.Request(url)
	urllib2.urlopen(request)

def videoStart():
	request = buildRequest('Player.GetItem', {'playerid' : 1, 'properties' : ['file', 'title', 'year', 'thumbnail', 'fanart']})
	result, data = JSquery(request)[:2]
	if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (start play) "+str(data), 3)
	global newline
	newline = {}
	if ( result and 'item' in data and data['item'] ):
		item = data['item']
		getTitle=item['title']
		if getTitle=='': getTitle=item['label']
		thumbnail = item['thumbnail'].strip().rstrip('/').replace('image://','')
		thumbnail = urllib.unquote(thumbnail)
		fanart = item['fanart'].strip().rstrip('/').replace('image://','')
		fanart = urllib.unquote(fanart)
		typ = item['type']
		if typ=='unknown': typ = 'video'
		newline = {"title":getTitle,"year":item['year'],"file":item['file'].strip(), "id":item.get('id', 0), "type":typ,"thumbnail":thumbnail, "fanart":fanart}
		if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (start line) "+str(newline), 3)

def videoEnd():
	global newline
	if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (end) "+str(newline), 3)
	if newline != {}:
		retry=1
		source=''
		while source=='' and retry<50:
			source = xbmc.getInfoLabel('ListItem.Path')
			retry=retry+1
			time.sleep(0.1)
		if newline["id"]>0:
			if newline["type"]=="movie": source=lang(30002)
			elif newline["type"]=="episode": source=lang(30003)
			elif newline["type"]=="musicvideo": source=lang(30004)
			else: source=lang(30022)
		if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (end source) "+source, 3)
		if xbmcvfs.exists(txtfile):
			f = xbmcvfs.File(txtfile)
			lines = json.load(f)
			f.close()
		else: lines = []

		replay = "N"
		for line in lines:
			if newline["file"]==line["file"]:
				lines.remove(line)
				line.update({"date": time.strftime("%Y-%m-%d")})
				line.update({"time": time.strftime("%H:%M:%S")})
				lines.insert(0, line)
				replay = "S"
				if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (end final replay) "+str(line), 3)
				if fivestar	== "true": send2fivestar(line)
				break

		if replay=="N":
			newline.update({"source": source})
			newline.update({"date": time.strftime("%Y-%m-%d")})
			newline.update({"time": time.strftime("%H:%M:%S")})
			lines.insert(0, newline)
			if enable_debug	== "true": xbmc.log("<<<plugin.video.last_played (end final play) "+str(newline), 3)
			if fivestar	== "true": send2fivestar(newline)
			if len(lines)>100:
				del lines[len(lines)-1]

		if len(lines)>0:
			f = xbmcvfs.File(txtfile, 'w')
			json.dump(lines, f)
			f.close()
	newline={}

class KodiPlayer(xbmc.Player):
	def __init__(self, *args, **kwargs):
		xbmc.Player.__init__(self)

	@classmethod
	def onPlayBackStarted(self):
		videoStart()

	@classmethod
	def onPlayBackEnded(self):
		videoEnd()

	@classmethod
	def onPlayBackStopped(self):
		videoEnd()

player_monitor = KodiPlayer()

while not xbmc.abortRequested:
	xbmc.sleep(1000)

del player_monitor
