# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import sys, urllib
import xbmcplugin, xbmcgui

from classes.channel import Channel
from classes.settings import Settings

# -- Classes ------------------------------------------------
class ChannelUI( Channel ):
	def __init__( self, handle, sortmethods = [ xbmcplugin.SORT_METHOD_TITLE ], next = 'initial' ):
		self.base_url		= sys.argv[0]
		self.next			= next
		self.handle			= handle
		self.sortmethods	= sortmethods
		self.count			= 0

	def Begin( self ):
		for method in self.sortmethods:
			xbmcplugin.addSortMethod( self.handle, method )

	def Add( self, altname = None ):
		resultingname = self.channel if self.count == 0 else '%s (%d)' % ( self.channel, self.count, )
		li = xbmcgui.ListItem( label = resultingname if altname is None else altname )
		xbmcplugin.addDirectoryItem(
			handle	= self.handle,
			url		= self.build_url( {
				'mode': self.next,
				'channel': self.id
			} ),
			listitem = li,
			isFolder = True
		)

	def End( self ):
		xbmcplugin.endOfDirectory( self.handle )

	def build_url( self, query ):
		return self.base_url + '?' + urllib.urlencode( query )
