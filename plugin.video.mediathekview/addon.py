# -*- coding: utf-8 -*-
"""
The main addon module

MIT License

Copyright (c) 2017-2018, Leo Moll

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# pylint: disable=import-error
# pylint: disable=mixed-indentation, bad-whitespace, bad-continuation, missing-docstring

# -- Imports ------------------------------------------------
from __future__ import unicode_literals  # ,absolute_import, division
# from future import standard_library
# from builtins import *
# standard_library.install_aliases()
import time
import datetime

import xbmcgui
import xbmcplugin

from resources.lib.kodi.KodiAddon import KodiPlugin

from resources.lib.store import Store
from resources.lib.notifier import Notifier
from resources.lib.settings import Settings
from resources.lib.filmui import FilmUI
from resources.lib.channelui import ChannelUI
from resources.lib.initialui import InitialUI
from resources.lib.showui import ShowUI
from resources.lib.downloader import Downloader
from resources.lib.searches import RecentSearches

# -- Classes ------------------------------------------------
class MediathekView( KodiPlugin ):

	def __init__( self ):
		super( MediathekView, self ).__init__()
		self.settings	= Settings()
		self.notifier	= Notifier()
		self.database	= Store( self.getNewLogger( 'Store' ), self.notifier, self.settings )

	def show_main_menu( self ):
		# Search
		self.addFolderItem( 30901, { 'mode': "search", 'extendedsearch': False } )
		# Search all
		self.addFolderItem( 30902, { 'mode': "search", 'extendedsearch': True } )
		# Browse livestreams
		self.addFolderItem( 30903, { 'mode': "livestreams" } )
		# Browse recently added
		self.addFolderItem( 30904, { 'mode': "recent", 'channel': 0 } )
		# Browse recently added by channel
		self.addFolderItem( 30905, { 'mode': "recentchannels" } )
		# Browse by Initial->Show
		self.addFolderItem( 30906, { 'mode': "initial", 'channel': 0 } )
		# Browse by Channel->Initial->Shows
		self.addFolderItem( 30907, { 'mode': "channels" } )
		# Database Information
		self.addActionItem( 30908, { 'mode': "action-dbinfo" } )
		# Manual database update
		if self.settings.updmode == 1 or self.settings.updmode == 2:
			self.addActionItem( 30909, { 'mode': "action-dbupdate" } )
		self.endOfDirectory()
		self._check_outdate()

	def show_searches( self, extendedsearch = False ):
		self.addFolderItem( 30931, { 'mode': "newsearch", 'extendedsearch': extendedsearch } )
		RecentSearches( self, extendedsearch ).load().populate()
		self.endOfDirectory()

	def new_search( self, extendedsearch = False ):
		settingid = 'lastsearch2' if extendedsearch is True else 'lastsearch1'
		headingid = 30902 if extendedsearch is True else 30901
		# are we returning from playback ?
		search = self.addon.getSetting( settingid )
		if search:
			# restore previous search
			self.database.Search( search, FilmUI( self ), extendedsearch )
		else:
			# enter search term
			( search, confirmed ) = self.notifier.GetEnteredText( '', headingid )
			if len( search ) > 2 and confirmed is True:
				RecentSearches( self, extendedsearch ).load().add( search ).save()
				if self.database.Search( search, FilmUI( self ), extendedsearch ) > 0:
					self.addon.setSetting( settingid, search )
			else:
				# pylint: disable=line-too-long
				self.info( 'The following ERROR can be ignored. It is caused by the architecture of the Kodi Plugin Engine' )
				self.endOfDirectory( False, cacheToDisc = True )
				# self.show_searches( extendedsearch )

	def show_db_info( self ):
		info = self.database.GetStatus()
		heading = self.language( 30907 )
		infostr = self.language( {
			'NONE': 30941,
			'UNINIT': 30942,
			'IDLE': 30943,
			'UPDATING': 30944,
			'ABORTED': 30945
		}.get( info['status'], 30941 ) )
		infostr = self.language( 30965 ) % infostr
		totinfo = self.language( 30971 ) % (
			info['tot_chn'],
			info['tot_shw'],
			info['tot_mov']
		)
		updatetype = self.language( 30972 if info['fullupdate'] > 0 else 30973 )
		if info['status'] == 'UPDATING' and info['filmupdate'] > 0:
			updinfo = self.language( 30967 ) % (
				updatetype,
				datetime.datetime.fromtimestamp( info['filmupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				info['add_chn'],
				info['add_shw'],
				info['add_mov']
			)
		elif info['status'] == 'UPDATING':
			updinfo = self.language( 30968 ) % (
				updatetype,
				info['add_chn'],
				info['add_shw'],
				info['add_mov']
			)
		elif info['lastupdate'] > 0 and info['filmupdate'] > 0:
			updinfo = self.language( 30969 ) % (
				updatetype,
				datetime.datetime.fromtimestamp( info['lastupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				datetime.datetime.fromtimestamp( info['filmupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				info['add_chn'],
				info['add_shw'],
				info['add_mov'],
				info['del_chn'],
				info['del_shw'],
				info['del_mov']
			)
		elif info['lastupdate'] > 0:
			updinfo = self.language( 30970 ) % (
				updatetype,
				datetime.datetime.fromtimestamp( info['lastupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
				info['add_chn'],
				info['add_shw'],
				info['add_mov'],
				info['del_chn'],
				info['del_shw'],
				info['del_mov']
			)
		else:
			updinfo = self.language( 30966 )

		xbmcgui.Dialog().textviewer(
			heading,
			infostr + '\n\n' +
			totinfo + '\n\n' +
			updinfo
		)

	def _check_outdate( self, maxage = 172800 ):
		if self.settings.updmode != 1 and self.settings.updmode != 2:
			# no check with update disabled or update automatic
			return
		if self.database is None:
			# should never happen
			self.notifier.ShowOutdatedUnknown()
			return
		status = self.database.GetStatus()
		if status['status'] == 'NONE' or status['status'] == 'UNINIT':
			# should never happen
			self.notifier.ShowOutdatedUnknown()
			return
		elif status['status'] == 'UPDATING':
			# great... we are updating. nuthin to show
			return
		# lets check how old we are
		tsnow = int( time.time() )
		tsold = int( status['lastupdate'] )
		if tsnow - tsold > maxage:
			self.notifier.ShowOutdatedKnown( status )

	def init( self ):
		if self.database.Init():
			if self.settings.HandleFirstRun():
				pass
			self.settings.HandleUpdateOnStart()

	def run( self ):
		# save last activity timestamp
		self.settings.ResetUserActivity()
		# process operation
		mode = self.get_arg( 'mode', None )
		if mode is None:
			self.show_main_menu()
		elif mode == 'search':
			extendedsearch = self.get_arg( 'extendedsearch', 'False' ) == 'True'
			self.show_searches( extendedsearch )
		elif mode == 'newsearch':
			self.new_search( self.get_arg( 'extendedsearch', 'False' ) == 'True' )
		elif mode == 'research':
			search			= self.get_arg( 'search', '' )
			extendedsearch	= self.get_arg( 'extendedsearch', 'False' ) == 'True'
			self.database.Search( search, FilmUI( self ), extendedsearch )
			RecentSearches( self, extendedsearch ).load().add( search ).save()
		elif mode == 'delsearch':
			search			= self.get_arg( 'search', '' )
			extendedsearch	= self.get_arg( 'extendedsearch', 'False' ) == 'True'
			RecentSearches( self, extendedsearch ).load().delete( search ).save().populate()
			self.runBuiltin( 'Container.Refresh' )
		elif mode == 'livestreams':
			self.database.GetLiveStreams( FilmUI( self, [ xbmcplugin.SORT_METHOD_LABEL ] ) )
		elif mode == 'recent':
			channel = self.get_arg( 'channel', 0 )
			self.database.GetRecents( channel, FilmUI( self ) )
		elif mode == 'recentchannels':
			self.database.GetRecentChannels( ChannelUI( self, nextdir = 'recent' ) )
		elif mode == 'channels':
			self.database.GetChannels( ChannelUI( self, nextdir = 'shows' ) )
		elif mode == 'action-dbinfo':
			self.show_db_info()
		elif mode == 'action-dbupdate':
			self.settings.TriggerUpdate()
			self.notifier.ShowNotification( 30963, 30964, time = 10000 )
		elif mode == 'initial':
			channel = self.get_arg( 'channel', 0 )
			self.database.GetInitials( channel, InitialUI( self ) )
		elif mode == 'shows':
			channel = self.get_arg( 'channel', 0 )
			initial = self.get_arg( 'initial', None )
			self.database.GetShows( channel, initial, ShowUI( self ) )
		elif mode == 'films':
			show = self.get_arg( 'show', 0 )
			self.database.GetFilms( show, FilmUI( self ) )
		elif mode == 'downloadmv':
			filmid	= self.get_arg( 'id', 0 )
			quality	= self.get_arg( 'quality', 1 )
			Downloader( self ).download_movie( filmid, quality )
		elif mode == 'downloadep':
			filmid	= self.get_arg( 'id', 0 )
			quality	= self.get_arg( 'quality', 1 )
			Downloader( self ).download_episode( filmid, quality )
		elif mode == 'playwithsrt':
			filmid		= self.get_arg( 'id', 0 )
			only_sru	= self.get_arg( 'only_set_resolved_url', 'False' ) == 'True'
			Downloader( self ).play_movie_with_subs( filmid, only_sru )

		# cleanup saved searches
		if mode is None or mode != 'search':
			self.addon.setSetting( 'lastsearch1', '' )
		if mode is None or mode != 'searchall':
			self.addon.setSetting( 'lastsearch2', '' )

	def exit( self ):
		self.database.Exit()


# -- Main Code ----------------------------------------------
if __name__ == '__main__':
	ADDON = MediathekView()
	ADDON.init()
	ADDON.run()
	ADDON.exit()
	del ADDON
