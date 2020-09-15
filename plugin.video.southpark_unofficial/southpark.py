#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os
import json as _json
import time
import datetime
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import xml.etree.ElementTree as ET
import random

# .major cannot be used in older versions, like kodi 16.
IS_PY3 = sys.version_info[0] > 2

if IS_PY3:
	from urllib.request import Request
	from urllib.request import urlopen
	from urllib.parse import unquote_plus, quote_plus
else:
	from urllib2 import Request, urlopen
	from urllib import unquote_plus, quote_plus

KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion')[0:2])

SP_SEASONS_EPS = [
	13,18,17,17,14,
	17,15,14,14,14,
	14,14,14,14,14,
	14,10,10,10,10,
	10,10,10
]

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0'
WARNING_TIMEOUT_LONG  = 7000
WARNING_TIMEOUT_SHORT = 3000

PLUGIN_MODE_SEASON     = "sp:season"
PLUGIN_MODE_FEATURED   = "sp:featured"
PLUGIN_MODE_RANDOM     = "sp:random"
PLUGIN_MODE_SEARCH     = "sp:search"
PLUGIN_MODE_PLAY_EP    = "sp:play"
PLUGIN_MODE_BANNED     = "sp:banned"
PLUGIN_MODE_PREMIERE   = "sp:beforepremiere"

def _unescape(s):
	htmlCodes = [["'", '&#39;'],['"', '&quot;'],['', '&gt;'],['', '&lt;'],['&', '&amp;']]
	for code in htmlCodes:
		s = s.replace(code[1], code[0])
	return s

def _date(string):
	if string != "":
		try:
			return datetime.datetime.fromtimestamp(int(string)).strftime('%Y-%m-%d %H:%M:%S')
		except:
			pass
	return string

def _encode(string):
	if IS_PY3:
		if isinstance(string, (bytes, bytearray)):
			return string.decode("utf-8")
		return string
	try:
		return string.encode('UTF-8','replace')
	except UnicodeError:
		return string

def _translation(addon, id):
	return _encode(addon.getLocalizedString(id))

def _premier_timeout(premiere):
	try:
		diff = int(premiere) - int(time.time())
	except ValueError:
		date = time.strptime(premiere, "%d.%m.%Y") # 30.09.2015
		diff = int(time.mktime(date)) - int(time.time())
		
	if diff < 0:
		diff = 0;
	days = int(diff / 86400)
	hours = int((diff % 86400) / 3600)
	mins =  int((diff % 3600) / 60)
	if KODI_VERSION_MAJOR < 17:
		return "%02dd %02dh %02dm".format(days, hours, mins)
	return "{:02d}d {:02d}h {:02d}m".format(days, hours, mins)

def log_debug(message):
	xbmc.log("[sp.addon] {0}".format(message), xbmc.LOGDEBUG)

def log_error(message):
	xbmc.log("[sp.addon] {0}".format(message), xbmc.LOGERROR)

def _http_get(url):
	#log_debug("http get: {0}".format(url))
	if len(url) < 1:
		return None
	req = Request(url)
	req.add_header('User-Agent', USER_AGENT)
	response = urlopen(req)
	link = response.read()
	response.close()
	if IS_PY3:
		link = link.decode("utf-8")
	return link

def _parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def _save_subs(fname, stream):
	data = _unescape(_http_get(stream))
	if IS_PY3:
		data = data.encode("utf-8")
	output = open(fname,'wb')
	output.truncate()
	output.write(data)
	output.close()
	#log_debug("Saved subtitle {0}.".format(fname))
	return stream

class SP_Paths(object):
	"""South Park plugin Paths"""
	def __init__(self, addon_id):
		super(SP_Paths, self).__init__()
		self.PLUGIN_ICON      = xbmc.translatePath('special://home/addons/{0}/icon.png'.format(addon_id))
		self.DEFAULT_FANART   = xbmc.translatePath('special://home/addons/{0}/fanart.jpg'.format(addon_id))
		self.DEFAULT_IMGDIR   = xbmc.translatePath('special://home/addons/{0}/imgs/'.format(addon_id))
		self.TEMPORARY_FOLDER = xbmc.translatePath('special://temp/southpark')
		if not os.path.isdir(self.TEMPORARY_FOLDER):
			os.mkdir(self.TEMPORARY_FOLDER, 0o755)

class KodiParams(object):
	"""docstring for KodiParams"""
	def __init__(self, param_string):
		super(KodiParams, self).__init__()
		params = _parameters_string_to_dict(param_string)
		self.PARAM_MODE         = unquote_plus(params.get('mode'     , ''))
		self.PARAM_URL          = unquote_plus(params.get('url'      , ''))
		self.PARAM_EP_TITLE     = unquote_plus(params.get('title'    , ''))
		self.PARAM_EP_THUMBNAIL = unquote_plus(params.get('thumbnail', ''))
		self.PARAM_EP_WEBPAGE   = unquote_plus(params.get('webpage'  , ''))

	def debug(self):
		log_debug("PARAM_MODE:         {0}".format(self.PARAM_MODE        ))
		log_debug("PARAM_URL:          {0}".format(self.PARAM_URL         ))
		log_debug("PARAM_EP_TITLE:     {0}".format(self.PARAM_EP_TITLE    ))
		log_debug("PARAM_EP_THUMBNAIL: {0}".format(self.PARAM_EP_THUMBNAIL))
		log_debug("PARAM_EP_WEBPAGE:   {0}".format(self.PARAM_EP_WEBPAGE))
		

class SP_I18N(object):
	"""South Park plugin I18N"""
	def __init__(self, addon):
		super(SP_I18N, self).__init__()
		self.ERROR_NO_INTERNET_CONNECTION         = _translation(addon, 30004)
		self.MENU_FEATURED_EPISODES               = _translation(addon, 30005)
		self.MENU_RANDOM_EPISODE                  = _translation(addon, 30006)
		self.MENU_SEARCH_EPISODE                  = _translation(addon, 30013)
		self.MENU_SEASON_EPISODE                  = _translation(addon, 30007)
		self.OPTIONS_AUDIO_LANGUAGE               = _translation(addon, 30000)
		self.OPTIONS_ENABLE_CC                    = _translation(addon, 30012)
		self.OPTIONS_GEOLOCATION                  = _translation(addon, 30001)
		self.OPTIONS_PLAY_DIRECTLY_RANDOM_EPISODE = _translation(addon, 30015)
		self.WARNING_BAD_INTERNET_CONNECTION      = _translation(addon, 30010)
		self.WARNING_BANNED_EPISODE               = _translation(addon, 30011)
		self.WARNING_GEOBLOCKED                   = _translation(addon, 30002)
		self.WARNING_LOADING                      = _translation(addon, 30009)
		self.WARNING_LOADING_RANDOM_EPISODE       = _translation(addon, 30003)
		self.WARNING_PREMIERE                     = _translation(addon, 30014)

class SP_Options(object):
	"""South Park plugin Options"""
	def __init__(self, addon):
		super(SP_Options, self).__init__()
		self.addon = addon
		self.GEO_LOCATIONS   = ["US","UK","ES","DE","IT","SE"]
		self.AUDIO_AVAILABLE = ["en","es","de","se"]
		self.VIDEO_QUALITY   = ["high","low"]

	def debug(self):
		log_debug("OPTIONS Geolocation          {0}".format(self.geolocation(True)))
		log_debug("OPTIONS Audio                {0}".format(self.audio(True)))
		log_debug("OPTIONS Show Subtitles       {0}".format(self.show_subtitles()))
		log_debug("OPTIONS Play Random Directly {0}".format(self.playrandom()))

	def geolocation(self, as_string=False):
		geo = int(self.addon.getSetting('geolocation'))
		if as_string:
			return self.GEO_LOCATIONS[geo] 
		return geo

	def show_subtitles(self):
		return self.addon.getSetting('cc') == "true"

	def audio(self, as_string=False):
		au = int(self.addon.getSetting('audio_lang'))
		if as_string:
			return self.AUDIO_AVAILABLE[au] 
		return au

	def playrandom(self):
		return self.addon.getSetting('playrandom') == "true"

class SP_Helper(object):
	"""South Park Helper"""
	def __init__(self, options):
		super(SP_Helper, self).__init__()
		self.options = options
		self.PROTO_REF = [
			"https", ## en
			"https", ## es
			"https", ## de
			"https"  ## se
		]
		self.DOMAIN_REF = [
			"southpark.cc.com",    ## en
			"southpark.cc.com",    ## es
			"www.southpark.de",    ## de
			"southparkstudios.nu"  ## se
		]
		self.DOMAIN_URL = [
			"southparkstudios.com", ## en
			"southparkstudios.com", ## es
			"southpark.de",         ## de
			"southparkstudios.nu"   ## se
		]
		self.FULL_EPISODES = [
			"/full-episodes/",        ## en
			"/episodios-en-espanol/", ## es
			"/alle-episoden/",        ## de
			"/full-episodes/"         ## se
		]
		self.MEDIAGEN = [
			"player",       ## en
			"player",       ## es
			"video-player", ## de
			"player"        ## se
		]
		self.MEDIAGEN_OPTS = [
			"&suppressRegisterBeacon=true&lang=",   ## en
			"&suppressRegisterBeacon=true&lang=",   ## es
			"&device=Other&aspectRatio=16:9&lang=", ## de
			"&suppressRegisterBeacon=true&lang="    ## se
		]
		self.RTMP_STREAMS = [
			"rtmpe://viacommtvstrmfs.fplive.net:1935/viacommtvstrm",
			"rtmpe://cp75298.edgefcs.net/ondemand"
		]

	def proto_ref(self):
		return self.PROTO_REF[self.options.audio()]

	def domain_ref(self):
		return self.DOMAIN_REF[self.options.audio()]

	def domain_url(self):
		return self.DOMAIN_URL[self.options.audio()]

	def full_episodes(self):
		return self.FULL_EPISODES[self.options.audio()]

	def mediagen(self):
		return self.MEDIAGEN[self.options.audio()]

	def mediagen_opts(self):
		return self.MEDIAGEN_OPTS[self.options.audio()]

	def rtmp_streams(self, index=0):
		return self.RTMP_STREAMS[index]

	def page_url(self, url):
		geolocation = self.options.geolocation()
		reference   = self.domain_ref()
		episode_dom = self.domain_url()
		fmt =  "http://media.mtvnservices.com/player/prime/mediaplayerprime.2.12.5.swf?uri=mgid:arc:episode:{domain_url}:{url}"
		fmt += "&type=network&ref=southpark.cc.com&geo={geolocation}&group=entertainment&network=None&device=Other&networkConnectionType=None"
		fmt += "&CONFIG_URL=http://media.mtvnservices.com/pmt-arc/e1/players/mgid:arc:episode:{domain_url}:/context4/config.xml"
		fmt += "?uri=mgid:arc:episode:{domain_url}:{url}&type=network&ref={domain_ref}&geo={geolocation}"
		fmt += "&group=entertainment&network=None&device=Other&networkConnectionType=None"
		return fmt.format(domain_url=episode_dom, url=url, geolocation=geolocation, domain_ref=reference)

	def flash_version(self):
		return "WIN 24,0,0,186"

	def swf_player(self):
		return "http://media.mtvnservices.com/player/prime/mediaplayerprime.2.12.5.swf"

	def swf_verify(self):
		return "true"

	def carousel(self):
		if self.options.geolocation(True) == "DE":
			return "{0}://www.southpark.de/feeds/carousel/video/e3748950-6c2a-4201-8e45-89e255c06df1/30/1/json".format(self.proto_ref())
		elif self.options.geolocation(True) == "SE":
			return "{0}://www.southparkstudios.nu/feeds/carousel/wiki/3fb9ffcb-1f70-42ed-907d-9171091a28f4/12/1/json".format(self.proto_ref())
		elif self.options.geolocation(True) == "UK":
			return "{0}://www.southparkstudios.co.uk/feeds/carousel/wiki/4d56eb84-60d9-417e-9550-31bbfa1e7fb9/12/1/json".format(self.proto_ref())
		return "{0}://southpark.cc.com/feeds/carousel/video/2b6c5ab4-d717-4e84-9143-918793a3b636/14/2/json/!airdate/?lang={1}".format(self.proto_ref(), self.options.audio(True))

	def random_episode(self, suburl=""):
		return "{0}://{1}{2}{3}".format(self.proto_ref(), self.domain_ref(), self.full_episodes(), suburl)

	def mediagen_url(self, identifier):
		if self.options.audio(True) == "se":
			return "https://media.mtvnservices.com/pmt/e1/access/index.html?uri=mgid:arc:episode:{0}:{1}&configtype=edge".format(self.domain_url(), identifier)
		return "{0}://{1}/feeds/video-player/mrss/mgid:arc:episode:{2}:{3}?lang={4}".format(self.proto_ref(), self.domain_ref(), self.domain_url(), identifier, self.options.audio(True))

	def search(self, text):
		return "{0}://southpark.cc.com/feeds/carousel/search/81bc07c7-07bf-4a2c-a128-257d0bc0f4f7/14/1/json/{1}".format(self.proto_ref(), text)

	def season_data(self, season):
		if self.options.audio(True) == "de":
			return "{0}://www.southpark.de/feeds/carousel/video/e3748950-6c2a-4201-8e45-89e255c06df1/30/1/json/!airdate/season-{1}".format(self.proto_ref(), season)
		elif self.options.geolocation(True) == "SE" and season < 23: # SE doesn't have the 23rd season.
			return "{0}://www.southparkstudios.nu/feeds/carousel/video/9bbbbea3-a853-4f1c-b5cf-dc6edb9d4c00/30/1/json/!airdate/season-{1}".format(self.proto_ref(), season)
		elif self.options.geolocation(True) == "UK":
			return "{0}://www.southparkstudios.co.uk/feeds/carousel/video/02ea1fb4-2e7c-45e2-ad42-ec8a04778e64/30/1/json/!airdate/season-{1}".format(self.proto_ref(), season)
		# cc.com is the ony one with jsons so descriptions will be in english
		return "{0}://southpark.cc.com/feeds/carousel/video/06bb4aa7-9917-4b6a-ae93-5ed7be79556a/30/1/json/!airdate/season-{1}?lang={2}".format(self.proto_ref(), season, self.options.audio(True))

class Video(object):
	"""Video data"""
	def __init__(self, streams, duration, captions):
		super(Video, self).__init__()
		self.streams  = streams
		self.duration = duration
		self.captions = captions

	def play_data(self, helper):
		## High quality is the last stream  (-1)
		vqual = -1
		rtmp  = self.streams[vqual]
		playpath = ""
		if not "http" in rtmp:
			if "viacomccstrm" in self.streams[vqual]:
				playpath = "mp4:{0}".format(self.streams[vqual].split('viacomccstrm/')[1])
				rtmp =  helper.rtmp_streams()
			elif "cp9950.edgefcs.net" in self.streams[vqual]:
				playpath = "mp4:{0}".format(self.streams[vqual].split('mtvnorigin/')[1])
				rtmp =  helper.rtmp_streams()
		return playpath, rtmp

class SouthParkAddon(object):
	"""South Park Addon"""
	def __init__(self, argv, last_season, addon_id='plugin.video.southpark_unofficial'):
		super(SouthParkAddon, self).__init__()
		self.addon_id  = addon_id
		self.addon_obj = xbmcaddon.Addon(id=self.addon_id)
		self.argv      = argv
		self.phandle   = int(argv[1])
		self.seasons   = last_season + 1
		self.options = SP_Options(self.addon_obj)
		self.i18n    = SP_I18N   (self.addon_obj)
		self.helper  = SP_Helper (self.options  )
		self.paths   = SP_Paths  (self.addon_id )

	def notify(self, text, utime=WARNING_TIMEOUT_SHORT):
		utext = _encode(text)
		uaddonname = _encode(self.addon_obj.getAddonInfo('name'))
		uicon = _encode(self.paths.PLUGIN_ICON);
		xbmcgui.Dialog().notification(uaddonname, utext, uicon, utime)

	def create_menu(self):
		#xbmcplugin.addSortMethod(self.phandle, xbmcplugin.SORT_METHOD_LABEL)
		content = _http_get("http://{0}".format(self.helper.domain_ref()))
		if "/messages/geoblock/" in content or "/geoblock/messages/" in content:
			self.notify(self.i18n.WARNING_GEOBLOCKED, WARNING_TIMEOUT_LONG)
		
		self.add_directory(self.i18n.MENU_FEATURED_EPISODES, '', PLUGIN_MODE_FEATURED, self.paths.PLUGIN_ICON)
		self.add_entry    (self.i18n.MENU_RANDOM_EPISODE   , '', PLUGIN_MODE_RANDOM  , self.paths.PLUGIN_ICON, is_playable=self.options.playrandom())
		self.add_entry    (self.i18n.MENU_SEARCH_EPISODE   , '', PLUGIN_MODE_SEARCH  , self.paths.PLUGIN_ICON)
		for i in range(1, self.seasons):
			dirname  = "{0} {1}".format(self.i18n.MENU_SEASON_EPISODE, i)
			iconpath = "{0}{1}.jpg".format(self.paths.DEFAULT_IMGDIR, i)
			self.add_directory(dirname, str(i), PLUGIN_MODE_SEASON, iconpath)
		xbmcplugin.endOfDirectory(self.phandle)

	def create_featured(self):
		jsonrsp = _http_get(self.helper.carousel())
		promojson = _json.loads(jsonrsp)
		for episode in promojson['results']:
			self.add_episode(episode)

	def create_random(self):
		if not self.options.playrandom():
			self.notify(self.i18n.WARNING_LOADING_RANDOM_EPISODE, WARNING_TIMEOUT_SHORT)
		retries = 0
		while retries < 10:
			retries += 1
			season  = random.randint(0, len(SP_SEASONS_EPS))
			episode = random.randint(0, SP_SEASONS_EPS[season])
			jsonrsp = _http_get(self.helper.season_data(season + 1))
			jsonrsp = _encode(jsonrsp)
			seasonjson = _json.loads(jsonrsp)
			if episode >= len(seasonjson['results']):
				episode = len(seasonjson['results']) - 1
			episode_data = seasonjson['results'][episode]
			if episode_data['_availability'] == "banned":
				log_error("Found banned episode s{0}e{1}. trying again!".format(season, episode))
				continue
			elif episode_data['_availability'] == "beforepremiere":
				log_error("Found premiere episode s{0}e{1}. trying again!".format(season, episode))
				continue
			if self.options.playrandom():
				self.play_episode(episode_data['itemId'], episode_data['title'], episode_data['images'], episode_data['_url']['default'])
			else:
				self.add_episode(episode_data)
			break
		if retries > 9:
			log_error("Cannot find an episode to play!")

	def create_search(self):
		keyboard = xbmc.Keyboard('')
		keyboard.doModal()
		if (keyboard.isConfirmed()):
			text = keyboard.getText().lower()
			jsonrsp = _http_get(self.helper.search(text.replace(' ', '+')))
			xbmcplugin.addSortMethod(self.phandle, xbmcplugin.SORT_METHOD_EPISODE)
			seasonjson = _json.loads(jsonrsp)
			for episode in seasonjson['results']:
				self.add_episode(episode)

	def create_episodes(self, season):
		xbmcplugin.addSortMethod(self.phandle, xbmcplugin.SORT_METHOD_EPISODE)
		jsonrsp = _http_get(self.helper.season_data(season))
		jsonrsp = _encode(jsonrsp)
		seasonjson = _json.loads(jsonrsp)
		for episode in seasonjson['results']:
			self.add_episode(episode)

	def play_episode(self, url, title, thumbnail, webpage):
		## maybe a firewall is checking if we are loading the episode webpage.
		_http_get(webpage)

		mediagen = self.get_mediagen(url)
		if len(mediagen) < 1 or (self.options.audio(True) == "de" and len(mediagen) <= 1):
			self.notify(self.i18n.WARNING_BANNED_EPISODE, WARNING_TIMEOUT_LONG)
			return

		self.notify("{0} {1}".format(self.i18n.WARNING_LOADING, _encode(title)), WARNING_TIMEOUT_SHORT)
		parts = len(mediagen)
		player = xbmc.Player()
		ccs = []
		playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
		playlist.clear()
		start_listitem = None
		i = 0
		for media in mediagen:
			video = self.get_video_data(media)
			if len(video.streams) == 0:
				parts = len(mediagen) - 1
				continue

			playpath, rtmp = video.play_data(self.helper)

			videoname = "{title} ({i} of {n})".format(title=title, i=(i + 1), n=parts)
			li = xbmcgui.ListItem(videoname)
			li.setArt({'icon': thumbnail, 'thumb': thumbnail})
			li.setInfo('video', {'Title': videoname})
			li.setProperty('conn', "B:0")
			if not "http" in rtmp:
				if playpath != "":
					li.setProperty('PlayPath', playpath)
				li.setProperty('flashVer',  self.helper.flash_version())
				li.setProperty('pageUrl',   self.helper.page_url(url))
				li.setProperty('SWFPlayer', self.helper.swf_player())
				li.setProperty("SWFVerify", self.helper.swf_verify())
			li.setPath(rtmp)
			if video.captions != "" and self.options.show_subtitles():
				fname = os.path.join(self.paths.TEMPORARY_FOLDER, "subtitle_{0}_{1}.vtt".format(i, parts))
				subname = _save_subs(fname, video.captions)
				if subname != "":
					ccs.append(subname)
			playlist.add(url=rtmp, listitem=li, index=i)
			if i == 0:
				start_listitem = li
			i += 1

		if self.phandle == -1:
			## this could be removed..
			player.play(playlist)
		else:
			xbmcplugin.setResolvedUrl(handle=self.phandle, succeeded=True, listitem=start_listitem)

		for s in range(1):
			if player.isPlaying():
				break
			time.sleep(1)

		if not player.isPlaying():
			self.notify(self.i18n.ERROR_NO_INTERNET_CONNECTION, WARNING_TIMEOUT_SHORT)
			player.stop()

		pos = -1
		if pos != playlist.getposition():
			pos = playlist.getposition()
			if self.options.show_subtitles() and len(ccs) >= playlist.size():
				player.setSubtitles(ccs[pos])
				player.showSubtitles(self.options.show_subtitles())
			else:
				log_error("[{0}] missing some vtt subs...".format(self.addon_id))

		while pos < playlist.size() and player.isPlaying():
			while player.isPlaying():
				time.sleep(0.05)
				if pos != playlist.getposition():
					pos = playlist.getposition()
					if self.options.show_subtitles() and len(ccs) >= playlist.size():
						player.setSubtitles(ccs[pos])
						player.showSubtitles(self.options.show_subtitles())
					else:
						log_error("[{0}] missing some vtt subs...".format(self.addon_id))
			time.sleep(10)
		return

	def get_video_data(self, mediagen):
		xml = ""
		if self.options.audio(True) != "de":
			mediagen = mediagen.replace('device={device}', 'device=Android&deviceOsVersion=4.4.4&acceptMethods=hls')
		else:
			mediagen = mediagen.replace('device={device}', 'acceptMethods=hls')
		xml = _http_get(mediagen)
		root = ET.fromstring(xml)
		rtmpe = []
		duration = []
		captions = ""
		if sys.version_info >=  (2, 7):
			for item in root.iter('src'):
				if item.text != None and not "intros" in item.text:
					if self.options.audio(True) == "es":
						rtmpe.append(item.text)
					elif not "acts/es" in item.text:
						rtmpe.append(item.text)
			for item in root.iter('rendition'):
				if item.attrib['duration'] != None:
					duration.append(int(item.attrib['duration']))
			for item in root.iter('typographic'):
				if item.attrib['src'] != None and item.attrib['format'] == "vtt":
					captions = item.attrib['src']
		else:
			for item in root.getiterator('src'):
				if item.text != None and not "intros" in item.text:
					if self.options.audio(True) == "es":
						rtmpe.append(item.text)
					elif not "acts/es" in item.text:
						rtmpe.append(item.text)
			for item in root.getiterator('rendition'):
				if item.attrib['duration'] != None:
					duration.append(int(item.attrib['duration']))
			for item in root.getiterator('typographic'):
				if item.attrib['src'] != None and item.attrib['format'] == "vtt":
					captions = item.attrib['src']
		return Video(rtmpe, duration, captions)

	def get_mediagen(self, identifier):
		mediagen = []
		comp = self.helper.mediagen_url(identifier)
		feed = _http_get(comp)
		if self.options.audio(True) == "se":
			jsondata = _json.loads(feed)
			for media in jsondata["feed"]["items"]:
				mediagen.append(media["group"]["content"])
		else:
			root = ET.fromstring(feed)
			if sys.version_info >=  (2, 7):
				for item in root.iter('{http://search.yahoo.com/mrss/}content'):
					if item.attrib['url'] != None:
						mediagen.append(_unescape(item.attrib['url']))
			else:
				for item in root.getiterator('{http://search.yahoo.com/mrss/}content'):
					if item.attrib['url'] != None:
						mediagen.append(_unescape(item.attrib['url']))
		return mediagen


	def add_episode(self, episode):
		ep_url   = "invalid"
		ep_mode  = PLUGIN_MODE_PLAY_EP

		ep_title   = _encode(episode['title'])
		ep_image   = _encode(episode['images'])
		ep_desc    = _encode(episode['description'])
		ep_seas    = episode['episodeNumber'][0] + episode['episodeNumber'][1] ## SEASON  NUMBER
		ep_numb    = episode['episodeNumber'][2] + episode['episodeNumber'][3] ## EPISODE NUMBER
		ep_aird    = episode['originalAirDate']
		ep_webpage = _encode(episode['_url']['default'])

		if episode['_availability'] == "banned":
			ep_title += " [Banned]"
			ep_mode   = PLUGIN_MODE_BANNED
		elif episode['_availability'] == "beforepremiere":
			ep_title += " [Premiere]"
			ep_mode   = PLUGIN_MODE_PREMIERE
			ep_desc   = "Premiere in {0}\n{1}".format(_premier_timeout(ep_aird), ep_desc)
		else:
			ep_url = episode['itemId']

		self.add_entry(ep_title, ep_url, ep_mode, ep_image, ep_desc, ep_seas, ep_numb, ep_aird, ep_webpage, is_playable=True)

	def add_directory(self, name, url, mode, iconimage="DefaultFolder.png"):
		u = self.argv[0]+"?url="+quote_plus(url)+"&mode="+str(mode)
		ok = True
		liz = xbmcgui.ListItem(name)
		if KODI_VERSION_MAJOR > 17:
			liz.setIsFolder(True)
		liz.setArt({'icon': iconimage, 'thumb': iconimage})
		liz.setInfo(type="Video", infoLabels={"Title": name})
		liz.setProperty("fanart_image", self.paths.DEFAULT_FANART)
		ok = xbmcplugin.addDirectoryItem(handle=self.phandle, url=u, listitem=liz, isFolder=True)
		return ok

	def add_entry(self, name, url, mode, iconimage, desc="", season="", episode="", date="", webpage="", is_playable=False):
		name    = _encode(name)
		desc    = _encode(desc)
		webpage = _encode(webpage)
		if "?" in iconimage:
			pos = iconimage.index('?') - len(iconimage)
			iconimage = iconimage[:pos]
		url       = "{0}?url={1}&mode={2}&title={3}&thumbnail={4}&webpage={5}".format(self.argv[0], quote_plus(url), mode, quote_plus(name), iconimage, quote_plus(webpage))
		convdate  = _date(date)
		is_folder = not is_playable
		entry = xbmcgui.ListItem(name)
		if KODI_VERSION_MAJOR > 17:
			entry.setIsFolder(is_folder)
		entry.setArt({'thumb': iconimage})
		entry.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Season": season, "Episode": episode, "Aired": convdate})
		entry.setProperty("fanart_image", self.paths.DEFAULT_FANART)
		entry.setProperty("isPlayable", "true" if is_playable else "false")
		xbmcplugin.setContent(self.phandle, 'episodes')
		return xbmcplugin.addDirectoryItem(handle=self.phandle, url=url, listitem=entry, isFolder=is_folder)

	def handle(self):
		kodi = KodiParams(self.argv[2])
		##kodi.debug()
		##self.options.debug()
		if kodi.PARAM_MODE == PLUGIN_MODE_SEASON:
			self.create_episodes(kodi.PARAM_URL)
		elif kodi.PARAM_MODE == PLUGIN_MODE_PLAY_EP:
			self.play_episode(kodi.PARAM_URL, kodi.PARAM_EP_TITLE, kodi.PARAM_EP_THUMBNAIL, kodi.PARAM_EP_WEBPAGE)
		elif kodi.PARAM_MODE == PLUGIN_MODE_FEATURED:
			self.create_featured()
		elif kodi.PARAM_MODE == PLUGIN_MODE_RANDOM:
			self.create_random()
		elif kodi.PARAM_MODE == PLUGIN_MODE_SEARCH:
			self.create_search()
		elif kodi.PARAM_MODE == PLUGIN_MODE_BANNED:
			self.notify(self.i18n.WARNING_BANNED_EPISODE, WARNING_TIMEOUT_LONG)
		elif kodi.PARAM_MODE == PLUGIN_MODE_PREMIERE:
			self.notify(self.i18n.WARNING_PREMIERE, WARNING_TIMEOUT_LONG)
		elif kodi.PARAM_MODE == '':
			self.create_menu()
		else:
			self.notify("---ERROR---")
			return
		xbmcplugin.endOfDirectory(self.phandle)
