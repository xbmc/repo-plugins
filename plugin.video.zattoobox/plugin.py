# coding=utf-8

##################################
# ZattooBox v0.5.0
# (c) 2014 Pascal Nançoz
# nancpasc@gmail.com
#
# XBMC Addon for Zattoo recordings
##################################
import sys, urllib, urlparse, os
import xbmcgui, xbmcplugin, xbmcaddon

#import zappylib
from resources.lib.zappylib.zapisession import ZapiSession
from resources.lib.zappylib.zapihelper import ZapiHelper

__addon__       = xbmcaddon.Addon()
__addonname__   = __addon__.getAddonInfo('name')
_dataFolder_	= xbmc.translatePath(__addon__.getAddonInfo('profile')).decode('utf-8')
_zapiSession_	= ZapiSession(_dataFolder_)

def build_directoryContent(content, addon_handle):
	xbmcplugin.setContent(addon_handle, 'movies')
	for record in content:
		li = xbmcgui.ListItem(record['title'], iconImage=record['image'])
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=record['url'], listitem=li, isFolder=record['isFolder'])
	xbmcplugin.endOfDirectory(addon_handle)

def build_root(addon_uri, addon_handle):
	content = [
		{'title': __addon__.getLocalizedString(30100), 'image': '', 'isFolder': True, 'url': addon_uri + '?' + urllib.urlencode({'mode': 'f', 'level': 'livetv_fav'})},
		{'title': __addon__.getLocalizedString(30101), 'image': '', 'isFolder': True, 'url': addon_uri + '?' + urllib.urlencode({'mode': 'f', 'level': 'livetv_all'})},
		{'title': __addon__.getLocalizedString(30102), 'image': '', 'isFolder': True, 'url': addon_uri + '?' + urllib.urlencode({'mode': 'f', 'level': 'recordings'})}]
	build_directoryContent(content, addon_handle)

def build_recordingsList(addon_uri, addon_handle):
	resultData = _zapiSession_.exec_zapiCall('/zapi/playlist', None)
	if resultData is not None:
		content = []
		for record in resultData['recordings']:
			content.append({
				'title': record['title'], 'image': record['image_url'], 'isFolder': False,
				'url': addon_uri + '?' + urllib.urlencode({'mode': 'watch_r', 'id': record['id']})})
		build_directoryContent(content, addon_handle)

def build_channelsList(addon_uri, addon_handle, category):
	zapiHelper = ZapiHelper(_zapiSession_)
	channels = zapiHelper.get_channels(category)
	if channels is not None:
		content = []
		for record in channels:
			content.append({
				'title': record['title'], 'image': record['image_url'], 'isFolder': False,
				'url': addon_uri + '?' + urllib.urlencode({'mode': 'watch_c', 'id': record['id']})})
		build_directoryContent(content, addon_handle)

def watch_recording(recording_id):
	params = {'recording_id': recording_id, 'stream_type': 'hls'}
	resultData = _zapiSession_.exec_zapiCall('/zapi/watch', params)
	if resultData is not None:
		url = resultData['stream']['url']
		xbmc.Player().play(url)

def watch_channel(channel_id):
	params = {'cid': channel_id, 'stream_type': 'hls'}
	resultData = _zapiSession_.exec_zapiCall('/zapi/watch', params)
	if resultData is not None:
		url = resultData['stream']['watch_urls'][0]['url']
		xbmc.Player().play(url)

#XBMC plugin entry point
addon_uri = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

if _zapiSession_.init_session(__addon__.getSetting('username'), __addon__.getSetting('password')):
	mode = args.get('mode', None)

	if mode is None:
		build_root(addon_uri, addon_handle)

	elif mode[0] == 'f':
		level = args.get('level')[0]
		if level == 'recordings':
			build_recordingsList(addon_uri, addon_handle)

		elif level == 'livetv_fav':
			build_channelsList(addon_uri, addon_handle, 'favorites')

		elif level == 'livetv_all':
			build_channelsList(addon_uri, addon_handle, 'all')

	elif mode[0] == 'watch_r':
		recording_id = args.get('id')[0]
		watch_recording(recording_id)

	elif mode[0] == 'watch_c':
		cid = args.get('id')[0]
		watch_channel(cid)
else:
	xbmcgui.Dialog().ok(__addonname__, __addon__.getLocalizedString(30902))