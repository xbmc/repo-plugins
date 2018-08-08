# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import time
import xbmc
import xbmcaddon

# -- Classes ------------------------------------------------
class Settings( object ):
	def __init__( self ):
		self.Load()

	def Load( self ):
		addon = xbmcaddon.Addon()
		self.datapath		= xbmc.translatePath( addon.getAddonInfo('profile').decode('utf-8') )
		self.firstrun		= addon.getSetting( 'firstrun' ) == 'true'
		# general
		self.preferhd		= addon.getSetting( 'quality' ) == 'true'
		self.autosub		= addon.getSetting( 'autosub' ) == 'true'
		self.nofuture		= addon.getSetting( 'nofuture' ) == 'true'
		self.minlength		= int( float( addon.getSetting( 'minlength' ) ) ) * 60
		self.groupshows		= addon.getSetting( 'groupshows' ) == 'true'
		self.maxresults		= int( addon.getSetting( 'maxresults' ) )
		self.maxage			= int( addon.getSetting( 'maxage' ) ) * 86400
		self.recentmode		= int( addon.getSetting( 'recentmode' ) )
		# database
		self.type			= int( addon.getSetting( 'dbtype' ) )
		self.host			= addon.getSetting( 'dbhost' )
		self.port			= int( addon.getSetting( 'dbport' ) )
		self.user			= addon.getSetting( 'dbuser' )
		self.password		= addon.getSetting( 'dbpass' )
		self.database		= addon.getSetting( 'dbdata' )
		self.updmode		= int( addon.getSetting( 'updmode' ) )
		self.updinterval	= int( float( addon.getSetting( 'updinterval' ) ) ) * 3600
		# download
		self.downloadpathep		= addon.getSetting( 'downloadpathep' )
		self.downloadpathmv		= addon.getSetting( 'downloadpathmv' )
		self.moviefolders		= addon.getSetting( 'moviefolders' ) == 'true'
		self.movienamewithshow	= addon.getSetting( 'movienamewithshow' ) == 'true'
		self.reviewname			= addon.getSetting( 'reviewname' ) == 'true'
		self.downloadsrt		= addon.getSetting( 'downloadsrt' ) == 'true'
		self.makenfo			= int( addon.getSetting( 'makenfo' ) )
		# update stuff
		if len( self.downloadpathep ) == 0:
			self.downloadpathep = addon.getSetting( 'downloadpath' )
			if len( self.downloadpathep ) > 0:
				addon.setSetting( 'downloadpathep', self.downloadpathep )


	def Reload( self ):
		addon = xbmcaddon.Addon()
		# check if the db configration has changed
		dbchanged = self.type != int( addon.getSetting( 'dbtype' ) )
		dbchanged = dbchanged or self.host != addon.getSetting( 'dbhost' )
		dbchanged = dbchanged or self.port != int( addon.getSetting( 'dbport' ) )
		dbchanged = dbchanged or self.user != addon.getSetting( 'dbuser' )
		dbchanged = dbchanged or self.password != addon.getSetting( 'dbpass' )
		dbchanged = dbchanged or self.database != addon.getSetting( 'dbdata' )
		# reload configuration
		self.Load()
		# return change status
		return dbchanged

	@staticmethod
	def IsUpdateTriggered():
		if xbmcaddon.Addon().getSetting( 'updatetrigger' ) == 'true':
			xbmcaddon.Addon().setSetting( 'updatetrigger', 'false' )
			return True
		return False

	@staticmethod
	def IsUserAlive():
		return int( time.time() ) - int( float( xbmcaddon.Addon().getSetting( 'lastactivity' ) ) ) < 7200

	@staticmethod
	def TriggerUpdate():
		xbmcaddon.Addon().setSetting( 'updatetrigger', 'true' )

	@staticmethod
	def ResetUserActivity():
		xbmcaddon.Addon().setSetting( 'lastactivity', '{}'.format( time.time() ) )

	@staticmethod
	def SaveUpdateInstance( instanceid ):
		xbmcaddon.Addon().setSetting( 'updateinid', instanceid )

	def HandleUpdateOnStart( self ):
		if self.updmode == 2:
			if xbmcaddon.Addon().getSetting( 'instanceid' ) != xbmcaddon.Addon().getSetting( 'updateinid' ):
				self.TriggerUpdate()

	def HandleFirstRun( self ):
		if self.firstrun:
			self.firstrun = False
			xbmcaddon.Addon().setSetting( 'firstrun', 'false' )
			return True
		return False
