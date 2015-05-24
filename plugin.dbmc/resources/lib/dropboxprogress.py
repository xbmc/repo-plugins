#/*
# *      Copyright (C) 2013 Joost Kop
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import xbmcplugin
import xbmcgui

import time

from resources.lib.utils import *

class DropboxBackgroundProgress(xbmcgui.WindowXMLDialog):
    """
    Dialog class that shows the progress of a Dropbox background task.
    Using the DialogExtendedProgressBar.xml
    """
    #DialogExtendedProgressBar IDs
    HEADING_LABEL = 30
    LINE1_LABEL = 31
    PROGRESS_BAR = 32
    #ACTION IDs
    ACTION_SELECT_ITEM = 7
    
    parentWindow = None
    
    _heading = ''
    _visible = False
    _closedTime = 0
    TIMEOUT = 7 #secs

    def __init__(self, *args, **kwargs):
        super(DropboxBackgroundProgress, self).__init__(*args, **kwargs)

    def setHeading(self, heading):
        self._heading = heading
        
    def onInit(self):
        #super(DropboxBackgroundProgress, self).onInit()
        self.getControl(self.HEADING_LABEL).setLabel(self._heading)
        self._visible = True
        
    def update(self, itemsHandled, itemsTotal, text=None):
        if itemsTotal > 0:
            if not self._visible and (self._closedTime + self.TIMEOUT) < time.time():
                self.show()
            percent = 1
            if itemsHandled > 0:
                percent = (itemsHandled *100) / itemsTotal
            line1 = "(%s/%s)"%(itemsHandled, itemsTotal)
            if text:
                line1 += text
            #Some skins don't have the following items in the FileBrowser!
            try:
                self.getControl(self.LINE1_LABEL).setLabel(line1)
            except Exception as e:
                log_debug("DropboxFileBrowser Exception: %s" %(repr(e)) )
            try:
                self.getControl(self.PROGRESS_BAR).setPercent(percent)
            except Exception as e:
                log_debug("DropboxFileBrowser Exception: %s" %(repr(e)) )

    def onClick(self, controlId):
        self._visible = False
        self._closedTime = time.time()
        self.close()
        
    def onAction(self, action):
        self._visible = False
        self._closedTime = time.time()
        self.close()

