# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import sys, urllib
import xbmcplugin, xbmcgui

from classes.settings import Settings

# -- Classes ------------------------------------------------
class InitialUI( object ):
	def __init__( self, handle, sortmethods = [ xbmcplugin.SORT_METHOD_TITLE ] ):
		self.handle			= handle
		self.sortmethods	= sortmethods
		self.channelid		= 0
		self.initial		= ''
		self.count			= 0

	def Begin( self, channelid ):
		self.channelid = channelid
		for method in self.sortmethods:
			xbmcplugin.addSortMethod( self.handle, method )

	def Add( self, altname = None ):
		if altname is None:
			resultingname = '%s (%d)' % ( self.initial if self.initial != ' ' and self.initial != '' else ' No Title', self.count )
		else:
			resultingname = altname
		li = xbmcgui.ListItem( label = resultingname )
		xbmcplugin.addDirectoryItem(
			handle	= self.handle,
			url		= self.build_url( {
				'mode': "shows",
				'channel': self.channelid,
				'initial': self.initial,
				'count': self.count
			} ),
			listitem = li,
			isFolder = True
		)

	def End( self ):
		xbmcplugin.endOfDirectory( self.handle )

	def build_url( self, query ):
		return sys.argv[0] + '?' + urllib.urlencode( query )
