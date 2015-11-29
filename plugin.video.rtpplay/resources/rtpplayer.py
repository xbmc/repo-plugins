#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
 Author: enen92 

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
 
"""

import xbmc
from watched import *

class RTPPlayer(xbmc.Player):
	def __init__(self,videoarray,mainurl):
		self._playbackLock = True
		print("Player has been created")
		self.array = videoarray
		self.urlwatched = mainurl
		self.timepos = 0
		self.totalTime = 0
		self.playingfile = ''
            
	def onPlayBackStarted(self):
		self._playbackLock = True
		self.playingfile = self.getPlayingFile()
		self.totalTime = self.getTotalTime()
                              
	def onPlayBackStopped(self):
		print("player stopped")
		self._playbackLock = False
		try:
			if float(self.timepos/self.totalTime) > 0.92 and self.playingfile == self.array[-1]:
				mark_as_watched(self.urlwatched)
			else: pass
		except: pass

	def onPlayBackEnded(self):              
		self.onPlayBackStopped()
		print("playbackended")

	def _trackPosition(self):
		try:
			self.timepos = self.getTime()
		except: print('Error trackposition')

