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
from resources.lib.dropboxclient import *

class DropboxFileBrowser(xbmcgui.WindowXMLDialog):
    """
    Dialog class that let's user select the a folder from Dropbox.
    """
    #FileBrowser IDs
    DIRECTORY_LIST = 450
    THUMB_LIST = 451
    HEADING_LABEL = 411
    PATH_LABEL = 412
    OK_BUTTON = 413
    CANCEL_BUTTON = 414
    CREATE_FOLDER = 415
    FLIP_IMAGE_HOR = 416
    #ACTION IDs
    ACTION_SELECT_ITEM = 7
    
    _heading = ''
    _currentPath = ''
    selectedFolder = None

    def __init__(self, *args, **kwargs):
        super(DropboxFileBrowser, self).__init__(*args, **kwargs)
        self._start_path = DROPBOX_SEP

    def setDBClient(self, client):
        self.client = client
        
    def setHeading(self, heading, path=None):
        self._heading = heading
        if path:
            self._start_path = path
        self._thumbView = False
        
    def onInit(self):
        #super(DropboxFileBrowser, self).onInit()
        #Some skins don't have the following items in the FileBrowser!
        try:
            self.getControl(self.FLIP_IMAGE_HOR).setEnabled(False)
        except Exception as e:
            log_debug("DropboxFileBrowser Exception: %s" %(repr(e)) )
        try:
            self.getControl(self.THUMB_LIST).setVisible(False) #bugy! check/change FileBrowser.xml file!?
            self._thumbView = True
        except Exception as e:
            log_debug("DropboxFileBrowser Exception: %s" %(repr(e)) )
        self.getControl(self.HEADING_LABEL).setLabel(self._heading)
        self.showFolders(self._start_path)

    def showFolders(self, path):
        log_debug('Selecting path: %s'%path)
        #Some skins don't have the following items in the FileBrowser!
        try:
            self.getControl(self.PATH_LABEL).setLabel(path)
        except Exception as e:
            log_debug("DropboxFileBrowser Exception: %s" %(repr(e)) )
        listView = self.getControl(self.DIRECTORY_LIST)
        if self._thumbView:
            thumbView = self.getControl(self.THUMB_LIST)
        listView.reset()
        if self._thumbView:
            thumbView.reset()
        self._currentPath = path
        items = self.client.getFolderContents(path)
        listItems = []
        if path != DROPBOX_SEP:
            backPath = os.path.dirname(path)
            listItem = xbmcgui.ListItem(label='..', label2=backPath, iconImage="DefaultFolderBack.png", thumbnailImage='DefaultFolderBack.png')
            listItems.append(listItem)
        for item in items:
            if item['is_dir'] == True:
                listItem = xbmcgui.ListItem(label=os.path.basename(path_from(item['path'])), label2=path_from(item['path']), iconImage="DefaultFolder.png", thumbnailImage='DefaultFolder.png')
                listItems.append(listItem)
        listView.addItems(listItems)
        if self._thumbView:
            thumbView.addItems(listItems) #bugy! check/change FileBrowser.xml file!?
        self.setFocusId(self.DIRECTORY_LIST)
        
    def onClick(self, controlId):
        if controlId == self.DIRECTORY_LIST:
            #update with new selected path
            newPath = path_from(self.getControl(controlId).getSelectedItem().getLabel2())
            self.showFolders(newPath)
        elif controlId == self.OK_BUTTON:
            self.selectedFolder = path_from(self._currentPath)
            self.close()
        elif controlId == self.CANCEL_BUTTON:
            self.close()
        elif controlId == self.CREATE_FOLDER:
            keyboard = xbmc.Keyboard('', LANGUAGE_STRING(30030))
            keyboard.doModal()
            if keyboard.isConfirmed():
                newFolder = self._currentPath
                if self._currentPath[-1:] != DROPBOX_SEP: newFolder += DROPBOX_SEP
                newFolder += keyboard.getText()
                success = self.client.createFolder(newFolder)
                if success:
                    log('New folder created: %s' % newFolder)
                    #update current list
                    self.showFolders(self._currentPath)
                else:
                    log_error('Creating new folder Failed: %s' % newFolder)

#     def onAction(self, action):
#         if (action.getId() == self.ACTION_SELECT_ITEM):
#             print "Action: %s"%action.getId()
#             controlId = self.getFocusId()
#             if controlId == self.DIRECTORY_LIST:
#                 #update with new selected path
#                 newPath = self.getControl(controlId).getSelectedItem().getLabel2()
#                 self.showFolders(newPath)
#             elif controlId == self.OK_BUTTON:
#                 self.selectedFolder = self._currentPath
#                 self.close()
#             elif controlId == self.CANCEL_BUTTON:
#                 self.close()
#             #self.onClick(controlId)
#         else:
#             super(DropboxFileBrowser, self).onAction(action)
