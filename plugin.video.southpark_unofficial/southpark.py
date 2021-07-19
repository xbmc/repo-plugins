#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, os
import json as _json
import random
import datetime
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import time
import base64

# .major cannot be used in older versions, like kodi 16.
IS_PY3 = sys.version_info[0] > 2

if IS_PY3:
	from urllib.request import Request
	from urllib.request import urlopen
	from urllib.parse import unquote_plus
else:
	from urllib2 import Request, urlopen
	from urllib import unquote_plus

KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion')[0:2])

if KODI_VERSION_MAJOR > 18:
	import xbmcvfs

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0'
WARNING_TIMEOUT_LONG  = 7000
WARNING_TIMEOUT_SHORT = 3000

PLUGIN_MODE_SEASON      = "sp:season"
PLUGIN_MODE_RANDOM      = "sp:random"
PLUGIN_MODE_SEARCH      = "sp:search"
PLUGIN_MODE_PLAY_EP     = "sp:play"
PLUGIN_MODE_UNAVAILABLE = "sp:unavailable"
PLUGIN_MODE_PREMIERE    = "sp:beforepremiere"
PLUGIN_MODE_CLEARCACHE  = "sp:clearcache"

def log_debug(message):
	xbmc.log("[sp.addon] {}".format(message), xbmc.LOGDEBUG)

def log_error(message):
	xbmc.log("[sp.addon] {}".format(message), xbmc.LOGERROR)

def _unescape(s):
	htmlCodes = [["'", '&#39;'],['"', '&quot;'],['', '&gt;'],['', '&lt;'],['&', '&amp;']]
	for code in htmlCodes:
		s = s.replace(code[1], code[0])
	return s

def _datetime(strdate):
	date  = time.strptime(strdate, '%Y-%m-%d %H:%M:%S.%f')
	return datetime.datetime(year=date.tm_year, \
		month=date.tm_mon, \
		day=date.tm_mday, \
		hour=date.tm_hour, \
		minute=date.tm_min, \
		second=date.tm_sec)

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

def _http_get(url, json=False):
	#log_debug("http get: {0}".format(url))
	if len(url) < 1:
		return None
	req = Request(url)
	req.add_header('User-Agent', USER_AGENT)
	response = urlopen(req)
	data = response.read()
	response.close()
	if IS_PY3:
		data = data.decode("utf-8")
	if json:
		data = _json.loads(data, strict=False)
	return data

def _decode_dictionary(string):
	newd = {}
	if string:
		tokens = string[1:].split("&")
		for pair in tokens:
			split = pair.split('=')
			if (len(split)) == 2:
				newd[split[0]] = split[1]
	return newd

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

def _dk(obj, keys, default=None):
	if not isinstance(obj, list) and not isinstance(obj, dict):
		return default
	for k in keys:
		if not isinstance(k, int) and "|" in k and isinstance(obj, list):
			t = k.split("|")
			found = None
			for o in obj:
				if t[0] not in o:
					return default
				elif o[t[0]] == t[1]:
					found = o
					break
			if found == None:
				#log_debug("not found: {}".format(k))
				return default
			obj = found
		elif isinstance(obj, dict) and k not in obj:
			#log_debug("not found: {}".format(k))
			return default
		elif isinstance(obj, list) and isinstance(k, int) and k >= len(obj):
			#log_debug("not found: {}".format(k))
			return default
		else:
			obj = obj[k]
	return obj

def _load_data(lang, path):
	path = path.format(lang)
	addon_data = None
	if os.path.isfile(path):
		try:
			with open(path, "r") as fp:
				addon_data = _json.load(fp, strict=False)
			if "date" in addon_data:
				if addon_data["date"] != None:
					now   = datetime.datetime.now()
					date  = _datetime(addon_data["date"])
					delta = now - date
					if (delta.seconds/3600) > 12:
						addon_data = None
				else:
					addon_data = None
			elif "seasons" not in addon_data or not isinstance(addon_data["seasons"], list):
				addon_data = None
		except Exception as e:
			log_error(e)
			addon_data = None

	if addon_data == None:
		url = "https://raw.githubusercontent.com/wargio/plugin.video.southpark_unofficial/addon-data/addon-data-{}.json".format(lang)
		addon_data = _http_get(url, True)
		addon_data["date"] = "{}".format(datetime.datetime.now()),

		with open(path,'w') as output:
			output.truncate()
			_json.dump(addon_data, output)

	return SP_Data(addon_data["seasons"], addon_data["created"])

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
		self.WARNING_UNAVAILABLE_EPISODE          = _translation(addon, 30011)
		self.WARNING_GEOBLOCKED                   = _translation(addon, 30002)
		self.WARNING_LOADING                      = _translation(addon, 30009)
		self.WARNING_LOADING_RANDOM_EPISODE       = _translation(addon, 30003)
		self.WARNING_PREMIERE                     = _translation(addon, 30014)


class KodiParams(object):
	"""Kodi parameters"""
	def __init__(self, param_string):
		super(KodiParams, self).__init__()
		params = _decode_dictionary(param_string)
		self.PARAM_MODE    = unquote_plus(params.get('mode'     , ''))
		self.PARAM_SEASON  = unquote_plus(params.get('season'   , ''))
		self.PARAM_EPISODE = unquote_plus(params.get('episode'  , ''))

	def debug(self):
		log_debug("PARAM_MODE:    {0}".format(self.PARAM_MODE   ))
		log_debug("PARAM_SEASON:  {0}".format(self.PARAM_SEASON ))
		log_debug("PARAM_EPISODE: {0}".format(self.PARAM_EPISODE))

class SP_Paths(object):
	"""South Park plugin Paths"""
	def __init__(self, addon_id):
		super(SP_Paths, self).__init__()
		self.PLUGIN_ICON      = self.translate_path('special://home/addons/{0}/icon.png'.format(addon_id))
		self.DEFAULT_FANART   = self.translate_path('special://home/addons/{0}/fanart.jpg'.format(addon_id))
		self.DEFAULT_IMGDIR   = self.translate_path('special://home/addons/{0}/imgs/'.format(addon_id))
		self.TEMPORARY_FOLDER = self.translate_path('special://temp/southpark')
		self.PLUGIN_DATA      = self.translate_path('special://temp/southpark/data_{}.json')
		if not os.path.isdir(self.TEMPORARY_FOLDER):
			os.mkdir(self.TEMPORARY_FOLDER, 0o755)

	def clear_cache(self):
		if KODI_VERSION_MAJOR > 18:
			dirs, files = xbmcvfs.listdir(self.TEMPORARY_FOLDER)
			for file in files:
				xbmcvfs.delete(self.TEMPORARY_FOLDER + "/" + file)
		else:
			for file in os.listdir(self.TEMPORARY_FOLDER):
				fpath = self.TEMPORARY_FOLDER + "/" + file
				if os.path.isfile(fpath):
					os.remove(fpath)

	def translate_path(self, path):
		if KODI_VERSION_MAJOR > 18:
			return xbmcvfs.translatePath(path)
		return xbmc.translatePath(path)

class SP_Options(object):
	"""South Park plugin Options"""
	def __init__(self, addon):
		super(SP_Options, self).__init__()
		self.addon = addon
		self.geolocation = ["en", "es", "de", "se", "eu", "br", "lat"]

	def debug(self):
		log_error("OPTIONS Geolocation          {0}".format(self.audio(True)))
		log_error("OPTIONS Show Subtitles       {0}".format(self.show_subtitles()))
		log_error("OPTIONS Play Random Directly {0}".format(self.playrandom()))

	def show_subtitles(self):
		return self.addon.getSetting('cc') == "true"

	def audio(self, as_string=False):
		au = int(self.addon.getSetting('audio_lang'))
		if as_string:
			return self.geolocation[au] 
		return au

	def playrandom(self):
		return self.addon.getSetting('playrandom') == "true"

class SP_Data(object):
	"""Contains the data that is needed by the addon"""
	def __init__(self, seasons, created):
		super(SP_Data, self).__init__()
		self.seasons = seasons
		self.created = created

	def random(self):
		season  = random.randint(0, len(self.seasons) - 1)
		episode = random.randint(0, len(self.seasons[season]) - 1)
		return self.seasons[season][episode]

	def episode(self, season, episode):
		return self.seasons[season][episode]

	def last_season(self):
		return len(self.seasons) + 1

class SouthParkAddon(object):
	"""South Park Addon"""
	def __init__(self, argv, addon_id='plugin.video.southpark_unofficial'):
		super(SouthParkAddon, self).__init__()
		self.addon_id  = addon_id
		self.addon_obj = xbmcaddon.Addon(id=self.addon_id)
		self.argv      = argv
		self.phandle   = int(argv[1])
		self.paths     = SP_Paths    (self.addon_id )
		self.options   = SP_Options  (self.addon_obj)
		self.i18n      = SP_I18N   (self.addon_obj)
		self.data      = _load_data(self.options.audio(True), self.paths.PLUGIN_DATA)

	def notify(self, text, utime=WARNING_TIMEOUT_SHORT):
		utext      = _encode(text)
		uicon      = _encode(self.paths.PLUGIN_ICON);
		uaddonname = _encode(self.addon_obj.getAddonInfo('name'))
		xbmcgui.Dialog().notification(uaddonname, utext, uicon, utime)

	def add_directory(self, name, season, mode, iconimage="DefaultFolder.png"):
		u = self.argv[0]+"?mode={0}&season={1}".format(mode, season)
		ok = True
		liz = xbmcgui.ListItem(name)
		if KODI_VERSION_MAJOR > 17:
			liz.setIsFolder(True)
		liz.setArt({'icon': iconimage, 'thumb': iconimage})
		liz.setInfo(type="Video", infoLabels={"Title": name})
		liz.setProperty("fanart_image", self.paths.DEFAULT_FANART)
		ok = xbmcplugin.addDirectoryItem(handle=self.phandle, url=u, listitem=liz, isFolder=True)
		return ok

	def add_entry(self, name, url, mode, iconimage, desc="", season="", episode="", date="", is_playable=False):
		name    = _encode(name)
		desc    = _encode(desc)
		if "?" in iconimage:
			pos = iconimage.index('?') - len(iconimage)
			iconimage = iconimage[:pos]
		url       = "{0}?mode={1}&season={2}&episode={3}".format(self.argv[0], mode, season, episode)
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

	def create_episodes(self, season):
		#log_debug("SEASON: {}".format(season))
		xbmcplugin.addSortMethod(self.phandle, xbmcplugin.SORT_METHOD_EPISODE)
		for episode in self.data.seasons[int(season) - 1]:
			self.add_episode(episode)
		xbmcplugin.endOfDirectory(self.phandle)

	def add_episode(self, episode):
		ep_mode    = PLUGIN_MODE_PLAY_EP

		ep_title   = _encode(episode['title'])
		ep_image   = _encode(episode['image'])
		ep_desc    = _encode(episode['details'])
		ep_seas    = episode["season"]
		ep_numb    = episode["episode"]
		ep_aird    = episode['date']
		ep_uuid    = episode['uuid']

		if len(episode['mediagen']) < 1:
			ep_title += " [Unavailable]"
			ep_mode = PLUGIN_MODE_UNAVAILABLE

		self.add_entry(ep_title, ep_uuid, ep_mode, ep_image, ep_desc, ep_seas, ep_numb, ep_aird, is_playable=True)

	def create_menu(self):
		self.add_entry    (self.i18n.MENU_RANDOM_EPISODE   , '', PLUGIN_MODE_RANDOM  , self.paths.PLUGIN_ICON, is_playable=self.options.playrandom())
		#self.add_entry    (self.i18n.MENU_SEARCH_EPISODE   , '', PLUGIN_MODE_SEARCH  , self.paths.PLUGIN_ICON)
		for i in range(1, self.data.last_season()):
			dirname  = "{0} {1}".format(self.i18n.MENU_SEASON_EPISODE, i)
			iconpath = "{0}{1}.jpg".format(self.paths.DEFAULT_IMGDIR, i)
			self.add_directory(dirname, str(i), PLUGIN_MODE_SEASON, iconpath)
		xbmcplugin.endOfDirectory(self.phandle)

	def create_random(self):
		if not self.options.playrandom():
			self.notify(self.i18n.WARNING_LOADING_RANDOM_EPISODE, WARNING_TIMEOUT_SHORT)
		retries = 0
		while retries < 10:
			retries += 1
			episode_data = self.data.random()
			if len(episode_data['mediagen']) < 1:
				log_error("Found locked episode '{0}'. trying again!".format(episode_data["title"]))
				continue
			if self.options.playrandom():
				self.play_episode(episode_data['season'], episode_data['episode'])
			else:
				self.add_episode(episode_data)
			break
		if retries > 9:
			log_error("Cannot find an episode to play!")
		xbmcplugin.endOfDirectory(self.phandle)


	def play_episode(self, season, episode):
		data = self.data.episode(int(season) - 1, int(episode) - 1)
		self.notify("{0} {1}".format(self.i18n.WARNING_LOADING, _encode(data["title"])), WARNING_TIMEOUT_SHORT)
		streams   = []
		subtitles = []
		try:
			for url in data["mediagen"]:
				url = base64.b64decode(url.encode('ascii')).decode('ascii')
				mediagen = _http_get(url, True)

				subs = _dk(mediagen, ["package", "video", "item", 0, "transcript", 0, "typographic"], [])
				subs = list(filter(lambda x: "format" in x and x["format"] == "vtt", subs))
				if len(subs) > 0:
					subtitles.append(subs[0]["src"])
				else:
					subtitles.append(None)

				m3u8 = None
				try:
					m3u8 = _dk(mediagen, ["package", "video", "item", 0, "rendition", "src"], None)
				except TypeError:
					m3u8 = _dk(mediagen, ["package", "video", "item", 0, "rendition", 0, "src"], None)

				if m3u8 == None:
					raise Exception("invalid m3u8")
				streams.append(m3u8)
		except Exception as e:
			streams = []
			log_error(e)

		if len(streams) < 1:
			self.notify(self.i18n.WARNING_UNAVAILABLE_EPISODE, WARNING_TIMEOUT_LONG)
			xbmcplugin.endOfDirectory(self.phandle)
			return

		playlist = None
		parts = len(streams)
		if parts > 1:
			playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
			playlist.clear()

		firstitem = None
		show_subs = self.options.show_subtitles()
		for i in range(0, parts):
			playitem = xbmcgui.ListItem(path=streams[i])
			title = data["title"].encode("utf-8")
			if len(streams) > 1:
				title = "{title} ({i}/{n})".format(title=title, i=(i + 1), n=parts)

			playitem.setArt({'icon': data["image"], 'thumb': data["image"]})
			playitem.setInfo('video', {'Title': title, 'Plot': data["details"]})

			if subtitles[i] != None and show_subs:
				playitem.setSubtitles([subtitles[i]])

			if i == 0:
				firstitem = playitem
			if playlist != None:
				playlist.add(url=streams[i], listitem=playitem, index=i)

		player = xbmc.Player()
		player.showSubtitles(show_subs)
		if self.phandle == -1:
			## this could be removed..
			if playlist != None:
				player.play(playlist)
			else:
				player.play(listitem=firstitem)
		else:
			xbmcplugin.setResolvedUrl(handle=self.phandle, succeeded=True, listitem=firstitem)
		xbmcplugin.endOfDirectory(self.phandle)


	def handle(self):
		kodi = KodiParams(self.argv[2])
		##kodi.debug()
		##self.options.debug()
		if   kodi.PARAM_MODE == PLUGIN_MODE_SEASON:
			self.create_episodes(kodi.PARAM_SEASON)
			return
		elif kodi.PARAM_MODE == PLUGIN_MODE_PLAY_EP:
			self.play_episode(kodi.PARAM_SEASON, kodi.PARAM_EPISODE)
			return
		elif kodi.PARAM_MODE == PLUGIN_MODE_RANDOM:
			self.create_random()
			return
		#elif kodi.PARAM_MODE == PLUGIN_MODE_SEARCH:
		#	self.create_search()
		elif kodi.PARAM_MODE == PLUGIN_MODE_UNAVAILABLE:
			self.notify(self.i18n.WARNING_UNAVAILABLE_EPISODE, WARNING_TIMEOUT_LONG)
		elif kodi.PARAM_MODE == PLUGIN_MODE_PREMIERE:
			self.notify(self.i18n.WARNING_PREMIERE, WARNING_TIMEOUT_LONG)
		elif kodi.PARAM_MODE == PLUGIN_MODE_CLEARCACHE:
			self.paths.clear_cache()
		elif kodi.PARAM_MODE == '':
			self.create_menu()
		else:
			self.notify("---ERROR---")
			return
