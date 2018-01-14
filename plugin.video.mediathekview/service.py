# -*- coding: utf-8 -*-
#
# MIT License
#
# Copyright (c) 2017-2018, Leo Moll
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -- Imports ------------------------------------------------
from __future__ import unicode_literals  # ,absolute_import, division

import xbmc

from resources.lib.kodi.KodiAddon import KodiService

from resources.lib.notifier import Notifier
from resources.lib.settings import Settings
from resources.lib.updater import MediathekViewUpdater

# -- Classes ------------------------------------------------
class MediathekViewMonitor( xbmc.Monitor ):
	def __init__( self, service ):
		super( MediathekViewMonitor, self ).__init__()
		self.service	= service
		self.logger		= service.getNewLogger( 'Monitor' )
		self.logger.info( 'Startup' )

	def __del__( self ):
		self.logger.info( 'Shutdown' )

	def onSettingsChanged( self ):
		self.service.ReloadSettings()

class MediathekViewService( KodiService ):
	def __init__( self ):
		super( MediathekViewService, self ).__init__()
		self.setTopic( 'Service' )
		self.settings	= Settings()
		self.notifier	= Notifier()
		self.monitor	= MediathekViewMonitor( self )
		self.updater	= MediathekViewUpdater( self.getNewLogger( 'Updater' ), self.notifier, self.settings, self.monitor )

	def Init( self ):
		self.info( 'Init' )
		self.updater.Init()

	def Run( self ):
		self.info( 'Starting up...' )
		while not self.monitor.abortRequested():
			updateop = self.updater.GetCurrentUpdateOperation()
			if updateop == 1:
				# full update
				self.info( 'Initiating full update...' )
				self.updater.Update( True )
			elif updateop == 2:
				# differential update
				self.info( 'Initiating differential update...' )
				self.updater.Update( False )
			# Sleep/wait for abort for 60 seconds
			if self.monitor.waitForAbort( 60 ):
				# Abort was requested while waiting. We should exit
				break
		self.info( 'Shutting down...' )

	def Exit( self ):
		self.info( 'Exit' )
		self.updater.Exit()

	def ReloadSettings( self ):
		# TODO: support online reconfiguration
		pass

# -- Main Code ----------------------------------------------
if __name__ == '__main__':
	service = MediathekViewService()
	service.Init()
	service.Run()
	service.Exit()
	del service
