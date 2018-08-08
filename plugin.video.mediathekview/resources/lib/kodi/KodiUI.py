# -*- coding: utf-8 -*-
# Copyright 2017 Leo Moll and Dominik Schlösser
#

# -- Imports ------------------------------------------------
import xbmc
import xbmcgui
import xbmcaddon

# -- Classes ------------------------------------------------
class KodiUI( object ):

	def __init__( self ):
		self.addon			= xbmcaddon.Addon()
		self.language		= self.addon.getLocalizedString
		self.bgdialog		= KodiBGDialog()

	def GetEnteredText( self, deftext = None, heading = None, hidden = False ):
		heading = self.language( heading ).encode( 'utf-8' ) if isinstance( heading, int ) else heading if heading is not None else ''
		deftext = self.language( deftext ).encode( 'utf-8' ) if isinstance( deftext, int ) else deftext if deftext is not None else ''
		keyboard = xbmc.Keyboard( deftext, heading, 1 if hidden else 0 )
		keyboard.doModal()
		if keyboard.isConfirmed():
			return ( keyboard.getText(), True, )
		return ( deftext.encode( 'utf-8' ), False, )

	def ShowOkDialog( self, heading = None, line1 = None, line2 = None, line3 = None  ):
		heading = self.language( heading ).decode( 'utf-8' ) if isinstance( heading, int ) else heading if heading is not None else ''
		line1 = self.language( line1 ).decode( 'utf-8' ) if isinstance( line1, int ) else line1 if line1 is not None else ''
		line2 = self.language( line2 ).decode( 'utf-8' ) if isinstance( line2, int ) else line2 if line2 is not None else ''
		line3 = self.language( line3 ).decode( 'utf-8' ) if isinstance( line3, int ) else line3 if line3 is not None else ''
		dialog = xbmcgui.Dialog()
		ok = dialog.ok( heading, line1, line2, line3 )
		del dialog
		return ok

	def ShowNotification( self, heading, message, icon = xbmcgui.NOTIFICATION_INFO, time = 5000, sound = True ):
		heading = self.language( heading ) if isinstance( heading, int ) else heading
		message = self.language( message ) if isinstance( message, int ) else message
		xbmcgui.Dialog().notification( heading, message, icon, time, sound )

	def ShowWarning( self, heading, message, time = 5000, sound = True ):
		self.ShowNotification( heading, message, xbmcgui.NOTIFICATION_WARNING, time, sound )

	def ShowError( self, heading, message, time = 5000, sound = True ):
		self.ShowNotification( heading, message, xbmcgui.NOTIFICATION_ERROR, time, sound )

	def ShowBGDialog( self, heading = None, message = None ):
		self.bgdialog.Create( heading, message )

	def UpdateBGDialog( self, percent, heading = None, message = None ):
		self.bgdialog.Update( percent, heading, message )

	def HookBGDialog( self, blockcount, blocksize, totalsize ):
		self.bgdialog.UrlRetrieveHook( blockcount, blocksize, totalsize )

	def CloseBGDialog( self ):
		self.bgdialog.Close()

class KodiBGDialog( object ):
	def __init__( self ):
		self.language		= xbmcaddon.Addon().getLocalizedString
		self.bgdialog= None

	def __del__( self ):
		self.Close()

	def Create( self, heading = None, message = None ):
		heading = self.language( heading ) if isinstance( heading, int ) else heading
		message = self.language( message ) if isinstance( message, int ) else message
		if self.bgdialog is None:
			self.bgdialog = xbmcgui.DialogProgressBG()
			self.bgdialog.create( heading, message )
		else:
			self.bgdialog.update( 0, heading, message )

	def Update( self, percent, heading = None, message = None ):
		if self.bgdialog is not None:
			heading = self.language( heading ) if isinstance( heading, int ) else heading
			message = self.language( message ) if isinstance( message, int ) else message
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
