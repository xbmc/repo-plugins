# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import sys, urllib
import xbmcplugin, xbmcgui

from resources.lib.show import Show

# -- Classes ------------------------------------------------
class ShowUI( Show ):
	def __init__( self, handle, sortmethods = None ):
		self.base_url		= sys.argv[0]
		self.handle			= handle
		self.sortmethods	= sortmethods if sortmethods is not None else [ xbmcplugin.SORT_METHOD_TITLE ]
		self.querychannelid	= 0

	def Begin( self, channelid ):
		self.querychannelid = channelid
		for method in self.sortmethods:
			xbmcplugin.addSortMethod( self.handle, method )

	def Add( self, altname = None ):
		if altname is not None:
			resultingname = altname
		elif self.querychannelid == '0':
			resultingname = self.show + ' [' + self.channel + ']'
		else:
			resultingname = self.show
		li = xbmcgui.ListItem( label = resultingname )
		xbmcplugin.addDirectoryItem(
			handle	= self.handle,
			url		= self.build_url( {
				'mode': "films",
				'show': self.id
			} ),
			listitem = li,
			isFolder = True
		)

	def End( self ):
		xbmcplugin.endOfDirectory( self.handle )

	def build_url( self, query ):
		return self.base_url + '?' + urllib.urlencode( query )
