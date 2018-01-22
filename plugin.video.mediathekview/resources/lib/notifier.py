# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
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
