# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------

# -- Classes ------------------------------------------------
class Logger( object ):
	def __init__( self, name, version, topic = None ):
		self.name		= name
		self.version	= version
		self.setTopic( topic )

	def getNewLogger( self, topic = None ):
		pass

	def setTopic( self, topic = None ):
		if topic == None:
			self.prefix = '[%s-%s]: ' % ( self.name, self.version )
		else:
			self.prefix = '[%s-%s:%s]: ' % ( self.name, self.version, topic )

	def debug( self, message, *args ):
		pass

	def info( self, message, *args ):
		pass

	def warn( self, message, *args ):
		pass

	def error( self, message, *args ):
		pass
