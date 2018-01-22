# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import os
import sys
import urllib

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

from resources.lib.kodi.KodiLogger import KodiLogger

# -- Classes ------------------------------------------------
class KodiAddon( KodiLogger ):
	def __init__( self ):
		self.addon			= xbmcaddon.Addon()
		self.addon_id		= self.addon.getAddonInfo( 'id' )
		self.icon			= self.addon.getAddonInfo( 'icon' )
		self.fanart			= self.addon.getAddonInfo( 'fanart' )
		self.version		= self.addon.getAddonInfo( 'version' )
		self.path			= self.addon.getAddonInfo( 'path' )
		self.datapath		= xbmc.translatePath( self.addon.getAddonInfo('profile').decode('utf-8') )
		self.language		= self.addon.getLocalizedString
		KodiLogger.__init__( self, self.addon_id, self.version )

	def getSetting( self, setting_id ):
		return self.addon.getSetting( setting_id )

	def setSetting( self, setting_id, value ):
		return self.addon.setSetting( setting_id, value )

	def doAction( self, action ):
		self.debug( 'Triggered action {}', action )
		xbmc.executebuiltin( 'Action({})'.format( action ) )

class KodiService( KodiAddon ):
	def __init__( self ):
		KodiAddon.__init__( self )

class KodiPlugin( KodiAddon ):
	def __init__( self ):
		KodiAddon.__init__( self )
		self.base_url		= sys.argv[0]
		self.addon_handle	= int( sys.argv[1] )

	def build_url( self, query ):
		return self.base_url + '?' + urllib.urlencode( query )

	def runPlugin( self, params ):
		xbmc.executebuiltin( 'RunPlugin({})'.format( self.build_url( params ) ) )

	def addActionItem( self, name, params ):
		self.addDirectoryItem( name, params, False )

	def addFolderItem( self, name, params ):
		self.addDirectoryItem( name, params, True )

	def addDirectoryItem( self, name, params, isFolder ):
		if isinstance( name, int ):
			name = self.language( name )
		li = xbmcgui.ListItem( name )
		xbmcplugin.addDirectoryItem(
			handle		= self.addon_handle,
			url			= self.build_url( params ),
			listitem	= li,
			isFolder	= isFolder
		)

	def endOfDirectory( self, succeeded = True, updateListing = False, cacheToDisc = True ):
		xbmcplugin.endOfDirectory( self.addon_handle, succeeded, updateListing, cacheToDisc )


class KodiInterlockedMonitor( xbmc.Monitor ):
	def __init__( self, service, setting_id ):
		super( KodiInterlockedMonitor, self ).__init__()
		self.instance_id	= ''.join( format( x, '02x' ) for x in bytearray( os.urandom( 16 ) ) )
		self.setting_id		= setting_id
		self.service		= service

	def RegisterInstance( self, waittime = 1 ):
		if self.BadInstance():
			self.service.info( 'Found other instance with id {}', self.instance_id )
			self.service.info( 'Startup delayed by {} second(s) waiting the other instance to shut down', waittime )
			self.service.setSetting( self.setting_id, self.instance_id )
			xbmc.Monitor.waitForAbort( self, waittime )
		else:
			self.service.setSetting( self.setting_id, self.instance_id )

	def UnregisterInstance( self ):
		self.service.setSetting( self.setting_id, '' )

	def BadInstance( self ):
		instance_id = self.service.getSetting( self.setting_id )
		return len( instance_id ) > 0 and self.instance_id != instance_id

	def abortRequested( self ):
		return self.BadInstance() or xbmc.Monitor.abortRequested( self )

	def waitForAbort( self, timeout = None ):
		if timeout is None:
			# infinite wait
			while not self.abortRequested():
				if xbmc.Monitor.waitForAbort( self, 1 ):
					return True
			return True
		else:
			for _ in range( timeout ):
				if self.BadInstance() or xbmc.Monitor.waitForAbort( self, 1 ):
					return True
			return self.BadInstance()
