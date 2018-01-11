# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmc, xbmcgui

# -- Classes ------------------------------------------------
class KodiUI( object ):

	def __init__( self ):
		self.bgdialog		= None

	def GetEnteredText( self, deftext = '', heading = '', hidden = False ):
		keyboard = xbmc.Keyboard( deftext, heading, 1 if hidden else 0 )
		keyboard.doModal()
		if keyboard.isConfirmed():
			return keyboard.getText()
		return deftext

	def ShowNotification( self, heading, message, icon = xbmcgui.NOTIFICATION_INFO, time = 5000, sound = True ):
		xbmcgui.Dialog().notification( heading, message, icon, time, sound )

	def ShowWarning( self, heading, message, time = 5000, sound = True ):
		xbmcgui.Dialog().notification( heading, message, xbmcgui.NOTIFICATION_WARNING, time, sound )

	def ShowError( self, heading, message, time = 5000, sound = True ):
		xbmcgui.Dialog().notification( heading, message, xbmcgui.NOTIFICATION_ERROR, time, sound )

	def ShowBGDialog( self, heading = None, message = None ):
		if self.bgdialog is None:
			self.bgdialog = xbmcgui.DialogProgressBG()
			self.bgdialog.create( heading, message )
		else:
			self.bgdialog.update( 0, heading, message )

	def UpdateBGDialog( self, percent, heading = None, message = None ):
		if self.bgdialog is not None:
			self.bgdialog.update( percent, heading, message )

	def CloseBGDialog( self ):
		if self.bgdialog is not None:
			self.bgdialog.close()
			del self.bgdialog
			self.bgdialog = None

class KodiBGDialog( object ):
	def __init__( self ):
		self.bgdialog= None

	def __del__( self ):
		self.Close()

	def Create( self, heading = None, message = None ):
		if self.bgdialog is None:
			self.bgdialog = xbmcgui.DialogProgressBG()
			self.bgdialog.create( heading, message )
		else:
			self.bgdialog.update( 0, heading, message )

	def Update( self, percent, heading = None, message = None ):
		if self.bgdialog is not None:
			self.bgdialog.update( percent, heading, message )

	def UrlRetrieveHook( self, blockcount, blocksize, totalsize ):
		downloaded = blockcount * blocksize
		if totalsize > 0:
			percent = int( (downloaded * 100) / totalsize )
			if self.bgdialog is not None:
				self.bgdialog.update( percent )

	def Close( self ):
		if self.bgdialog is not None:
			self.bgdialog.close()
			del self.bgdialog
			self.bgdialog = None
