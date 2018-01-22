# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmcgui
import xbmcplugin

import resources.lib.mvutils as mvutils

from resources.lib.channel import Channel

# -- Classes ------------------------------------------------
class ChannelUI( Channel ):
	def __init__( self, plugin, sortmethods = None, nextdir = 'initial' ):
		self.plugin			= plugin
		self.handle			= plugin.addon_handle
		self.nextdir		= nextdir
		self.sortmethods	= sortmethods if sortmethods is not None else [ xbmcplugin.SORT_METHOD_TITLE ]
		self.count			= 0

	def Begin( self ):
		for method in self.sortmethods:
			xbmcplugin.addSortMethod( self.handle, method )

	def Add( self, altname = None ):
		resultingname = self.channel if self.count == 0 else '%s (%d)' % ( self.channel, self.count, )
		li = xbmcgui.ListItem( label = resultingname if altname is None else altname )
		icon = 'special://home/addons/' + self.plugin.addon_id + '/resources/icons/' + self.channel.lower() + '-m.png'
		li.setArt( {
			'thumb': icon,
			'icon': icon
		} )
		xbmcplugin.addDirectoryItem(
			handle	= self.handle,
			url		= mvutils.build_url( {
				'mode': self.nextdir,
				'channel': self.id
			} ),
			listitem = li,
			isFolder = True
		)

	def End( self ):
		xbmcplugin.endOfDirectory( self.handle )
