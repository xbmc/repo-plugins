# -*- coding: utf-8 -*-
"""
The film UI module

Copyright 2017-20180 Leo Moll and Dominik Schlösser
"""

# pylint: disable=import-error
# pylint: disable=mixed-indentation, bad-whitespace, bad-continuation, missing-docstring

# -- Imports ------------------------------------------------
import os

import xbmcgui
import xbmcplugin

from resources.lib.film import Film
from resources.lib.settings import Settings

# -- Classes ------------------------------------------------
class FilmUI( Film ):
	def __init__( self, plugin, sortmethods = None ):
		Film.__init__( self )
		self.plugin			= plugin
		self.handle			= plugin.addon_handle
		self.settings		= Settings()
		self.sortmethods	= sortmethods if sortmethods is not None else [
			xbmcplugin.SORT_METHOD_TITLE,
			xbmcplugin.SORT_METHOD_DATE,
			xbmcplugin.SORT_METHOD_DURATION,
			xbmcplugin.SORT_METHOD_SIZE
		]
		self.showshows		= False
		self.showchannels	= False

	def Begin( self, showshows, showchannels ):
		self.showshows		= showshows
		self.showchannels	= showchannels
		# xbmcplugin.setContent( self.handle, 'tvshows' )
		for method in self.sortmethods:
			xbmcplugin.addSortMethod( self.handle, method )

	def Add( self, alttitle = None, totalItems = None ):
		( videourl, listitem, ) = self.get_list_item( alttitle )

		# create context menu
		contextmenu = []
		if self.url_video or self.url_video_sd or self.url_video_hd:
			# play with subtitles
			if not self.settings.autosub and self.url_sub:
				contextmenu.append( (
					self.plugin.language( 30921 ),
					'RunPlugin({})'.format(
						self.plugin.build_url( {
							'mode': "playwithsrt",
							'id': self.id,
							'only_set_resolved_url': False
						} )
					)
				) )

			# Download movie
			contextmenu.append( (
				self.plugin.language( 30922 ),
				'RunPlugin({})'.format(
					self.plugin.build_url( {
						'mode': "downloadmv",
						'id': self.id,
						'quality': 1
					} )
				)
			) )
			if self.url_video_hd:
				# Download HD movie
				contextmenu.append( (
					self.plugin.language( 30923 ),
					'RunPlugin({})'.format(
						self.plugin.build_url( {
							'mode': "downloadmv",
							'id': self.id,
							'quality': 2
						} )
					)
				) )
			# Download TV episode
			contextmenu.append( (
				self.plugin.language( 30924 ),
				'RunPlugin({})'.format(
					self.plugin.build_url( {
						'mode': "downloadep",
						'id': self.id,
						'quality': 1
					} )
				)
			) )
			if self.url_video_hd:
				# Download HD TV episode
				contextmenu.append( (
					self.plugin.language( 30925 ),
					'RunPlugin({})'.format(
						self.plugin.build_url( {
							'mode': "downloadep",
							'id': self.id,
							'quality': 2
						} )
					)
				) )
			listitem.addContextMenuItems( contextmenu )


		if self.settings.autosub and self.url_sub:
			videourl = self.plugin.build_url( {
				'mode': "playwithsrt",
				'id': self.id,
				'only_set_resolved_url': True
			} )

		if totalItems is not None:
			xbmcplugin.addDirectoryItem(
				handle		= self.handle,
				url			= videourl,
				listitem	= listitem,
				isFolder	= False,
				totalItems	= totalItems
			)
		else:
			xbmcplugin.addDirectoryItem(
				handle		= self.handle,
				url			= videourl,
				listitem	= listitem,
				isFolder	= False
			)

	def End( self ):
		xbmcplugin.endOfDirectory( self.handle, cacheToDisc = False )

	def get_list_item( self, alttitle, film = None ):
		if film is None:
			film = self
		# get the best url
		videourl = film.url_video_hd if ( film.url_video_hd != "" and self.plugin.settings.preferhd ) else film.url_video if film.url_video != "" else film.url_video_sd
		videohds = " (HD)" if ( film.url_video_hd != "" and self.plugin.settings.preferhd ) else ""
		# exit if no url supplied
		if videourl == "":
			return None

		if alttitle is not None:
			resultingtitle = alttitle
		else:
			if self.showshows:
				resultingtitle = film.show + ': ' + film.title
			else:
				resultingtitle = film.title
			if self.showchannels:
				resultingtitle += ' [' + film.channel + ']'

		info_labels = {
			'title' : resultingtitle + videohds,
			'sorttitle' : resultingtitle.lower(),
			'tvshowtitle' : film.show,
			'plot' : film.description
		}

		if film.size > 0:
			info_labels['size'] = film.size * 1024 * 1024

		if film.seconds > 0:
			info_labels['duration'] = film.seconds

		if film.aired is not None:
			airedstring = '%s' % film.aired
			if airedstring[:4] != '1970':
				info_labels['date']		= airedstring[8:10] + '-' + airedstring[5:7] + '-' + airedstring[:4]
				info_labels['aired']		= airedstring
				info_labels['dateadded']	= airedstring

		icon = os.path.join( self.plugin.addon.getAddonInfo( 'path' ), 'resources', 'icons', film.channel.lower() + '-m.png' )

		listitem = xbmcgui.ListItem( resultingtitle, path = videourl )
		listitem.setInfo( type = 'video', infoLabels = info_labels )
		listitem.setProperty( 'IsPlayable', 'true' )
		listitem.setArt( {
			'thumb': icon,
			'icon': icon
		} )
		return ( videourl, listitem )
