# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import os
import xbmc,xbmcaddon

# -- Classes ------------------------------------------------
class Settings( object ):
	def __init__( self ):
		self.addon = xbmcaddon.Addon()
		self.Reload()

	def Reload( self ):
		self.datapath		= os.path.join( xbmc.translatePath( "special://masterprofile" ).decode('utf-8'), 'addon_data', self.addon.getAddonInfo( 'id' ).decode('utf-8') )
		self.firstrun		= self.addon.getSetting( 'firstrun' ) == 'true'
		self.preferhd		= self.addon.getSetting( 'quality' ) == 'true'
		self.nofuture		= self.addon.getSetting( 'nofuture' ) == 'true'
		self.minlength		= int( float( self.addon.getSetting( 'minlength' ) ) ) * 60
		self.groupshows		= self.addon.getSetting( 'groupshows' ) == 'true'
		self.downloadpath	= self.addon.getSetting( 'downloadpath' )
		self.type			= self.addon.getSetting( 'dbtype' )
		self.host			= self.addon.getSetting( 'dbhost' )
		self.user			= self.addon.getSetting( 'dbuser' )
		self.password		= self.addon.getSetting( 'dbpass' )
		self.database		= self.addon.getSetting( 'dbdata' )
		self.updenabled		= self.addon.getSetting( 'updenabled' ) == 'true'
		self.updinterval	= int( float( self.addon.getSetting( 'updinterval' ) ) ) * 3600
		self.updxzbin		= self.addon.getSetting( 'updxzbin' )

	def HandleFirstRun( self ):
		if self.firstrun:
			self.firstrun = False
			self.addon.setSetting( 'firstrun', 'false' )
			return True
		return False
