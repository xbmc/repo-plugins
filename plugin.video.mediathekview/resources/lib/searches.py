"""
Management of recent searches

Copyright (c) 2018, Leo Moll

Licensed under MIT License
"""

# pylint: disable=import-error
# pylint: disable=mixed-indentation, bad-whitespace, bad-continuation, missing-docstring

# -- Imports ------------------------------------------------
import os
import json
import time

from contextlib import closing
from operator import itemgetter

import xbmcplugin

# -- Classes ------------------------------------------------
class RecentSearches( object ):
	def __init__( self, plugin, extendedsearch, sortmethods = None ):
		self.plugin			= plugin
		self.handle			= plugin.addon_handle
		self.sortmethods	= sortmethods if sortmethods is not None else [ xbmcplugin.SORT_METHOD_TITLE ]
		self.extendedsearch	= extendedsearch
		self.recents		= []
		self.datafile		= os.path.join(
			self.plugin.settings.datapath,
			'recent_ext_searches.json' if extendedsearch else 'recent_std_searches.json'
		)

	def load( self ):
		try:
			with closing( open( self.datafile ) ) as json_file:
				data = json.load( json_file )
				if isinstance( data, list ):
					self.recents = sorted( data, key = itemgetter( 'when' ), reverse = True )
		# pylint: disable=broad-except
		except Exception as err:
			self.plugin.error( 'Failed to load last searches file {}: {}', self.datafile, err )
		return self

	def save( self ):
		data = sorted( self.recents, key = itemgetter( 'when' ), reverse = True )
		try:
			with closing( open( self.datafile, 'w' ) ) as json_file:
				json.dump( data, json_file )
		# pylint: disable=broad-except
		except Exception as err:
			self.plugin.error( 'Failed to write last searches file {}: {}', self.datafile, err )
		return self

	def add( self, search ):
		slow = search.decode('utf-8').lower()
		try:
			for entry in self.recents:
				if entry['search'].lower() == slow:
					entry['when'] = int( time.time() )
					return self
		# pylint: disable=broad-except
		except Exception as err:
			self.plugin.error( 'Recent searches list is broken (error {}) - cleaning up', err )
			self.recents = []
		self.recents.append( {
			'search':			search.decode('utf-8'),
			'when':				int( time.time() )
		} )
		return self

	def delete( self, search ):
		slow = search.decode('utf-8').lower()
		try:
			for entry in self.recents:
				if entry['search'].lower() == slow:
					self.recents.remove(entry)
					return self
		# pylint: disable=broad-except
		except Exception as err:
			self.plugin.error( 'Recent searches list is broken (error {}) - cleaning up', err )
			self.recents = []
		return self

	def populate( self ):
		for entry in self.recents:
			self.plugin.addFolderItem(
				entry['search'],
				{
					'mode': "research",
					'search': entry['search'].encode('utf-8'),
					'extendedsearch': self.extendedsearch
				},
				[
					(
						self.plugin.language( 30932 ),
						'RunPlugin({})'.format(
							self.plugin.build_url( {
								'mode': "delsearch",
								'search': entry['search'].encode('utf-8'),
								'extendedsearch': self.extendedsearch
							} )
						)
					)
				]
			)
