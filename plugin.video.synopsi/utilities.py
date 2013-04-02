# xbmc
import xbmc, xbmcgui, xbmcaddon, xbmcplugin, xbmcvfs
import CommonFunctions

# python standart lib
import json
import struct
import os
import urllib
import urlparse
import hashlib
import uuid
import threading
import traceback
import re
from base64 import b64encode
from urllib import urlencode
from urllib2 import Request, urlopen
from copy import copy
import time
import sys
import xml.etree.ElementTree as et

# application
import resources.const
import top

common = CommonFunctions
common.plugin = "SynopsiTV"


__addon__  = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('name')
__addonpath__	= __addon__.getAddonInfo('path')
__author__  = __addon__.getAddonInfo('author')
VERSION   = __addon__.getAddonInfo('version')
__profile__      = xbmc.translatePath(__addon__.getAddonInfo('profile'))
__lockLoginScreen__ = threading.Lock()

# constant
BTN_SHOW_ALL_MOVIES = os.path.join(__addonpath__, 'resources', 'skins', 'Default', 'media', 'show_all_button.png')
CANCEL_DIALOG = (9, 10, 92, 216, 247, 257, 275, 61467, 61448)
CANCEL_DIALOG2 = (61467, )
HACK_SHOW_ALL_LOCAL_MOVIES = -1
SEARCH_RESULT_LIMIT = 15


# api request title properties
reccoDefaultProps = ['id', 'cover_medium', 'name', 'type', 'watched', 'year']
defaultDetailProps = ['id', 'cover_full', 'cover_large', 'cover_medium', 'cover_small', 'cover_thumbnail', 'date', 'genres', 'url', 'name', 'plot', 'released', 'trailer', 'type', 'year', 'directors', 'writers', 'runtime', 'cast']
tvshowdefaultDetailProps = defaultDetailProps + ['seasons']
defaultCastProps = ['name']

homeReccoLimit = 5
reccoDefaulLimit = 29
type2listinglabel = { 'movie': 'Similar movies', 'tvshow': 'Seasons'}

list_filter = reccoDefaultProps + ['type', 'id', 'stvId', 'xbmc_id', 'name', 'file']

item_show_all_movies_hack = { 'id': HACK_SHOW_ALL_LOCAL_MOVIES, 'cover_medium': BTN_SHOW_ALL_MOVIES, 'name': '', 'type': 'HACK'}

#	enums
class OverlayCode:
	Empty = 0
	OnYourDisk = 1
	AlreadyWatched = 2
	AlreadyWatchedOnYourDisk = 3	#	this is just to know the code, it should be created by addition of the two


class ActionCode:
	MovieRecco = 10
	LocalMovieRecco = 15
	LocalMovies = 16
	TVShows = 20
	LocalTVShows = 25
	UnwatchedEpisodes = 40
	UpcomingEpisodes = 50

	LoginAndSettings = 90

	TVShowEpisodes = 60

	DialogAccountCreate = 920
	VideoDialogShow = 900
	VideoDialogShowById = 910

submenu_categories = [
	(ActionCode.MovieRecco, "Movie Recommendations"),
	(ActionCode.TVShows, "Popular TV Shows"),
	(ActionCode.LocalMovieRecco, "Local Movie Recommendations"),
	(ActionCode.LocalTVShows, "Local TV Shows"),
	(ActionCode.UnwatchedEpisodes, "Unwatched TV Show Episodes"),
	(ActionCode.UpcomingEpisodes, "Upcoming TV Episodes"),
	(ActionCode.LoginAndSettings, "Login and Settings")
]

submenu_categories_dict = dict(submenu_categories)

# we do not want the all local movies have listed in main menu, so this is an easy fix
submenu_categories_dict[ActionCode.LocalMovies] = 'All Your Local Movies'

# texts
t_noupcoming = 'There are no upcoming episodes from your tracked TV shows.'
t_nounwatched = 'There are no unwatched episodes in your TV Show tracking'
t_nolocalrecco = 'There are no items in this list. Either you have no movies in your library or they have not been recognized by Synopsi'
t_nolocaltvshow = 'There are no items in this list. Either you have no episodes in your library or they have not been recognized by Synopsi'
t_needrestart = 'To start the SynopsiTV service, please turn off your media center then turn it back on again. Do this now?'
t_needrestart_update = 'Addon has been recently updated. For the plugin to work, it\'s neccessary to restart your media center. Restart now ?'
t_enter_title_to_search =  'Enter a title name to search for.'
t_correct_search_title = 'Search for the correct title'

t_listing_failed = 'Unknown error'
t_stv = 'SynopsiTV'
t_unavail = 'N/A'

overlay_image = ['', 'ondisk-stack.png', 'already-watched-stack.png', 'ondisk-AND-already-watched-stack.png']

t_emptylist_by_mode = {
	ActionCode.UnwatchedEpisodes: t_nounwatched,
	ActionCode.UpcomingEpisodes: t_noupcoming,
	ActionCode.LocalMovieRecco: t_nolocalrecco,
	ActionCode.LocalMovies: t_nolocalrecco,	
	ActionCode.LocalTVShows: t_nolocaltvshow
}


# exceptions
class HashError(Exception):
	pass

class ShutdownRequestedException(Exception):
	pass

class ListEmptyException(BaseException):
	pass


def player_info():
	try:
		info = {
			'player_name': xbmc.getInfoLabel('System.FriendlyName'), 
			'build_version': xbmc.getInfoLabel('System.BuildVersion')
		}
	except:
		info = {'player_name': 'N/A'}
		
	return info

def os_info():
	try:
		info = list(os.uname())
		del info[1]
	except:
		info = 'N/A'
	
	return info

def software_info():
	i = { 'plugin_version': VERSION, 'os_info': os_info() }
	i.update(player_info())
	return i 

def dump(var):
	return json.dumps(var, indent=4)

def structfilter(var, filter_keys):
	v = copy(var)
	if isinstance(var, list):
		for i in var:
			v = structfilter(i, filter_keys)
	elif isinstance(var, dict):
		v = filterkeys(var, filter_keys)
	else:
		v = var

	return v

def uniquote(s):
	return urllib.quote_plus(s.encode('ascii', 'backslashreplace'))

def uniunquote(uni):
	return urllib.unquote_plus(uni.decode('utf-8'))


def filterkeys(var, keys):
	return dict([(k,var[k]) for k in var.keys() if k in keys])

def filtertitles(titles):
	return structfilter(titles, list_filter)

def log(msg):
	#~ xbmc.log(unicode(msg).encode('utf-8'))
	xbmc.log(threading.current_thread().name + ' ' + unicode(msg).encode('utf-8'))

def notification(text, name='SynopsiTV Plugin', time=5000):
    """
    Sends notification to XBMC.
    """
    xbmc.executebuiltin("XBMC.Notification({0},{1},{2})".format(name, text, time))

def get_current_addon():
	global __addon__
	return __addon__

def addon_openSettings():
	addon = get_current_addon()
	addon.openSettings()
	changed = top.apiClient.checkAccountChange()

	return changed

def addon_getSetting(aid, adef=None):
	addon = get_current_addon()
	try:
		res = addon.getSetting(aid)
	except:
		res = adef

	return res

def exc_text_by_mode(mode):
	return t_emptylist_by_mode.get(mode, t_listing_failed)

# application utilities
def check_first_run():
	reloadSkin = False
	# on first run
	if __addon__.getSetting('FIRSTRUN') == 'true':
		log('SYNOPSI FIRST RUN')

		addon_openSettings()

		# enable home screen recco
		xbmc.executebuiltin('Skin.SetBool(homepageShowRecentlyAdded)')
		reloadSkin = True			
		__addon__.setSetting('FIRSTRUN', "false")


	if addon_getSetting('ADDON_SERVICE_FIRSTRUN') != "false":		
		if dialog_need_restart():
			raise ShutdownRequestedException('User requested shutdown')
		else:
			if reloadSkin:
				xbmc.executebuiltin('ReloadSkin()')		
			raise Exception('Addon service is not running')

def dialog_text(msg, max_line_length=60, max_lines=3):
	line_end = [0]
	idx = -1
	line_no = 0
	row_start = 0

	while True:
		last_idx = idx
		idx = msg.find(' ', idx+1)
		if idx==-1:
			# if length of this line would fit into $max_line_length
			if len(msg) - line_end[-1] > max_line_length:
				line_end.append(last_idx)
				line_no += 1
				if line_no >= max_lines:
					break				
			else:
				break
		elif idx-line_end[-1] > max_line_length:
			line_end.append(last_idx)
			line_no += 1
			if line_no >= max_lines:
				break

	line_end.append(None)

	result = []
	last_index = 0
	c = 1
	for end_index in line_end[1:]:
		line = msg[last_index:end_index]
		result.append(line)
		if not end_index:
			break

		last_index = end_index+1
		c += 1

	return result

def list_get(alist, index, default=''):
	try:
		return alist[index]
	except IndexError:
		return default

def dialog_ok(msg):
	lines = dialog_text(msg)
	return xbmcgui.Dialog().ok(t_stv, list_get(lines, 0), list_get(lines, 1), list_get(lines, 2))

def dialog_yesno(msg):
	lines = dialog_text(msg)
	return xbmcgui.Dialog().yesno(t_stv, list_get(lines, 0), list_get(lines, 1), list_get(lines, 2))


def clear_setting_cache():
	"Clear cached addon setting. Useful after update"
	settingsPath = os.path.join(__profile__, 'settings.xml')
	if xbmcvfs.exists(settingsPath):
		xbmcvfs.delete(settingsPath)

def setting_cache_append_string(string):
	settingsPath = os.path.join(__profile__, 'settings.xml')

	# load file
	with open(settingsPath) as f:
		lines = f.read().splitlines()

	lines.insert(-1, string)

	# save file
	with open(settingsPath, 'w') as f:
		f.write(os.linesep.join(lines))

	log('appended string')

class XMLRatingDialog(xbmcgui.WindowXMLDialog):
	"""
	Dialog class that asks user about rating of movie.
	"""
	response = 4
	# 1 = Amazing, 2 = OK, 3 = Terrible, 4 = Not rated
	def __init__(self, *args, **kwargs):
		xbmcgui.WindowXMLDialog.__init__( self )

	def onInit(self):
		self.getString = __addon__.getLocalizedString
		self.getControl(11).setLabel(self.getString(69601))
		self.getControl(10).setLabel(self.getString(69602))
		self.getControl(15).setLabel(self.getString(69603))
		self.getControl(1 ).setLabel(self.getString(69604))
		self.getControl(2 ).setLabel(self.getString(69600))

	def onClick(self, controlId):
		"""
		For controlID see: <control id="11" type="button"> in Rating.xml
		"""
		if controlId == 11:
			self.response = 1
		elif controlId == 10:
			self.response = 2
		elif controlId == 15:
			self.response = 3
		else:
			self.response = 4
		self.close()

	def onAction(self, action):
		if (action.getId() in CANCEL_DIALOG):
			self.response = 4
			self.close()

class XMLLoginDialog(xbmcgui.WindowXMLDialog):
	"""
	Dialog class that asks user about rating of movie.
	"""
	response = 4
	# 1 = Cancel, 2 = OK
	def __init__(self, *args, **kwargs):
		# xbmcgui.WindowXMLDialog.__init__( self )
		super(XMLLoginDialog, self).__init__()
		self.username = kwargs['username']
		self.password = kwargs['password']

	def onInit(self):
		self.getString = __addon__.getLocalizedString
		c = self.getControl(10)

		self.getControl(10).setText(self.username)
		self.getControl(11).setText(self.password)

	def onClick(self, controlId):
		"""
		For controlID see: <control id="11" type="button"> in Rating.xml
		"""
		# log(str('onClick:'+str(controlId)))

		# Cancel
		if controlId==16:
			self.response = 1
			self.close()
		# Ok
		elif controlId==15:
			self.response = 2
			self.close()

	def onAction(self, action):
		# log('action id:' + str(action.getId()))
		if (action.getId() in CANCEL_DIALOG2):
			self.response = 1
			self.close()

	def getData(self):
		return { 'username': self.getControl(10).getText(), 'password': self.getControl(11).getText() }



def get_protected_folders():
	"""
	Returns array of protected folders.
	"""
	array = []
	if __addon__.getSetting("PROTFOL") == "true":
		num_folders = int(__addon__.getSetting("NUMFOLD")) + 1
		for i in range(num_folders):
			path = __addon__.getSetting("FOLDER{0}".format(i + 1))
			array.append(path)

	return array


def is_protected(path):
	"""
	If file is protected.
	"""
	protected = get_protected_folders()
	for _file in protected:
		if _file in path:
			notification("Ignoring file", str(path))
			return True

	return False


def textfilter(bytestring):
	import string,re

	norm = string.maketrans('', '') #builds list of all characters
	non_alnum = string.translate(norm, norm, string.letters+string.digits) 
	
	trans_nontext=string.maketrans(non_alnum,'?'*len(non_alnum))
	cleaned=string.translate(bytestring, trans_nontext)
	
	return cleaned

def stv_hash(filepath):
	"""
	New synopsi hash. Hashing the sedond 512 kB of a file using SHA1.
	"""

	chunk_offset = 524288
	chunk_length = 524288
	
	sha1 = hashlib.sha1()

	try:
		f = xbmcvfs.File(filepath, 'r')
		f.seek(chunk_offset, 0)
		fcontent = f.read(chunk_length)
		if len(fcontent) != chunk_length:
			raise IOError()

		sha1.update(fcontent)
		f.close()

	except (IOError) as e:
		log('Unable to hash file [%s]' % filepath)
		return None

	return sha1.hexdigest()


def old_stv_hash(filepath):
	"""
	Old synopsi hash. Using only first and last 256 bytes.
	"""

	sha1 = hashlib.sha1()

	try:
		f = xbmcvfs.File(filepath, 'rb')
		sha1.update(f.read(256))
		f.seek(-256, 2)
		sha1.update(f.read(256))
		f.close()
	except (IOError) as e:
		return None

	return sha1.hexdigest()


def hash_opensubtitle(name):
	"""
	OpenSubtitles hash.
	"""
	try:
		longlongformat = 'q'  # long long
		bytesize = struct.calcsize(longlongformat)

		_file = xbmcvfs.File(name, 'rb')

		filesize = _file.size()
		hash = filesize

		if filesize < 65536 * 2:
			return None
			# return "SizeError"

		for x in range(65536 / bytesize):
			_buffer = _file.read(bytesize)
			(l_value,) = struct.unpack(longlongformat, _buffer)
			hash += l_value
			hash = hash & 0xFFFFFFFFFFFFFFFF #to remain as 64bit number

		_file.seek(max(0, filesize - 65536), 0)
		for x in range(65536 / bytesize):
			_buffer = _file.read(bytesize)
			(l_value,)= struct.unpack(longlongformat, _buffer)
			hash += l_value
			hash = hash & 0xFFFFFFFFFFFFFFFF

		_file.close()
		returnedhash =  "%016x" % hash

		return returnedhash

	except(IOError):
		log('Unable to hash file [%s]' % name)
		return None


def generate_deviceid():
	"""
	Returns deviceid generated from MAC address.
	"""
	uid = str(uuid.getnode())
	sha1 = hashlib.sha1()
	sha1.update(uid)
	sha1.update(xbmcBuildVer)
	return sha1.hexdigest()

def generate_iuid():
	"""
	Returns install-uniqe id. Has to be generated for every install.
	"""

	return str(uuid.uuid1())



def get_hash_array(path):
	"""
	Returns hash array of dictionaries.
	"""
	hash_array = []
	if not "stack://" in path:
		file_dic = {}

		stv_hash = stv_hash(path)
		sub_hash = hash_opensubtitle(path)

		if stv_hash:
			file_dic['synopsihash'] = stv_hash
		if sub_hash:
			file_dic['subtitlehash'] = sub_hash

		if  sub_hash or stv_hash:
			hash_array.append(file_dic)

	else:
		for moviefile in path.strip("stack://").split(" , "):
			hash_array.append({"path": moviefile,
							"synopsihash": str(stv_hash(moviefile)),
							"subtitlehash": str(hash_opensubtitle(moviefile))
							})
	return hash_array

def get_api_port():
	"""
	This function returns TCP port to which is changed XBMC RPC API.
	If nothing is changed return default 9090.
	"""

	try:
		path = os.path.join('special://profile', 'advancedsettings.xml')
				
		f = xbmcvfs.File(path, 'r')
		fcontent = f.read()
		f.close()

		root = et.fromstring(fcontent)
		nodes = root.findall('.//tcpport')
		value = int(nodes[0].text)

	except:
		value = 9090

	return value

def get_install_id():
	global __addon__

	iuid = __addon__.getSetting(id='INSTALL_UID')
	if not iuid:
		iuid = generate_iuid()
		log('iuid:' + iuid)
		__addon__.setSetting(id='INSTALL_UID', value=iuid)

	return iuid

def home_screen_fill(apiClient, cache):
	"""
	This method updates movies on HomePage.
	"""

	# get recco movies and episodes
	try:
		movie_recco = apiClient.profileRecco('movie', True, homeReccoLimit)['titles']
		episode_recco = apiClient.get_unwatched_episodes()

		#~ log('movie_recco:' + dump(movie_recco))
		#~ log('episode_recco:' + dump(episode_recco))
		log('movie_recco count:' + str(len(movie_recco)))
		log('episode_recco count:' + str(len(episode_recco)))

		MOVIES_COUNT = 5	# count of template display slots
		WINDOW = xbmcgui.Window( 10000 )

		for i in range(0, MOVIES_COUNT):
			# recco could return less than 5 items
			if i < len(movie_recco):
				m = movie_recco[i]
				lib_item = cache.getByStvId(m['id'])
				log('movie %d %s' % (i, m['name']))
				log('lib_item %s' % (str(lib_item)))

				WINDOW.setProperty("LatestMovie.{0}.Title".format(i+1), m['name'])
				if lib_item:
					WINDOW.setProperty("LatestMovie.{0}.Path".format(i+1), lib_item['file'])
				WINDOW.setProperty("LatestMovie.{0}.Thumb".format(i+1), m['cover_large'])

			# recco could return less than 5 items
			if i < len(episode_recco):
				e = episode_recco[i]				
				c_episode = cache.getByStvId(e['id'])
					
								
				WINDOW.setProperty("LatestEpisode.{0}.EpisodeTitle".format(i+1), e['tvshow_name'])				# tv show name
				WINDOW.setProperty("LatestEpisode.{0}.ShowTitle".format(i+1), e['name'])						# episode name
				WINDOW.setProperty("LatestEpisode.{0}.EpisodeNo".format(i+1), get_episode_identifier(e))		# episode id string
				WINDOW.setProperty("LatestEpisode.{0}.Path".format(i+1), c_episode['file'] if c_episode else '')
				WINDOW.setProperty("LatestEpisode.{0}.Thumb".format(i+1), e['cover_large'])


	except Exception as e:
		log(traceback.format_exc())
		notification('Movie reccomendation service failed')
		return


def login_screen(apiClient):
	if not __lockLoginScreen__.acquire(False):
		log('login_screen not starting duplicate')
		return False

	username = __addon__.getSetting('USER')
	password = __addon__.getSetting('PASS')

	log('string type: ' + str(type(username)))
	log('string type: ' + str(type(password)))

	ui = XMLLoginDialog("LoginDialog.xml", __addonpath__, "Default", username=username, password=password)
	ui.doModal()
	# ui.show()

	# dialog result is 'OK'
	if ui.response==2:
		log('dialog OK')
		# check if data changed
		d = ui.getData()
		if username!=d['username'] or password!=d['password']:
			# store in settings
			__addon__.setSetting('USER', value=d['username'])
			__addon__.setSetting('PASS', value=d['password'])
			apiClient.setUserPass(d['username'], d['password'])

		result=True
	else:
		log('dialog canceled')
		result=False

	del ui

	__lockLoginScreen__.release()
	log('login_screen result: %d' % result)
	return result

def get_rating():
	"""
	Get rating from user:
	1 = Amazing, 2 = OK, 3 = Terrible, 4 = Not rated
	"""
	ui = XMLRatingDialog("Rating.xml", __addonpath__, "Default")
	ui.doModal()
	_response = ui.response
	del ui
	return _response

def dialog_check_login_correct():
	if dialog_login_fail_yesno():
		addon_openSettings()

		# openSettings do not return users click, so we return if user had the intention to correct credentials
		return True
	else:
		return False

def dialog_login_fail_yesno():
	dialog = xbmcgui.Dialog()
	result = dialog.yesno(t_stv, "Authentication failed", "Would you like to open settings and correct your login info?")
	return result


def dialog_need_restart(reason=t_needrestart):
	dialog = xbmcgui.Dialog()
	yes = dialog_yesno(reason)
	return yes


def add_directory(name, url, mode, iconimage):
	u = sys.argv[0]+"?mode="+str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	# liz.setInfo(type="Video", infoLabels={"Title": name} )
	ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	return ok


def add_movie(movie, mode, iconimage):
	json_data = json.dumps(movie)
	if not movie.has_key('type'):
		log('add_movie type not set')

	log('add_movie: ' + dump(filtertitles(movie)))

	u = sys.argv[0]+"?&mode="+str(mode)+"&name="+uniquote(movie.get('name'))+"&data="+uniquote(json_data)
	li = xbmcgui.ListItem(movie.get('name'), iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	if movie.get('watched'):
		li.setInfo( type="Video", infoLabels={ "playcount": 1 } )

	# local movies button to show all movies
	isFolder = movie.get('id') == HACK_SHOW_ALL_LOCAL_MOVIES
	new_li = (u, li, isFolder)

	return new_li
	
	
def show_categories():
	"""
	Shows initial categories on home screen.
	"""
	xbmc.executebuiltin("Container.SetViewMode(503)")
	for categoryCode, categoryName in submenu_categories:
		add_directory(categoryName, "url", categoryCode, "list.png")

def get_movie_sources():		
	userdata = xbmc.translatePath('special://userdata')
	sourceFilePath = os.path.join(userdata, 'sources.xml')
	
	f = xbmcvfs.File(sourceFilePath, 'r')
	fcontent = f.read()
	f.close()

	root = et.fromstring(fcontent)
	el = root.findall('video/source/path')
	return sorted([i.text for i in el], key=len, reverse=True)

def rel_path(realpath):
	sources = get_movie_sources()
	for src in sources:
		if realpath.startswith(src):
			return realpath[len(src):]
	
	return realpath
		
def get_episode_identifier(item):
	return 'S%sE%s' % (item.get('season_number', '??'), item.get('episode_number', '??'))
