# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import datetime
import xbmcaddon

from resources.lib.kodi.KodiUI import KodiUI

# -- Classes ------------------------------------------------
class Notifier( KodiUI ):
	def __init__( self ):
		super( Notifier, self ).__init__()
		self.language		= xbmcaddon.Addon().getLocalizedString

	def ShowDatabaseError( self, err ):
		self.ShowError( 30951, '{}'.format( err ) )

	def ShowDownloadError( self, name, err ):
		self.ShowError( 30952, self.language( 30953 ).format( name, err ) )

	def ShowMissingExtractorError( self ):
		self.ShowError( 30952, 30954, time = 10000 )

	def ShowLimitResults( self, maxresults ):
		self.ShowNotification( 30980, self.language( 30981 ).format( maxresults ) )

	def ShowOutdatedUnknown( self ):
		self.ShowWarning( 30982, 30966 )

	def ShowOutdatedKnown( self, status ):
		updatetype = self.language( 30972 if status['fullupdate'] > 0 else 30973 )
		updatetime = datetime.datetime.fromtimestamp( status['lastupdate'] ).strftime( '%Y-%m-%d %H:%M:%S' ),
		updinfo = self.language( 30983 )
		self.ShowWarning( 30982, updinfo.format( updatetype, updatetime[0] ) )

	def ShowDownloadProgress( self ):
		self.ShowBGDialog( 30955 )

	def UpdateDownloadProgress( self, percent, message = None ):
		self.UpdateBGDialog( percent, message = message )

	def HookDownloadProgress( self, blockcount, blocksize, totalsize ):
		self.HookBGDialog( blockcount, blocksize, totalsize )

	def CloseDownloadProgress( self ):
		self.CloseBGDialog()

	def ShowUpdateProgress( self ):
		self.ShowBGDialog( 30956 )

	def UpdateUpdateProgress( self, percent, count, channels, shows, movies ):
		message = self.language( 30957 ) % ( count, channels, shows, movies )
		self.UpdateBGDialog( percent, message = message )

	def CloseUpdateProgress( self ):
		self.CloseBGDialog()

	def ShowUpdatingScheme( self ):
		self.ShowOkDialog( 30984, 30985 )

	def ShowUpdateSchemeProgress( self ):
		self.ShowBGDialog( 30984 )

	def UpdateUpdateSchemeProgress( self, percent ):
		self.UpdateBGDialog( percent, message = '' )

	def CloseUpdateSchemeProgress( self ):
		self.CloseBGDialog()
