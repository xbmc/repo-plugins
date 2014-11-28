# coding=utf-8

##################################
# ZattooBox v0.2.2
# (c) 2014 Pascal Nançoz
# nancpasc@gmail.com
#
# XBMC Addon for Zattoo recordings
##################################
import sys, os, re, base64
import xbmcgui, xbmcplugin, xbmcaddon
import urllib, urllib2, urlparse
import json

__addon__       = xbmcaddon.Addon()
__addonname__   = __addon__.getAddonInfo('name')

def get_resource_file(resource):
	return os.path.join(xbmc.translatePath(__addon__.getAddonInfo('path')).decode('utf-8'), 'resources', 'data', 'session', resource)

COOKIE_FILE      = get_resource_file('session.id')
ACCOUNT_FILE     = get_resource_file('account.dat')
ZAPI_SESSION_URL = 'https://zattoo.com'
ZAPI_URL         = 'http://zattoo.com'

def fetch_appToken():
	handle = urllib2.urlopen(ZAPI_URL + '/')
	html = handle.read()
	return re.search("window\.appToken\s*=\s*'(.*)'", html).group(1)

def session_url_request(url, params):
	try:
		response = _HTTPOpener.open(url, urllib.urlencode(params) if params is not None else None)
		if response is not None:
			save_session_id(extract_session_id(response.info().getheader('Set-Cookie')))
			return response.read() 
	except Exception:
		pass
	return None

def zapi_call(url, params, context='default'):
	content = session_url_request(url, params)

	if context != 'session' and content is None and session_retrieve(True):
		content = session_url_request(url, params)
	if content is None:
		if context != 'session':
			xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(30901))
		return None
	try:
		data = json.loads(content)
		if data['success'] == True:
			return data
	except Exception:
		pass
	return None

def hello2():
	url = ZAPI_URL + '/zapi/session/hello'
	appToken = fetch_appToken()
	params = {"client_app_token" : appToken,
			  "uuid"    : "d7512e98-38a0-4f01-b820-5a5cf98141fe",
			  "lang"    : "en",
			  "format"	: "json"}
	resultData = zapi_call(url, params, 'session')
	return resultData is not None

def login():
	url = ZAPI_SESSION_URL + '/zapi/account/login'
	params = {"login": __addon__.getSetting('username'), "password" : __addon__.getSetting('password')}
	resultData = zapi_call(url, params, 'session')
	if resultData is not None:
		save_account_data(resultData)
		return True
	return False

def build_directory_content(content, addon_handle):
	xbmcplugin.setContent(addon_handle, 'movies')
	for record in content:
		li = xbmcgui.ListItem(record['title'], iconImage=record['image'])
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=record['url'], listitem=li, isFolder=record['isFolder'])
	xbmcplugin.endOfDirectory(addon_handle)

def build_root(addon_uri, addon_handle):
	content = []
	content.append({'title': __addon__.getLocalizedString(30102), 'image': '', 'isFolder': True,
					'url': addon_uri + '?' + urllib.urlencode({'mode': 'f', 'level': 'recordings'})})
	build_directory_content(content, addon_handle)

def build_recordingsList(addon_uri, addon_handle):
	url = ZAPI_URL + '/zapi/playlist'
	resultData = zapi_call(url, None)
	if resultData is None:
		return None
	content = []
	for record in resultData['recordings']:
		content.append({'title': record['title'], 'image': record['image_url'], 'isFolder': False,
						'url': addon_uri + '?' + urllib.urlencode({'mode': 'watch_r', 'id': record['id']})})
	build_directory_content(content, addon_handle)

def watch_recording(recording_id):
	url = ZAPI_URL + '/zapi/watch'
	params = {'recording_id': recording_id, 'stream_type': 'hls'}
	resultData = zapi_call(url, params)
	if resultData is not None:
		url = resultData['stream']['url']
		xbmc.Player().play(url)

def set_session_opener(session_id):
	_HTTPOpener.addheaders = [
		('Content-type', 'application/x-www-form-urlencoded'),
		('Accept', 'application/json'),
		('Cookie', 'beaker.session.id=' + session_id)]

def session_retrieve(force_renew=False):
	global _HTTPOpener
	global _account_data
	try:
		_HTTPOpener = urllib2.build_opener()
		if not force_renew and os.path.isfile(COOKIE_FILE) and os.path.isfile(ACCOUNT_FILE):
			with open(COOKIE_FILE, 'r') as f:
				set_session_opener(base64.b64decode(f.readline()))
			with open(ACCOUNT_FILE, 'r') as f:
				_account_data = json.loads(base64.b64decode(f.readline()))
			if _account_data['success'] == True:
				return True
	except Exception:
		pass
	set_session_opener('')
	return hello2() and login()

def extract_session_id(cookie_content):
	return re.search("beaker\.session\.id\s*=\s*([^\s;]*)", cookie_content).group(1)

def save_account_data(data):
	if data is not None:
		_account_data = data
		with open(ACCOUNT_FILE, 'w') as f:
			f.write(base64.b64encode(json.dumps(data)))

def save_session_id(session_id):
	if session_id is not None:
		set_session_opener(session_id)
		with open(COOKIE_FILE, 'w') as f:
			f.write(base64.b64encode(session_id)) 

#XBMC plugin entry point
addon_uri = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

if session_retrieve():
	mode = args.get('mode', None)

	if mode is None:
		build_root(addon_uri, addon_handle)

	elif mode[0] == 'f':
		level = args.get('level')[0]
		if level == 'recordings':
			build_recordingsList(addon_uri, addon_handle)

	elif mode[0] == 'watch_r':
		recording_id = args.get('id')[0]
		watch_recording(recording_id)
else:
	xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(30902))