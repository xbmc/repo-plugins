# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------

# -- Classes ------------------------------------------------
class Film( object ):
	def __init__( self ):
		self.id				= 0
		self.title			= u''
		self.show			= u''
		self.channel		= u''
		self.description	= u''
		self.seconds		= 0
		self.size			= 0
		self.aired			= u''
		self.url_sub		= u''
		self.url_video		= u''
		self.url_video_sd	= u''
		self.url_video_hd	= u''
