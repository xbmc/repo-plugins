# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll
#

class DatabaseCorrupted( RuntimeError ):
	"""This exception is raised when the database throws errors during update"""

class DatabaseLost( RuntimeError ):
	"""This exception is raised when the connection to the database is lost during update"""

class ExitRequested( Exception ):
	"""This exception is thrown if the addon is shut down by Kodi or by another same addon"""
