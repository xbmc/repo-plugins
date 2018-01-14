# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmc

from resources.lib.base.Logger import Logger

# -- Classes ------------------------------------------------
class KodiLogger( Logger ):

	def __init__( self, name, version, topic = None ):
		super( KodiLogger, self ).__init__( name, version, topic)

	def getNewLogger( self, topic = None ):
		return KodiLogger( self.name, self.version, topic )

	def debug( self, message, *args ):
		self._log( xbmc.LOGDEBUG, message, *args )

	def info( self, message, *args ):
		self._log( xbmc.LOGNOTICE, message, *args )

	def warn( self, message, *args ):
		self._log( xbmc.LOGWARNING, message, *args )

	def error( self, message, *args ):
		self._log( xbmc.LOGERROR, message, *args )

	def _log( self, level, message, *args ):
		parts = []
		for arg in args:
			part = arg
			if isinstance( arg, basestring ):
				part = arg # arg.decode('utf-8')
			parts.append( part )
		xbmc.log( self.prefix + message.format( *parts ), level = level )
