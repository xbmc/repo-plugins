# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmc

from de.yeasoft.base.Logger import Logger

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
#		formatMessage = self._getFormatMessage( message )
#		xbmc.log( self.prefix + formatMessage.format( *parts ), level = level )

#	def _getFormatMessage( self, message ):
#		j = message.find( '{}' )
#		if j == -1:
#			return message
#		formatMessage = ''
#		i = 0
#		index = 0
#		while j != -1:
#			formatMessage += message[i:j] + '{' + str( index ) + '}'
#			i = j + len( '{}' )
#			j = message.find( '{}', i )
#			index += 1
#		formatMessage += message[i:]
#		return formatMessage
