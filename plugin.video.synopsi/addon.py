# -*- coding: utf-8 -*-
"""
Default file for SynopsiTV addon. See addon.xml
<extension point="xbmc.python.pluginsource" library="addon.py">
"""
# xbmc
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# python standart lib
import urllib
import sys
import os
import time
import json
import urllib2
import re
import os.path
import logging
import traceback
import subprocess
import CommonFunctions
import socket
import threading

# application
from utilities import *
from cache import StvList
from xbmcrpc import xbmc_rpc

threading.current_thread().name = 'addon.py'

class UnknownModeException(Exception):
	pass

class InputParamsException(Exception):
	pass

class AddonClient(object):
	def __init__(self, pluginhandle):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.pluginhandle = pluginhandle
		addon = get_current_addon()
		self.service_port = int(addon.getSetting('ADDON_SERVICE_PORT'))

	def execute(self, command, **arguments):
		try:
			json_data = {
				'command': command,
				'arguments': arguments
			}

			response = None

			self.s.connect(('localhost', self.service_port))
			xbmc.log('CLIENT / SEND / ' + dump(json_data))
			self.s.sendall(json.dumps(json_data) + "\n")

			total_data=[]
			while True:
				data = self.s.recv(8192)
				if not data: break
				total_data.append(data)

			response = ''.join(total_data)

			#~ xbmc.log('CLIENT / RAW RESPONSE / ' + str(response))
			self.s.close()
			response_json = json.loads(response)
			#~ xbmc.log('CLIENT / JSON RESPONSE / ' + dump(response))

		# TODO: some handling
		except:
			xbmc.log('CLIENT / ERROR / RESPONSE ' + str(response))
			#~ raise
			return {}

		return response_json

	def get_global_recco(self, movie_type):
		return self.execute('get_global_recco', movie_type=movie_type)

	def get_top_tvshows(self):
		return self.execute('get_top_tvshows')

	def get_local_tvshows(self):
		return self.execute('get_local_tvshows')

	def get_local_recco2(self, movie_type):
		return self.execute('get_local_recco2', movie_type=movie_type)

	def get_upcoming_episodes(self):
		return self.execute('get_upcoming_episodes')

	def get_unwatched_episodes(self):
		return self.execute('get_unwatched_episodes')

	def get_tvshow_season(self, tvshow_id):
		return self.execute('get_tvshow_season', tvshow_id=tvshow_id)

	def get_title(self, stv_id, **kwargs):
		return self.execute('get_title', stv_id=stv_id, **kwargs)

	def get_title_similars(self, stv_id):
		return self.execute('get_title_similars', stv_id=stv_id)

	def get_tvshow(self, tvshow_id):
		return self.execute('get_title', tvshow_id=tvshow_id)

	def get_local_movies(self):
		return self.execute('get_local_movies')

	def show_submenu(self, mode, **params):		
		return self.execute('show_submenu', action_code=mode, **params)

	def show_video_dialog(self, json_data):
		return self.execute('show_video_dialog', json_data=json_data)

	def show_video_dialog_byId(self, stv_id):
		return self.execute('show_video_dialog_byId', stv_id=stv_id)

	def open_settings(self):
		return self.execute('open_settings')

	def debug_1(self):
		return self.execute('debug_1')

	def debug_2(self):
		return self.execute('debug_2')

	def debug_3(self):
		return self.execute('debug_3')

# script start
try:
	dirhandle = int(sys.argv[1])

	log('SYS ARGV:' + str(sys.argv))

	url_parsed = urlparse.urlparse(sys.argv[2])
	params = urlparse.parse_qs(url_parsed.query)

	check_first_run()

	addonclient = AddonClient(dirhandle)

	param_vars = ['url', 'mode', 'type', 'data', 'stv_id']
	p = dict([(k, params.get(k, [None])[0]) for k in param_vars])

	try:
		if p['url']:
			p['url']=uniunquote(p['url'])

		if p['mode']:
			p['mode']=int(p['mode'])

		if p['type']:
			p['type']=int(p['type'])

		if p['data']:
			p['data'] = uniunquote(p['data'])
			p['json_data'] = json.loads(p['data'])

		if p['stv_id']:
			p['stv_id'] = int(p['stv_id'])

	except TypeError:
		raise InputParamsException('Wrong params: ' + str(sys.argv))

	#~ log('params:' + str(params))
	log('mode: %s type: %s' % (p['mode'], p['type']))
	#~ log('url: %s' % (p['url']))
	log('data: %s' % (p['data']))

	# hacks
	if p['mode'] == ActionCode.VideoDialogShow and p['json_data']['id'] == HACK_SHOW_ALL_LOCAL_MOVIES:
		p['mode'] = ActionCode.LocalMovies

	# debug
	#~ if p['mode'] in [ActionCode.MovieRecco, ActionCode.LocalMovieRecco, ActionCode.TVShows, ActionCode.LocalTVShows, ActionCode.TVShowEpisodes, ActionCode.UnwatchedEpisodes, ActionCode.UpcomingEpisodes, ActionCode.LocalMovies]:
		#~ p['mode']=971

	# routing
	if p['mode']==None:
		show_categories()
		xbmcplugin.endOfDirectory(dirhandle)

	elif p['mode'] in [ActionCode.MovieRecco, ActionCode.LocalMovieRecco, ActionCode.TVShows, ActionCode.LocalTVShows, ActionCode.TVShowEpisodes, ActionCode.UnwatchedEpisodes, ActionCode.UpcomingEpisodes, ActionCode.LocalMovies]:
		params = {'stv_id': p['stv_id']} if p['stv_id'] else {}
		addonclient.show_submenu(p['mode'], **params)

	elif p['mode']==ActionCode.VideoDialogShow:
		addonclient.show_video_dialog(p['json_data'])

	elif p['mode']==ActionCode.VideoDialogShowById:
		addonclient.show_video_dialog_byId(p['stv_id'])

	elif p['mode']==ActionCode.LoginAndSettings:
		addonclient.open_settings()

	# debugging
	elif p['mode']==970:
		xbmc.executebuiltin('CleanLibrary(video)')
		xbmc.executebuiltin('UpdateLibrary(video)')

	elif p['mode']==971:
		#~ addonclient.debug_1()

		#~ winid = common.getUserInput("Title", "")
		#~ xbmc.executebuiltin('ActivateWindow(' + winid + ')')

		#~ xbmc.executebuiltin('ActivateWindow(/home/smid/projects/XBMC/resources/skins/Default/720p/MyVideoNav.xml)')
		#~ xbmc.executebuiltin('ActivateWindow(9525)')
		
		#~ xbmcplugin.endOfDirectory(dirhandle)
		
		
		#~ xbmc.executebuiltin('RunScript(plugin.video.synopsi, 0, mode=910&stv_id=2514500)')
		#~ sys.exit(0)
		
		# fill in custom listing dialog/window
		items = [
        {
            "cover_medium": "https://s3.amazonaws.com/titles.synopsi.tv/00136558-223.jpg",
            "id": 136558,
            "name": "The Time Machine",
            'file': 'volaco'
        },
        {
            "cover_medium": "https://s3.amazonaws.com/titles.synopsi.tv/02514500-223.jpg",
            "id": 2514500,
            "name": "Inglourious Basterds",
            'watched': 'yes'
        },
        {
            "cover_medium": "https://s3.amazonaws.com/titles.synopsi.tv/00072215-223.jpg",
            "id": 72215,
            "name": "I, Robot",
            'watched': 'yes',
            'file': 'volaco'
        },
        {
            "cover_medium": "https://s3.amazonaws.com/titles.synopsi.tv/00072215-223.jpg",
            "id": 72215,
            "name": "I, Robot 2",
            'custom_overlay': 'ondisk-AND-already-watched-stack.png'
        },
        {
            "cover_medium": "https://s3.amazonaws.com/titles.synopsi.tv/00072215-223.jpg",
            "id": 72215,
            "name": "I, Robot 3",
            'custom_overlay': 'already-watched-stack.png'
        }
        ]

		dialog.open_list_dialog({ 'items': items }, close=True)
	

	elif p['mode']==972:
		#~ xbmc.executebuiltin('ActivateWindow(MyVideoNav,plugin://plugin.video.synopsi,return)')
		
		#~ addonclient.debug_2()
		#~ wid = xbmcgui.getCurrentWindowDialogId()
		#~ print 'wid:' + str(wid)
		#~ win = xbmcgui.WindowDialog(wid)
		#~ item_list = win.getControl(50)
		#~ for i in xrange(item_list.size()):
			#~ item = item_list.getListItem()
			#~ print i, item
		pass


	elif p['mode']==973:
		addonclient.debug_3()
	else:
		raise UnknownModeException('Unknown mode: %s' % p['mode'])

except ShutdownRequestedException:
	xbmcplugin.endOfDirectory(dirhandle)
	xbmc.executebuiltin('Quit')
except:
	log(traceback.format_exc())
	xbmcplugin.endOfDirectory(dirhandle)






