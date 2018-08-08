# -*- coding: utf-8 -*-
# Copyright (c) 2017-2018, Leo Moll

# -- Imports ------------------------------------------------
import os
import sys
import argparse
import datetime
import defusedxml.ElementTree as ET

from resources.lib.base.Logger import Logger
from resources.lib.updater import MediathekViewUpdater

# -- Classes ------------------------------------------------
class Settings( object ):

	def __init__( self, args ):
		self.datapath		= args.path if args.dbtype == 'sqlite' else './'
		self.type			= { 'sqlite' : 0, 'mysql' : 1 }.get( args.dbtype, 0 )
		if self.type == 1:
			self.host			= args.host
			self.port			= int( args.port )
			self.user			= args.user
			self.password		= args.password
			self.database		= args.database
		self.autosub		= False
		self.nofuture		= True
		self.minlength		= 0
		self.maxage			= 86400
		self.recentmode		= 0
		self.groupshows		= False
		self.updmode		= 3
		self.updinterval	= args.intervall

	@staticmethod
	def Reload():
		return False

	@staticmethod
	def IsUpdateTriggered():
		return True

	@staticmethod
	def IsUserAlive():
		return True

	@staticmethod
	def TriggerUpdate():
		return True

	@staticmethod
	def ResetUserActivity():
		pass

class AppLogger( Logger ):

	def __init__( self, name, version, topic = None, verbosity = 0 ):
		super( AppLogger, self ).__init__( name, version, topic )
		self.verbosity = verbosity

	def getNewLogger( self, topic = None ):
		return AppLogger( self.name, self.version, topic, self.verbosity )

	def debug( self, message, *args ):
		self._log( 2, message, *args )

	def info( self, message, *args ):
		self._log( 1, message, *args )

	def warn( self, message, *args ):
		self._log( 0, message, *args )

	def error( self, message, *args ):
		self._log( -1, message, *args )

	def _log( self, level, message, *args ):
		parts = []
		for arg in args:
			part = arg
			if isinstance( arg, basestring ):
				part = arg # arg.decode('utf-8')
			parts.append( part )
		output = '{} {} {}{}'.format(
			datetime.datetime.now(),
			{ -1: 'ERROR', 0: 'WARNING', 1: 'NOTICE', 2: 'DEBUG' }.get( level, 2 ),
			self.prefix,
			message.format( *parts )
		)

		if level < 0:
			# error
			sys.stderr.write( output + '\n' )
			sys.stderr.flush()
		elif self.verbosity >= level:
			# other message
			print( output )

class Notifier( object ):
	def __init__( self ):
		pass
	def GetEnteredText( self, deftext = '', heading = '', hidden = False ):
		pass
	def ShowNotification( self, heading, message, icon = None, time = 5000, sound = True ):
		pass
	def ShowWarning( self, heading, message, time = 5000, sound = True ):
		pass
	def ShowError( self, heading, message, time = 5000, sound = True ):
		pass
	def ShowBGDialog( self, heading = None, message = None ):
		pass
	def UpdateBGDialog( self, percent, heading = None, message = None ):
		pass
	def CloseBGDialog( self ):
		pass
	def ShowDatabaseError( self, err ):
		pass
	def ShowDownloadError( self, name, err ):
		pass
	def ShowMissingExtractorError( self ):
		pass
	def ShowLimitResults( self, maxresults ):
		pass
	def ShowOutdatedUnknown( self ):
		pass
	def ShowOutdatedKnown( self, status ):
		pass
	def ShowDownloadProgress( self ):
		pass
	def UpdateDownloadProgress( self, percent, message = None ):
		pass
	def CloseDownloadProgress( self ):
		pass
	def ShowUpdateProgress( self ):
		pass
	def UpdateUpdateProgress( self, percent, count, channels, shows, movies ):
		pass
	def HookDownloadProgress( self, blockcount, blocksize, totalsize ):
		pass
	def CloseUpdateProgress( self ):
		pass
	def ShowUpdatingScheme( self ):
		pass
	def ShowUpdateSchemeProgress( self ):
		pass
	def UpdateUpdateSchemeProgress( self, percent ):
		pass
	def CloseUpdateSchemeProgress( self ):
		pass

class MediathekViewMonitor( object ):
	@staticmethod
	def abortRequested():
		return False

class UpdateApp( AppLogger ):
	def __init__( self ):
		try:
			self.mypath = os.path.dirname( sys.argv[0] )
			tree = ET.parse( self.mypath + '/addon.xml' )
			version = tree.getroot().attrib['version']
			AppLogger.__init__( self, os.path.basename( sys.argv[0] ), version )
		except Exception:
			AppLogger.__init__( self, os.path.basename( sys.argv[0] ), '0.0' )

	def Init( self ):
		parser = argparse.ArgumentParser(
			formatter_class = argparse.ArgumentDefaultsHelpFormatter,
			description = 'This is the standalone database updater. It downloads the current database update from mediathekview.de and integrates it in a local database'
		)
		parser.add_argument(
			'-v', '--verbose',
			default = 0,
			action = 'count',
			help = 'show progress messages'
		)
		subparsers = parser.add_subparsers(
			dest = 'dbtype',
			help = 'target database'
		)
		sqliteopts = subparsers.add_parser( 'sqlite', formatter_class = argparse.ArgumentDefaultsHelpFormatter )
		sqliteopts.add_argument(
			'-v', '--verbose',
			default = 0,
			action = 'count',
			help = 'show progress messages'
		)
		sqliteopts.add_argument(
			'-f', '--force',
			default = False,
			action = 'store_true',
			help = 'ignore the minimum interval'
		)
		sqliteopts.add_argument(
			'-i', '--intervall',
			default = 3600,
			type = int,
			action = 'store',
			help = 'minimum interval between updates'
		)
		sqliteopts.add_argument(
			'-p', '--path',
			dest = 'path',
			help = 'alternative path for the sqlite database',
			default = './'
		)
		mysqlopts = subparsers.add_parser( 'mysql', formatter_class = argparse.ArgumentDefaultsHelpFormatter )
		mysqlopts.add_argument(
			'-v', '--verbose',
			default = 0,
			action = 'count',
			help = 'show progress messages'
		)
		mysqlopts.add_argument(
			'-f', '--force',
			default = False,
			action = 'store_true',
			help = 'ignore the minimum interval'
		)
		mysqlopts.add_argument(
			'-i', '--intervall',
			default = 3600,
			type = int,
			action = 'store',
			help = 'minimum interval between updates'
		)
		mysqlopts.add_argument(
			'-H', '--host',
			dest = 'host',
			help = 'hostname or ip address',
			default = 'localhost'
		)
		mysqlopts.add_argument(
			'-P', '--port',
			dest = 'port',
			help = 'connection port',
			default = '3306'
		)
		mysqlopts.add_argument(
			'-u', '--user',
			dest = 'user',
			help = 'connection username',
			default = 'mediathekview'
		)
		mysqlopts.add_argument(
			'-p', '--password',
			dest = 'password',
			help = 'connection password',
			default = None
		)
		mysqlopts.add_argument(
			'-d', '--database',
			dest = 'database',
			default = 'mediathekview',
			help = 'database name'
		)
		self.args		= parser.parse_args()
		self.verbosity	= self.args.verbose

		self.info( 'Startup' )
		self.settings	= Settings( self.args )
		self.notifier	= Notifier()
		self.monitor	= MediathekViewMonitor()
		self.updater	= MediathekViewUpdater( self.getNewLogger( 'MediathekViewUpdater' ), self.notifier, self.settings, self.monitor )
		return self.updater.Init( convert = True )

	def Run( self ):
		self.info( 'Starting up...' )
		updateop = self.updater.GetCurrentUpdateOperation( self.args.force )
		if updateop == 1:
			# full update
			self.info( 'Initiating full update...' )
			self.updater.Update( True )
		elif updateop == 2:
			# differential update
			self.info( 'Initiating differential update...' )
			self.updater.Update( False )
		self.info( 'Exiting...' )

	def Exit( self ):
		self.updater.Exit()
