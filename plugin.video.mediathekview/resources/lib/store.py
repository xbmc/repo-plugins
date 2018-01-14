# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

# -- Imports ------------------------------------------------
from resources.lib.storemysql  import StoreMySQL
from resources.lib.storesqlite import StoreSQLite

# -- Classes ------------------------------------------------
class Store( object ):
	def __init__( self, logger, notifier, settings ):
		self.logger = logger
		self.notifier = notifier
		self.settings = settings
		# load storage engine
		if settings.type == '0':
			self.logger.info( 'Database driver: Internal (sqlite)' )
			self.db = StoreSQLite( logger.getNewLogger( 'StoreSQLite' ), notifier, self.settings )
		elif settings.type == '1':
			self.logger.info( 'Database driver: External (mysql)' )
			self.db = StoreMySQL( logger.getNewLogger( 'StoreMySQL' ), notifier, self.settings )
		else:
			self.logger.warn( 'Unknown Database driver selected' )
			self.db = None

	def Init( self, reset = False ):
		if self.db is not None:
			self.db.Init( reset )

	def Exit( self ):
		if self.db is not None:
			self.db.Exit()

	def Search( self, search, filmui ):
		if self.db is not None:
			self.db.Search( search, filmui )

	def SearchFull( self, search, filmui ):
		if self.db is not None:
			self.db.SearchFull( search, filmui )

	def GetRecents( self, channelid, filmui ):
		if self.db is not None:
			self.db.GetRecents( channelid, filmui )

	def GetLiveStreams( self, filmui ):
		if self.db is not None:
			self.db.GetLiveStreams( filmui )

	def GetChannels( self, channelui ):
		if self.db is not None:
			self.db.GetChannels( channelui )

	def GetRecentChannels( self, channelui ):
		if self.db is not None:
			self.db.GetRecentChannels( channelui )

	def GetInitials( self, channelid, initialui ):
		if self.db is not None:
			self.db.GetInitials( channelid, initialui )

	def GetShows( self, channelid, initial, showui ):
		if self.db is not None:
			self.db.GetShows( channelid, initial, showui )

	def GetFilms( self, showid, filmui ):
		if self.db is not None:
			self.db.GetFilms( showid, filmui )

	def RetrieveFilmInfo( self, filmid ):
		if self.db is not None:
			return self.db.RetrieveFilmInfo( filmid )

	def GetStatus( self ):
		if self.db is not None:
			return self.db.GetStatus()
		else:
			return {
				'modified': int( time.time() ),
				'status': 'UNINIT',
				'lastupdate': 0,
				'filmupdate': 0,
				'fullupdate': 0,
				'add_chn': 0,
				'add_shw': 0,
				'add_mov': 0,
				'del_chn': 0,
				'del_shw': 0,
				'del_mov': 0,
				'tot_chn': 0,
				'tot_shw': 0,
				'tot_mov': 0
			}

	def UpdateStatus( self, status = None, lastupdate = None, filmupdate = None, fullupdate = None, add_chn = None, add_shw = None, add_mov = None, del_chn = None, del_shw = None, del_mov = None, tot_chn = None, tot_shw = None, tot_mov = None ):
		if self.db is not None:
			self.db.UpdateStatus( status, lastupdate, filmupdate, fullupdate, add_chn, add_shw, add_mov, del_chn, del_shw, del_mov, tot_chn, tot_shw, tot_mov )

	def SupportsUpdate( self ):
		if self.db is not None:
			return self.db.SupportsUpdate()
		return False

	def ftInit( self ):
		if self.db is not None:
			return self.db.ftInit()
		return False

	def ftUpdateStart( self, full ):
		if self.db is not None:
			return self.db.ftUpdateStart( full )
		return ( 0, 0, 0, )

	def ftUpdateEnd( self, delete ):
		if self.db is not None:
			return self.db.ftUpdateEnd( delete )
		return ( 0, 0, 0, 0, 0, 0, )

	def ftInsertFilm( self, film, commit = True ):
		if self.db is not None:
			return self.db.ftInsertFilm( film, commit )
		return ( 0, 0, 0, 0, )
