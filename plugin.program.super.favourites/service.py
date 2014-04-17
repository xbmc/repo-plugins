#
#       Copyright (C) 2014
#       Sean Poyser (seanpoyser@gmail.com)
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import utils
utils.Verify()

import xbmc
import os

class MyMonitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)
        self.hotkey = utils.ADDON.getSetting('HOTKEY')


    def onSettingsChanged(self):
        hotkey = utils.ADDON.getSetting('HOTKEY')

        if self.hotkey == hotkey:
            return

        self.hotkey = hotkey

        utils.DeleteKeymap()
        utils.VerifyKeymap()


monitor = MyMonitor()

while (not xbmc.abortRequested):
    xbmc.sleep(1000)

del monitor